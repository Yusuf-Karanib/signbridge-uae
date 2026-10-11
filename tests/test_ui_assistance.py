from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from signbridge.assistance import AssistanceStage
from signbridge.classifier import Prediction
from signbridge.ui import MainWindow


class AssistanceUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_accepted_prediction_is_silent_until_full_request_is_confirmed(self) -> None:
        window = MainWindow()
        prediction = Prediction(
            label="help",
            confidence=0.91,
            margin=0.40,
            accepted=True,
            alternatives=(("help", 0.91), ("hello", 0.11)),
        )

        with patch.object(window.speech, "speak") as speak:
            window._show_assistance_prediction("asl", prediction)
            self.assertEqual(
                window.assistance_session.stage, AssistanceStage.CONFIRM_SIGN
            )
            self.assertEqual(window.assistance_session.turns, [])
            speak.assert_not_called()

            window._confirm_assistance_sign()
            window.assistance_session.choose_request("directions")
            window._render_assistance()
            speak.assert_not_called()

            window._send_assistance_request()
            speak.assert_called_once_with("I need help with directions.", "en-US")

        window.close()

    def test_rejected_prediction_does_not_advance_the_session(self) -> None:
        window = MainWindow()
        prediction = Prediction(
            label="help",
            confidence=0.44,
            margin=0.02,
            accepted=False,
            alternatives=(("help", 0.44), ("hello", 0.42)),
        )

        with patch.object(window.speech, "speak") as speak:
            window._show_assistance_prediction("asl", prediction)

        self.assertEqual(window.assistance_session.stage, AssistanceStage.READY)
        self.assertEqual(window.assistance_session.turns, [])
        self.assertEqual(window.assist_result_label.text(), "Not sure")
        self.assertFalse(window.assist_confirm_sign_button.isVisible())
        speak.assert_not_called()
        window.close()

    def test_default_layout_leaves_room_for_camera_and_guided_controls(self) -> None:
        window = MainWindow()
        window.resize(1540, 900)
        window.show()
        self.app.processEvents()
        window._apply_initial_splitter_sizes()
        self.app.processEvents()

        camera_width, controls_width = window.main_splitter.sizes()
        self.assertGreater(camera_width, 650)
        self.assertGreater(controls_width, 550)
        self.assertEqual(window.tabs.count(), 5)
        window.close()


if __name__ == "__main__":
    unittest.main()
