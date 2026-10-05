from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication

from signbridge.ui import MainWindow


class FakeController:
    is_supported = True

    def __init__(self) -> None:
        self.volume_ups = 0
        self.pointer_moves: list[tuple[float, float]] = []
        self.clicks = 0

    def volume_up(self) -> bool:
        self.volume_ups += 1
        return True

    def volume_down(self) -> bool:
        return True

    def next_slide(self) -> bool:
        return True

    def previous_slide(self) -> bool:
        return True

    def move_pointer(self, x: float, y: float) -> bool:
        self.pointer_moves.append((x, y))
        return True

    def pointer_position(self) -> tuple[float, float]:
        return 0.5, 0.5

    def click(self) -> bool:
        self.clicks += 1
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

        for index in range(14):
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

    def test_mouse_requires_pointing_and_moves_relative_to_current_pointer(self) -> None:
        window = MainWindow()
        controller = FakeController()
        window.computer_controller = controller
        hand = np.zeros((21, 3), dtype=np.float32)
        hand[0, :2] = (0.5, 0.7)
        hand[9, :2] = (0.5, 0.5)
        hand[8, :2] = (0.5, 0.3)
        hand[4, :2] = (0.3, 0.5)

        window._run_mouse_control(
            {"name": "Open_Palm", "score": 0.95, "hands": (hand,), "hand_index": 0},
            1.0,
        )
        self.assertEqual(controller.pointer_moves, [])

        window._run_mouse_control(
            {"name": "Pointing_Up", "score": 0.95, "hands": (hand,), "hand_index": 0},
            2.0,
        )
        self.assertEqual(controller.pointer_moves, [])

        moved_hand = hand.copy()
        moved_hand[8, 0] = 0.53
        window._run_mouse_control(
            {
                "name": "Pointing_Up",
                "score": 0.95,
                "hands": (moved_hand,),
                "hand_index": 0,
            },
            2.1,
        )
        self.assertEqual(len(controller.pointer_moves), 1)
        self.assertLess(controller.pointer_moves[0][0], 0.5)

        jittered_hand = moved_hand.copy()
        jittered_hand[8, 0] += 0.002
        window._run_mouse_control(
            {
                "name": "Pointing_Up",
                "score": 0.95,
                "hands": (jittered_hand,),
                "hand_index": 0,
            },
            2.2,
        )
        self.assertEqual(len(controller.pointer_moves), 1)

        pinched_hand = jittered_hand.copy()
        pinched_hand[4, :2] = pinched_hand[8, :2]
        window._run_mouse_control(
            {"name": "None", "score": 0.0, "hands": (pinched_hand,), "hand_index": 0},
            3.0,
        )
        self.assertEqual(controller.clicks, 1)
        window.close()

    def test_low_camera_quality_is_clearly_marked(self) -> None:
        window = MainWindow()

        window._on_camera_performance(
            "Camera 0 • 160×120 • 10 preview FPS • LOW CAMERA QUALITY: test"
        )

        self.assertTrue(window.camera_performance_label.property("warning"))
        self.assertEqual(window.system_status.text(), "Camera 0 • LOW QUALITY")
        window.close()


if __name__ == "__main__":
    unittest.main()
