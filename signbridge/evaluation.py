from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from signbridge.config import EVALUATIONS_DIR, UNKNOWN_LABEL
from signbridge.dataset import DatasetStore


@dataclass(frozen=True)
class EvaluationAttempt:
    language: str
    expected_label: str
    person_id: str
    predicted_label: str
    accepted: bool
    confidence: float
    margin: float
    model_created_at: str
    condition: str
    processing_ms: float
    captured_at: str


class EvaluationStore:
    """Stores final-test results separately from all training samples."""

    def __init__(self, directory: Path = EVALUATIONS_DIR):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save_attempt(
        self,
        *,
        language: str,
        expected_label: str,
        person_id: str,
        predicted_label: str,
        accepted: bool,
        confidence: float,
        margin: float,
        model_created_at: str,
        condition: str,
        processing_ms: float,
    ) -> Path:
        language = DatasetStore.safe_component(language)
        expected_label = DatasetStore.safe_component(expected_label)
        person_id = DatasetStore.safe_component(person_id)
        captured_at = datetime.now(timezone.utc)
        payload = {
            "version": 1,
            "language": language,
            "expected_label": expected_label,
            "person_id": person_id,
            "predicted_label": str(predicted_label),
            "accepted": bool(accepted),
            "confidence": float(confidence),
            "margin": float(margin),
            "model_created_at": str(model_created_at),
            "condition": str(condition).strip() or "Normal indoor",
            "processing_ms": float(processing_ms),
            "captured_at": captured_at.isoformat(),
        }
        destination = self.directory / language
        destination.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{captured_at.strftime('%Y%m%dT%H%M%S%fZ')}_"
            f"{uuid.uuid4().hex[:8]}.json"
        )
        path = destination / filename
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(path)
        return path

    def load_attempts(
        self, language: str, model_created_at: str | None = None
    ) -> list[EvaluationAttempt]:
        root = self.directory / language
        if not root.exists():
            return []
        attempts: list[EvaluationAttempt] = []
        for path in sorted(root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if model_created_at and payload.get("model_created_at") != model_created_at:
                    continue
                attempts.append(
                    EvaluationAttempt(
                        language=str(payload["language"]),
                        expected_label=str(payload["expected_label"]),
                        person_id=str(payload["person_id"]),
                        predicted_label=str(payload["predicted_label"]),
                        accepted=bool(payload["accepted"]),
                        confidence=float(payload["confidence"]),
                        margin=float(payload["margin"]),
                        model_created_at=str(payload["model_created_at"]),
                        condition=str(payload.get("condition", "Normal indoor")),
                        processing_ms=float(payload.get("processing_ms", 0.0)),
                        captured_at=str(payload["captured_at"]),
                    )
                )
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return attempts

    def people(self, language: str) -> set[str]:
        return {attempt.person_id for attempt in self.load_attempts(language)}

    def summary(
        self, language: str, labels: tuple[str, ...], model_created_at: str
    ) -> dict:
        attempts = self.load_attempts(language, model_created_at)
        supported = [attempt for attempt in attempts if attempt.expected_label != UNKNOWN_LABEL]
        unknown = [attempt for attempt in attempts if attempt.expected_label == UNKNOWN_LABEL]
        accepted = [attempt for attempt in attempts if attempt.accepted]

        label_attempts: dict[str, int] = {}
        per_sign_recall: dict[str, float | None] = {}
        for label in labels:
            matching = [attempt for attempt in supported if attempt.expected_label == label]
            label_attempts[label] = len(matching)
            if matching:
                correct = sum(
                    attempt.accepted and attempt.predicted_label == label
                    for attempt in matching
                )
                per_sign_recall[label] = correct / len(matching)
            else:
                per_sign_recall[label] = None

        measured_recalls = [
            score for score in per_sign_recall.values() if score is not None
        ]
        balanced_accuracy = (
            float(np.mean(measured_recalls))
            if len(measured_recalls) == len(labels) and measured_recalls
            else None
        )
        accepted_correct = sum(
            attempt.expected_label != UNKNOWN_LABEL
            and attempt.predicted_label == attempt.expected_label
            for attempt in accepted
        )
        overall_correct = sum(
            (
                attempt.expected_label == UNKNOWN_LABEL and not attempt.accepted
            )
            or (
                attempt.expected_label != UNKNOWN_LABEL
                and attempt.accepted
                and attempt.predicted_label == attempt.expected_label
            )
            for attempt in attempts
        )
        by_condition = {}
        for condition in sorted({attempt.condition for attempt in attempts}):
            matching = [
                attempt for attempt in attempts if attempt.condition == condition
            ]
            supported_matching = [
                attempt
                for attempt in matching
                if attempt.expected_label != UNKNOWN_LABEL
            ]
            unknown_matching = [
                attempt
                for attempt in matching
                if attempt.expected_label == UNKNOWN_LABEL
            ]
            correct = sum(
                (
                    attempt.expected_label == UNKNOWN_LABEL
                    and not attempt.accepted
                )
                or (
                    attempt.expected_label != UNKNOWN_LABEL
                    and attempt.accepted
                    and attempt.predicted_label == attempt.expected_label
                )
                for attempt in matching
            )
            supported_correct = sum(
                attempt.accepted
                and attempt.predicted_label == attempt.expected_label
                for attempt in supported_matching
            )
            by_condition[condition] = {
                "attempts": len(matching),
                "accuracy": correct / len(matching),
                "supported_accuracy": (
                    supported_correct / len(supported_matching)
                    if supported_matching
                    else None
                ),
                "unknown_rejection": (
                    sum(not attempt.accepted for attempt in unknown_matching)
                    / len(unknown_matching)
                    if unknown_matching
                    else None
                ),
            }
        return {
            "model_created_at": model_created_at,
            "attempts": len(attempts),
            "people": len({attempt.person_id for attempt in attempts}),
            "correct_attempts": overall_correct,
            "balanced_accuracy": balanced_accuracy,
            "per_sign_recall": per_sign_recall,
            "label_attempts": label_attempts,
            "accepted_precision": (
                accepted_correct / len(accepted) if accepted else None
            ),
            "supported_sign_coverage": (
                sum(attempt.accepted for attempt in supported) / len(supported)
                if supported
                else None
            ),
            "unknown_attempts": len(unknown),
            "unknown_rejection": (
                sum(not attempt.accepted for attempt in unknown) / len(unknown)
                if unknown
                else None
            ),
            "average_processing_ms": (
                float(np.mean([attempt.processing_ms for attempt in attempts]))
                if attempts
                else None
            ),
            "by_condition": by_condition,
        }

    def write_report(
        self, language: str, labels: tuple[str, ...], model_created_at: str
    ) -> Path:
        report = self.summary(language, labels, model_created_at)
        path = self.directory / f"report_{DatasetStore.safe_component(language)}.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(path)
        return path
