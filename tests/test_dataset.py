from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signbridge.config import SEQUENCE_LENGTH
from signbridge.dataset import DatasetStore
from signbridge.landmarks import FEATURE_DIM


class DatasetTests(unittest.TestCase):
    def test_invalid_sequences_are_not_saved(self) -> None:
        with TemporaryDirectory() as temp:
            store = DatasetStore(Path(temp) / "samples", Path(temp) / "trash")
            for sequence in (
                np.zeros((2, FEATURE_DIM)),
                np.full((SEQUENCE_LENGTH, FEATURE_DIM), np.inf),
            ):
                with self.assertRaisesRegex(ValueError, "invalid"):
                    store.save_sample("asl", "help", "trainer", sequence)
            self.assertEqual(store.load_records(), [])

    def test_sample_round_trip_and_recoverable_removal(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            store = DatasetStore(root / "samples", root / "trash")
            sequence = np.zeros((SEQUENCE_LENGTH, FEATURE_DIM), dtype=np.float32)

            saved = store.save_sample(
                "asl",
                "hello",
                "person 01",
                sequence,
                consent_confirmed=True,
                capture_source="live_camera",
            )
            records = store.load_records("asl")

            self.assertTrue(saved.exists())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].person_id, "person-01")
            self.assertTrue(records[0].metadata["consent_confirmed"])
            self.assertEqual(records[0].metadata["capture_source"], "live_camera")
            np.testing.assert_array_equal(records[0].sequence, sequence)

            trashed = store.move_last_to_trash("asl", "hello")
            self.assertIsNotNone(trashed)
            self.assertTrue(trashed.exists())
            self.assertFalse(saved.exists())

            active = store.save_sample(
                "asl", "help", "person 01", sequence
            )
            other = store.save_sample(
                "asl", "help", "person-02", sequence
            )
            self.assertEqual(store.delete_person("person 01"), 2)
            self.assertFalse(trashed.exists())
            self.assertFalse(active.exists())
            self.assertTrue(other.exists())
            self.assertEqual(store.last_delete_skipped, 0)

            corrupt = store.samples_dir / "asl" / "help" / "corrupt.npz"
            corrupt.write_bytes(b"not-an-npz")
            self.assertEqual(store.delete_person("person-02"), 1)
            self.assertEqual(store.last_delete_skipped, 1)
            self.assertTrue(corrupt.exists())


if __name__ == "__main__":
    unittest.main()

