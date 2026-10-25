from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np
import joblib

from signbridge.classifier import (
    delete_language_model,
    load_model,
    predict_sequence,
    train_language_model,
    _build_pipeline,
    _choose_threshold,
    _evaluate_by_unseen_person,
    _add_rejection_metrics,
)
from signbridge.config import SEQUENCE_LENGTH, UNKNOWN_LABEL
from signbridge.dataset import DatasetStore
from signbridge.landmarks import FEATURE_DIM
from signbridge.vocabulary import LanguagePack, SignDefinition


class ClassifierTests(unittest.TestCase):
    def test_old_calibration_model_requests_retraining_without_deleting_it(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "old.joblib"
            joblib.dump({"version": 1}, path)
            with self.assertRaisesRegex(ValueError, "Retrain"):
                load_model("asl", path)
            self.assertTrue(path.exists())

    def test_train_save_load_and_predict(self) -> None:
        signs = tuple(
            SignDefinition(f"sign_{index}", f"SIGN-{index}", f"Sign {index}")
            for index in range(8)
        )
        pack = LanguagePack(
            id="test",
            name="Test language",
            short_name="Test",
            output_language="Test",
            locale="en-US",
            direction="ltr",
            reference_name="Test source",
            reference_url="https://example.invalid",
            signs=signs,
        )
        labels = [sign.id for sign in signs] + [UNKNOWN_LABEL]

        with TemporaryDirectory() as temp:
            root = Path(temp)
            store = DatasetStore(root / "samples", root / "trash")
            rng = np.random.default_rng(42)
            examples: dict[str, np.ndarray] = {}
            for person_index in range(3):
                for label_index, label in enumerate(labels):
                    for sample_index in range(2):
                        sequence = np.zeros(
                            (SEQUENCE_LENGTH, FEATURE_DIM), dtype=np.float32
                        )
                        start = label_index * 5
                        sequence[:, start : start + 5] = np.linspace(
                            0.5, 2.0, SEQUENCE_LENGTH, dtype=np.float32
                        )[:, None]
                        sequence += rng.normal(0, 0.002, sequence.shape).astype(np.float32)
                        sequence[:, 100 + person_index] += person_index * 0.002
                        store.save_sample("test", label, f"person-{person_index}", sequence)
                        examples[label] = sequence

            model_path = root / "test.joblib"
            bundle = train_language_model(
                "test", pack, store, destination=model_path, minimum_per_class=2
            )
            loaded = load_model("test", model_path)
            incompatible = load_model(
                "test", model_path, expected_labels=["different", UNKNOWN_LABEL]
            )
            prediction = predict_sequence(loaded, examples["sign_0"])

            self.assertTrue(model_path.exists())
            self.assertTrue(model_path.with_suffix(".json").exists())
            self.assertIsNone(incompatible)
            self.assertEqual(set(bundle["classes"]), set(labels))
            self.assertTrue(bundle["metrics"]["development_evaluated"])
            self.assertFalse(bundle["metrics"]["validated_on_unseen_people"])
            self.assertFalse(bundle["metrics"]["independent_final_test"])
            self.assertIsNotNone(bundle["metrics"]["unknown_rejection"])
            self.assertIsNotNone(bundle["metrics"]["supported_sign_coverage"])
            self.assertEqual(prediction.label, "sign_0")
            self.assertGreater(prediction.confidence, 1.0 / len(labels))

            privacy_models = root / "privacy-models"
            (privacy_models / "asl.joblib").parent.mkdir(parents=True)
            (privacy_models / "asl.joblib").write_bytes(b"model")
            (privacy_models / "asl.json").write_text("{}", encoding="utf-8")
            self.assertEqual(delete_language_model("asl", privacy_models), 2)
            self.assertFalse((privacy_models / "asl.joblib").exists())

    def test_scaling_is_fitted_only_on_each_calibration_training_split(self) -> None:
        from sklearn.preprocessing import StandardScaler

        original_fit = StandardScaler.fit
        fitted_sizes = []

        def track_fit(estimator, x, *args, **kwargs):
            fitted_sizes.append(len(x))
            return original_fit(estimator, x, *args, **kwargs)

        x = np.random.default_rng(1).normal(size=(12, 6))
        y = np.repeat(["hello", "help", UNKNOWN_LABEL], 4)
        with patch.object(StandardScaler, "fit", track_fit):
            _build_pipeline(12, 6).fit(x, y)

        self.assertEqual(sorted(fitted_sizes), [6, 6, 12])

    def test_failed_threshold_search_never_falls_back_to_unsafe_default(self) -> None:
        probabilities = np.asarray([[0.99, 0.01], [0.99, 0.01]])
        threshold = _choose_threshold(
            probabilities, ["help", UNKNOWN_LABEL], ["help", UNKNOWN_LABEL]
        )
        self.assertEqual(threshold, 1.0)
        metrics = {}
        _add_rejection_metrics(
            metrics, np.asarray([[1.0, 0.0], [1.0, 0.0]]),
            ["help", UNKNOWN_LABEL], ["help", UNKNOWN_LABEL], threshold,
        )
        self.assertEqual(metrics["supported_sign_coverage"], 0.0)
        self.assertEqual(metrics["unknown_rejection"], 1.0)
        self.assertIsNone(metrics["accepted_precision"])

    def test_incomplete_person_folds_are_skipped_instead_of_crashing(self) -> None:
        x = np.zeros((3, 4))
        y = np.asarray(["help", "hello", UNKNOWN_LABEL])
        groups = np.asarray(["a", "b", "c"])
        metrics, probabilities, actual = _evaluate_by_unseen_person(
            x, y, groups, ["help", "hello", UNKNOWN_LABEL]
        )
        self.assertFalse(metrics["development_evaluated"])
        self.assertIsNone(probabilities)
        self.assertIsNone(actual)

    def test_inference_rejects_low_visibility_even_with_high_model_score(self) -> None:
        pipeline = SimpleNamespace(
            predict_proba=lambda _x: np.asarray([[0.99, 0.01]]),
            named_steps={"classifier": SimpleNamespace(classes_=["help", UNKNOWN_LABEL])},
        )
        bundle = {"pipeline": pipeline}
        sequence = np.zeros((SEQUENCE_LENGTH, FEATURE_DIM), dtype=np.float32)

        self.assertTrue(predict_sequence(bundle, sequence, hand_presence_ratio=1.0).accepted)
        self.assertFalse(predict_sequence(bundle, sequence, hand_presence_ratio=0.0).accepted)
        self.assertFalse(predict_sequence(bundle, sequence, hand_presence_ratio=float("nan")).accepted)
        bundle["recognition_enabled"] = False
        self.assertFalse(predict_sequence(bundle, sequence, hand_presence_ratio=1.0).accepted)

    def test_nonfinite_landmarks_cannot_reach_the_model(self) -> None:
        sequence = np.full((SEQUENCE_LENGTH, FEATURE_DIM), np.nan, dtype=np.float32)
        with self.assertRaisesRegex(ValueError, "finite"):
            predict_sequence({}, sequence)


if __name__ == "__main__":
    unittest.main()
