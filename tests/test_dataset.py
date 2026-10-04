from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from signbridge.config import SEQUENCE_LENGTH
from signbridge.dataset import DatasetStore
from signbridge.landmarks import FEATURE_DIM


class DatasetTests(unittest.TestCase):
    def test_sample_round_trip_and_recoverable_removal(self) -> None:
        with TemporaryDirectory() as temp:
            root = Path(temp)
            store = DatasetStore(root / "samples", root / "trash")
            sequence = np.zeros((SEQUENCE_LENGTH, FEATURE_DIM), dtype=np.float32)

            saved = store.save_sample("asl", "hello", "person 01", sequence)
            records = store.load_records("asl")

            self.assertTrue(saved.exists())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].person_id, "person-01")
            np.testing.assert_array_equal(records[0].sequence, sequence)

            trashed = store.move_last_to_trash("asl", "hello")
            self.assertIsNotNone(trashed)
            self.assertTrue(trashed.exists())
            self.assertFalse(saved.exists())


if __name__ == "__main__":
    unittest.main()

