from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from signbridge.popsign_import import discover_popsign_training_clips


class PopSignImportTests(unittest.TestCase):
    @staticmethod
    def _clip(folder: Path, name: str) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_bytes(b"video placeholder")
        return path

    def test_discovers_one_train_sign_and_prefers_different_people(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "popsign_v2_1" / "game" / "train" / "hello"
            for person in ("p01", "p02", "p03"):
                self._clip(folder, f"{person}--100-.mp4")
                self._clip(folder, f"{person}--200-.mp4")

            clips = discover_popsign_training_clips(folder, limit=4)

            self.assertEqual(len(clips), 4)
            self.assertEqual({clip.label for clip in clips}, {"hello"})
            self.assertEqual(len({clip.person_id for clip in clips[:3]}), 3)
            self.assertTrue(all(clip.person_id.startswith("popsign-") for clip in clips))

    def test_never_accepts_validation_or_test_split_for_training(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "popsign_v2_1" / "game"
            for split in ("val", "test"):
                folder = root / split / "help"
                self._clip(folder, "p01--100-.mp4")
                with self.assertRaisesRegex(ValueError, "Keep it out of training"):
                    discover_popsign_training_clips(folder)

    def test_requires_one_supported_sign_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            train = Path(temp_dir) / "popsign_v2_1" / "game" / "train"
            self._clip(train / "hello", "p01--100-.mp4")
            self._clip(train / "help", "p02--100-.mp4")

            with self.assertRaisesRegex(ValueError, "one sign folder"):
                discover_popsign_training_clips(train)

    def test_rejects_variant_category(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = (
                Path(temp_dir)
                / "popsign_v2_1"
                / "non-game"
                / "train"
                / "help"
            )
            self._clip(folder, "p01--100-.mp4")

            with self.assertRaisesRegex(ValueError, "game/train"):
                discover_popsign_training_clips(folder)

    def test_skips_duplicates_final_test_people_and_bad_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "popsign_v2_1" / "game" / "train" / "water"
            duplicate = self._clip(folder, "p01--100-.mp4")
            self._clip(folder, "p02--100-.mp4")
            self._clip(folder, "p03--100-.mp4")
            self._clip(folder, "no-participant-separator.mp4")

            clips = discover_popsign_training_clips(
                folder,
                excluded_clip_ids={f"popsign_v2_1/water/{duplicate.name}"},
                excluded_people={"popsign-p02"},
            )

            self.assertEqual(len(clips), 1)
            self.assertEqual(clips[0].person_id, "popsign-p03")

    def test_again_is_not_silently_treated_as_another_sign(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "popsign_v2_1" / "game" / "train" / "again"
            self._clip(folder, "p01--100-.mp4")

            with self.assertRaisesRegex(ValueError, "hello, help and water"):
                discover_popsign_training_clips(folder)


if __name__ == "__main__":
    unittest.main()
