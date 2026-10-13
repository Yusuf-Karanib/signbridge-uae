from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

from signbridge.config import SEQUENCE_LENGTH
from signbridge.landmarks import FEATURE_DIM
from signbridge.video_import import extract_training_video, validate_video_path


class VideoImportTests(unittest.TestCase):
    def test_accepts_a_supported_existing_video_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "one-sign.MP4"
            path.write_bytes(b"small test placeholder")

            self.assertEqual(validate_video_path(path), path)

    def test_rejects_missing_or_unsupported_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "cannot be found"):
                validate_video_path(root / "missing.mp4")

            text_file = root / "not-a-video.txt"
            text_file.write_text("not video", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Choose an MP4"):
                validate_video_path(text_file)

    def test_extracts_landmarks_without_storing_the_raw_video(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "one-sign.avi"
            writer = cv2.VideoWriter(
                str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (64, 64)
            )
            self.assertTrue(writer.isOpened())
            for value in range(8):
                writer.write(np.full((64, 64, 3), value * 10, dtype=np.uint8))
            writer.release()

            hand = [
                SimpleNamespace(x=0.20 + index * 0.01, y=0.30, z=0.0)
                for index in range(21)
            ]

            def result_provider(_frame: np.ndarray, _timestamp: int) -> object:
                return SimpleNamespace(
                    pose_landmarks=[],
                    left_hand_landmarks=hand,
                    right_hand_landmarks=[],
                )

            imported = extract_training_video(
                path, result_provider=result_provider
            )

            self.assertEqual(
                imported.sequence.shape, (SEQUENCE_LENGTH, FEATURE_DIM)
            )
            self.assertEqual(imported.quality["source"], "imported_video")
            self.assertEqual(imported.quality["hand_presence_ratio"], 1.0)
            self.assertFalse(imported.quality["raw_video_stored"])


if __name__ == "__main__":
    unittest.main()
