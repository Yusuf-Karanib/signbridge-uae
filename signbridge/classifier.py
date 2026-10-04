from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import PCA
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from signbridge.config import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MARGIN_THRESHOLD,
    MIN_SAMPLES_PER_CLASS,
    TRAINED_MODELS_DIR,
    UNKNOWN_LABEL,
)
from signbridge.dataset import DatasetStore, SampleRecord
from signbridge.landmarks import FEATURE_VERSION, sequence_to_model_vector
from signbridge.vocabulary import LanguagePack


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    margin: float
    accepted: bool
    alternatives: tuple[tuple[str, float], ...]


def _build_pipeline(sample_count: int, feature_count: int) -> Pipeline:
    components = max(2, min(48, sample_count - 2, feature_count))
    return Pipeline(
        steps=[
            ("scale", StandardScaler()),
            # Keep stronger movement patterns stronger; whitening can amplify camera jitter.
            ("pca", PCA(n_components=components, whiten=False, random_state=42)),
            (
                "classifier",
                CalibratedClassifierCV(
                    estimator=SVC(
                        kernel="rbf",
                        C=6.0,
                        gamma="scale",
                        class_weight="balanced",
                        random_state=42,
                    ),
                    method="sigmoid",
                    cv=2,
                    ensemble=False,
                ),
            ),
        ]
    )


def _records_to_arrays(records: list[SampleRecord]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.stack([sequence_to_model_vector(record.sequence) for record in records])
    y = np.asarray([record.label for record in records])
    groups = np.asarray([record.person_id for record in records])
    return x, y, groups


def _evaluate_by_unseen_person(
    x: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    required_labels: list[str],
) -> tuple[dict, np.ndarray | None, list[str] | None]:
    unique_people = sorted(set(groups.tolist()))
    if len(unique_people) < 3:
        return (
            {
                "validated_on_unseen_people": False,
                "reason": "At least 3 different people are required for an unseen-person test.",
                "people": len(unique_people),
            },
            None,
            None,
        )

    probabilities: list[np.ndarray] = []
    actual: list[str] = []
    class_order: list[str] | None = None
    tested_people: list[str] = []
    for held_out in unique_people:
        train_mask = groups != held_out
        test_mask = groups == held_out
        train_classes = set(y[train_mask].tolist())
        if not set(required_labels).issubset(train_classes):
            continue
        fold = _build_pipeline(int(train_mask.sum()), x.shape[1])
        fold.fit(x[train_mask], y[train_mask])
        fold_classes = list(fold.named_steps["classifier"].classes_)
        if class_order is None:
            class_order = fold_classes
        if fold_classes != class_order:
            continue
        probabilities.extend(fold.predict_proba(x[test_mask]))
        actual.extend(y[test_mask].tolist())
        tested_people.append(held_out)

    if not probabilities or class_order is None or len(tested_people) < 2:
        return (
            {
                "validated_on_unseen_people": False,
                "reason": "Each training fold needs examples of every sign from other people.",
                "people": len(unique_people),
            },
            None,
            None,
        )

    prob = np.asarray(probabilities, dtype=np.float32)
    actual_array = np.asarray(actual)
    predicted = np.asarray([class_order[index] for index in np.argmax(prob, axis=1)])
    labels_for_metrics = [label for label in required_labels if label != UNKNOWN_LABEL]
    non_unknown = actual_array != UNKNOWN_LABEL
    if non_unknown.any():
        balanced = balanced_accuracy_score(actual_array[non_unknown], predicted[non_unknown])
        per_sign = {
            label: float(recall_score(actual_array == label, predicted == label, zero_division=0))
            for label in labels_for_metrics
        }
    else:
        balanced = 0.0
        per_sign = {label: 0.0 for label in labels_for_metrics}

    unknown_mask = actual_array == UNKNOWN_LABEL
    raw_unknown_top1 = (
        float(np.mean(predicted[unknown_mask] == UNKNOWN_LABEL)) if unknown_mask.any() else None
    )
    matrix = confusion_matrix(actual_array, predicted, labels=required_labels)
    metrics = {
        "validated_on_unseen_people": True,
        "people": len(unique_people),
        "tested_people": len(tested_people),
        "balanced_accuracy": float(balanced),
        "per_sign_recall": per_sign,
        "raw_unknown_top1": raw_unknown_top1,
        "confusion_labels": required_labels,
        "confusion_matrix": matrix.tolist(),
    }
    return metrics, prob, actual


def _choose_threshold(
    probabilities: np.ndarray | None,
    actual: list[str] | None,
    classes: list[str],
) -> float:
    if probabilities is None or actual is None:
        return DEFAULT_CONFIDENCE_THRESHOLD
    actual_array = np.asarray(actual)
    order = np.argsort(probabilities, axis=1)[:, ::-1]
    top_labels = np.asarray([classes[index] for index in order[:, 0]])
    top_scores = probabilities[np.arange(len(probabilities)), order[:, 0]]
    margins = top_scores - probabilities[np.arange(len(probabilities)), order[:, 1]]

    for threshold in np.arange(0.55, 0.96, 0.01):
        accepted = (
            (top_labels != UNKNOWN_LABEL)
            & (top_scores >= threshold)
            & (margins >= DEFAULT_MARGIN_THRESHOLD)
        )
        valid_attempts = actual_array != UNKNOWN_LABEL
        coverage = accepted[valid_attempts].mean() if valid_attempts.any() else 0.0
        if accepted.any():
            precision = precision_score(
                actual_array[accepted], top_labels[accepted], average="micro", zero_division=0
            )
            if precision >= 0.95 and coverage >= 0.60:
                return float(round(threshold, 2))
    return DEFAULT_CONFIDENCE_THRESHOLD


def _add_rejection_metrics(
    metrics: dict,
    probabilities: np.ndarray | None,
    actual: list[str] | None,
    classes: list[str],
    threshold: float,
) -> None:
    if probabilities is None or actual is None:
        metrics.update(
            {
                "accepted_precision": None,
                "supported_sign_coverage": None,
                "unknown_rejection": None,
            }
        )
        return

    actual_array = np.asarray(actual)
    order = np.argsort(probabilities, axis=1)[:, ::-1]
    top_labels = np.asarray([classes[index] for index in order[:, 0]])
    top_scores = probabilities[np.arange(len(probabilities)), order[:, 0]]
    margins = top_scores - probabilities[np.arange(len(probabilities)), order[:, 1]]
    accepted = (
        (top_labels != UNKNOWN_LABEL)
        & (top_scores >= threshold)
        & (margins >= DEFAULT_MARGIN_THRESHOLD)
    )
    supported = actual_array != UNKNOWN_LABEL
    unknown = actual_array == UNKNOWN_LABEL
    metrics.update(
        {
            "accepted_precision": (
                float(np.mean(top_labels[accepted] == actual_array[accepted]))
                if accepted.any()
                else None
            ),
            "supported_sign_coverage": (
                float(np.mean(accepted[supported])) if supported.any() else None
            ),
            "unknown_rejection": (
                float(np.mean(~accepted[unknown])) if unknown.any() else None
            ),
        }
    )


def train_language_model(
    language: str,
    pack: LanguagePack,
    store: DatasetStore,
    destination: Path | None = None,
    minimum_per_class: int = MIN_SAMPLES_PER_CLASS,
) -> dict:
    required_labels = list(pack.sign_ids) + [UNKNOWN_LABEL]
    records = [
        record for record in store.load_records(language) if record.label in required_labels
    ]
    counts = {label: 0 for label in required_labels}
    for record in records:
        counts[record.label] += 1
    missing = {
        label: count
        for label, count in counts.items()
        if count < minimum_per_class
    }
    if missing:
        details = ", ".join(
            f"{label}: {count}/{minimum_per_class}" for label, count in missing.items()
        )
        raise ValueError(f"More training samples are needed: {details}")

    x, y, groups = _records_to_arrays(records)
    metrics, validation_probabilities, validation_actual = _evaluate_by_unseen_person(
        x, y, groups, required_labels
    )
    pipeline = _build_pipeline(len(x), x.shape[1])
    pipeline.fit(x, y)
    classes = list(pipeline.named_steps["classifier"].classes_)
    threshold = _choose_threshold(validation_probabilities, validation_actual, classes)
    _add_rejection_metrics(
        metrics,
        validation_probabilities,
        validation_actual,
        classes,
        threshold,
    )
    created_at = datetime.now(timezone.utc).isoformat()
    bundle = {
        "version": 1,
        "language": language,
        "created_at": created_at,
        "feature_version": FEATURE_VERSION,
        "labels": required_labels,
        "classes": classes,
        "counts": counts,
        "people": sorted(set(groups.tolist())),
        "confidence_threshold": threshold,
        "margin_threshold": DEFAULT_MARGIN_THRESHOLD,
        "metrics": metrics,
        "pipeline": pipeline,
    }
    destination = destination or (TRAINED_MODELS_DIR / f"{language}.joblib")
    destination.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, destination)
    metrics_path = destination.with_suffix(".json")
    metrics_payload = {key: value for key, value in bundle.items() if key != "pipeline"}
    metrics_path.write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return bundle


