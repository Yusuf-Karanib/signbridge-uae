from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from signbridge.ui import MainWindow


class FakeController:
    is_supported = True

    def __init__(self) -> None:
        self.volume_ups = 0

    def volume_up(self) -> bool:
        self.volume_ups += 1
        return True

    def volume_down(self) -> bool:
        return True

    def next_slide(self) -> bool:
        return True

    def previous_slide(self) -> bool:
        return True

    def move_pointer(self, _x: float, _y: float) -> bool:
        return True

    def click(self) -> bool:
        return True


class ControlUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_open_palm_arms_then_stable_gesture_controls_and_tab_exit_stops(self) -> None:
        window = MainWindow()
        controller = FakeController()
        window.computer_controller = controller
        window.camera_ok = True
        window.tabs.setCurrentIndex(3)
        window._toggle_computer_control()

        for index in range(11):
            window._on_control_gesture(
                {
                    "name": "Open_Palm",
                    "score": 0.95,
                    "hands": (),
                    "timestamp": 10.0 + index * 0.3,
                }
            )
        self.assertTrue(window.control_armed)

        for index in range(7):
            window._on_control_gesture(
                {
                    "name": "Thumb_Up",
                    "score": 0.95,
                    "hands": (),
                    "timestamp": 20.0 + index * 0.1,
                }
            )
        self.assertEqual(controller.volume_ups, 1)

        window.tabs.setCurrentIndex(0)
        self.assertFalse(window.control_enabled)
        self.assertFalse(window.control_armed)
        window.close()


if __name__ == "__main__":
    unittest.main()
