from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from signbridge.config import UNKNOWN_LABEL
from signbridge.evaluation import EvaluationStore


class EvaluationTests(unittest.TestCase):
    def test_final_test_summary_is_separate_by_model(self) -> None:
        with TemporaryDirectory() as temp:
            store = EvaluationStore(Path(temp))
            common = {
                "language": "asl",
                "person_id": "tester 01",
                "confidence": 0.91,
                "margin": 0.30,
                "condition": "Normal indoor",
                "processing_ms": 14.0,
            }
            store.save_attempt(
                **common,
                expected_label="hello",
                predicted_label="hello",
                accepted=True,
                model_created_at="model-a",
            )
            store.save_attempt(
                **common,
                expected_label="help",
                predicted_label="hello",
                accepted=True,
                model_created_at="model-a",
            )
            store.save_attempt(
                **common,
                expected_label=UNKNOWN_LABEL,
                predicted_label="hello",
                accepted=False,
                model_created_at="model-a",
            )
            store.save_attempt(
                **common,
                expected_label="hello",
                predicted_label="help",
                accepted=True,
                model_created_at="older-model",
            )

            summary = store.summary("asl", ("hello", "help"), "model-a")

            self.assertEqual(summary["attempts"], 3)
            self.assertEqual(summary["people"], 1)
            self.assertEqual(summary["balanced_accuracy"], 0.5)
            self.assertEqual(summary["accepted_precision"], 0.5)
            self.assertEqual(summary["unknown_rejection"], 1.0)
            self.assertEqual(summary["by_condition"]["Normal indoor"]["attempts"], 3)
            self.assertAlmostEqual(
                summary["by_condition"]["Normal indoor"]["accuracy"], 2 / 3
            )
            self.assertEqual(summary["average_processing_ms"], 14.0)
            self.assertEqual(store.people("asl"), {"tester-01"})
            self.assertTrue(store.write_report("asl", ("hello", "help"), "model-a").exists())


if __name__ == "__main__":
    unittest.main()