def load_model(
    language: str,
    path: Path | None = None,
    expected_labels: list[str] | None = None,
) -> dict | None:
    path = path or (TRAINED_MODELS_DIR / f"{language}.joblib")
    if not path.exists():
        return None
    bundle = joblib.load(path)
    if bundle.get("feature_version") != FEATURE_VERSION:
        raise ValueError("The trained model uses an older landmark format. Retrain it.")
    if expected_labels is not None and bundle.get("labels") != expected_labels:
        return None
    return bundle


def predict_sequence(bundle: dict, sequence: np.ndarray) -> Prediction:
    vector = sequence_to_model_vector(sequence).reshape(1, -1)
    probabilities = bundle["pipeline"].predict_proba(vector)[0]
    classes = list(bundle["pipeline"].named_steps["classifier"].classes_)
    ranked = np.argsort(probabilities)[::-1]
    alternatives = tuple((classes[index], float(probabilities[index])) for index in ranked)
    top_label, top_score = alternatives[0]
    second_score = alternatives[1][1] if len(alternatives) > 1 else 0.0
    margin = top_score - second_score
    accepted = (
        top_label != UNKNOWN_LABEL
        and top_score >= float(bundle.get("confidence_threshold", DEFAULT_CONFIDENCE_THRESHOLD))
        and margin >= float(bundle.get("margin_threshold", DEFAULT_MARGIN_THRESHOLD))
    )
    return Prediction(
        label=top_label,
        confidence=top_score,
        margin=margin,
        accepted=accepted,
        alternatives=alternatives,
    )
