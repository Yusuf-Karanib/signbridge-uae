import unittest
from unittest.mock import patch

from signbridge.camera import CameraWorker


class CameraWorkerTests(unittest.TestCase):
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
