from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signbridge.classifier import load_model, predict_sequence, train_language_model
from signbridge.config import SEQUENCE_LENGTH, UNKNOWN_LABEL
from signbridge.dataset import DatasetStore
from signbridge.landmarks import FEATURE_DIM
from signbridge.vocabulary import LanguagePack, SignDefinition


class ClassifierTests(unittest.TestCase):
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
            self.assertTrue(bundle["metrics"]["validated_on_unseen_people"])
            self.assertIsNotNone(bundle["metrics"]["unknown_rejection"])
            self.assertIsNotNone(bundle["metrics"]["supported_sign_coverage"])
            self.assertEqual(prediction.label, "sign_0")
            self.assertGreater(prediction.confidence, 1.0 / len(labels))


if __name__ == "__main__":
    unittest.main()
