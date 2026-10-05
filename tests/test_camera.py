import unittest
from unittest.mock import patch

import cv2
import numpy as np

from signbridge.camera import (
    CameraWorker,
    camera_resolution_warning,
    configure_camera,
    prepare_preview_frame,
    resize_for_tracking,
    smooth_hand_tracks,
)


class CameraWorkerTests(unittest.TestCase):
    def test_camera_defaults_do_not_force_an_unsupported_video_format(self) -> None:
        class FakeCamera:
            def __init__(self) -> None:
                self.properties: list[tuple[int, float]] = []

            def set(self, property_id: int, value: float) -> bool:
                self.properties.append((property_id, value))
                return True

        camera = FakeCamera()

        configure_camera(camera)

        property_ids = {property_id for property_id, _value in camera.properties}
        self.assertNotIn(cv2.CAP_PROP_FOURCC, property_ids)

    def test_preview_can_stay_large_while_tracking_copy_is_small(self) -> None:
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        resized = resize_for_tracking(frame)

        self.assertEqual(resized.shape, (360, 640, 3))
        self.assertEqual(frame.shape, (720, 1280, 3))

    def test_low_resolution_preview_is_upscaled_before_overlay(self) -> None:
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        hand = np.full((21, 3), 0.5, dtype=np.float32)

        preview = prepare_preview_frame(frame, (hand,))

        self.assertEqual(preview.shape, (480, 640, 3))
        self.assertGreater(int(preview.sum()), 0)

    def test_low_camera_resolution_has_an_honest_warning(self) -> None:
        self.assertIn("160×120", camera_resolution_warning(160, 120) or "")
        self.assertIsNone(camera_resolution_warning(1280, 720))

    def test_small_hand_jitter_is_smoothed_more_than_large_motion(self) -> None:
        previous = np.full((21, 3), 0.5, dtype=np.float32)
        small_change = previous.copy()
        small_change[:, 0] += 0.01
        large_change = previous.copy()
        large_change[:, 0] += 0.10

        small_result = smooth_hand_tracks((small_change,), (previous,))[0]
        large_result = smooth_hand_tracks((large_change,), (previous,))[0]

        self.assertLess(float(small_result[0, 0]), 0.505)
        self.assertGreater(float(large_result[0, 0]), 0.56)

    def test_start_camera_resets_a_stopped_worker_and_changes_index(self) -> None:
        worker = CameraWorker(camera_index=0)
        worker._stop_event.set()

        with (
            patch.object(worker, "isRunning", return_value=False),
            patch.object(worker, "start") as start,
        ):
            started = worker.start_camera(2)

        self.assertTrue(started)
        self.assertEqual(worker.camera_index, 2)
        self.assertFalse(worker._stop_event.is_set())
        start.assert_called_once_with()

    def test_start_camera_does_not_start_twice(self) -> None:
        worker = CameraWorker(camera_index=0)

        with (
            patch.object(worker, "isRunning", return_value=True),
            patch.object(worker, "start") as start,
        ):
            started = worker.start_camera(1)

        self.assertFalse(started)
        self.assertEqual(worker.camera_index, 0)
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
