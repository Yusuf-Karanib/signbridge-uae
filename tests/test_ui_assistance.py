from __future__ import annotations

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from signbridge.agent import ReceptionAgent
from signbridge.assistance import AssistanceStage
from signbridge.classifier import Prediction
from signbridge.config import UNKNOWN_LABEL
from signbridge.integrations import AgentSettingsStore
from signbridge.tasks import TaskOutcome, TaskStatus, TaskStore, VisitorOutcome
from signbridge.ui import MainWindow


class AssistanceUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _window() -> MainWindow:
        return MainWindow(
            reception_agent=ReceptionAgent(TaskStore.in_memory()),
            settings_store=AgentSettingsStore.in_memory(),
            auto_start_camera=False,
        )

    def test_accepted_prediction_is_silent_until_full_request_is_confirmed(self) -> None:
        window = self._window()
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
            window.assistance_session.choose_request("hotel_check_in")
            window._render_assistance()
            speak.assert_not_called()
            self.assertEqual(window.assistance_action_results, [])

            window._send_assistance_request()
            speak.assert_called_once_with(
                "I need help checking in at the hotel.", "en-US"
            )
            self.assertEqual(len(window.assistance_action_results), 1)
            action = window.assistance_action_results[0]
            self.assertEqual(action.action_id, "hotel_check_in")
            self.assertFalse(action.external_action_taken)
            self.assertEqual(
                window.assistance_session.turns[-1].speaker, "Agent"
            )
            self.assertIn(action.task_id, window.reception_agent.pending_tasks)
            task = window.reception_agent.task_store.get(action.task_id)
            self.assertEqual(task.input_method, "camera")
            self.assertFalse(task.correction_used)
            self.assertEqual(task.confidence, 0.91)

            window._complete_assistance_session()
            self.assertEqual(window.assistance_action_results, [])
            self.assertEqual(window.assistance_session.turns, [])
            self.assertIn(action.task_id, window.reception_agent.pending_tasks)

        window.close()

    def test_rejected_prediction_does_not_advance_the_session(self) -> None:
        window = self._window()
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
        report = window.reception_agent.task_store.journey_summary()
        self.assertEqual(report["camera_rejected"], 1)
        self.assertEqual(report["journeys_with_tasks"], 0)
        window.close()

    def test_failed_task_write_keeps_request_confirmable_and_silent(self) -> None:
        window = self._window()
        window.assist_manual_sign.setCurrentIndex(window.assist_manual_sign.findData("help"))
        window._use_manual_assistance_sign()
        window._confirm_assistance_sign()
        window.assistance_session.choose_request("hotel_service")
        with (
            patch.object(window.reception_agent.task_store, "_save", side_effect=OSError("disk full")),
            patch.object(window.speech, "speak") as speak,
        ):
            window._send_assistance_request()
        self.assertEqual(window.assistance_session.stage, AssistanceStage.CONFIRM_REQUEST)
        self.assertEqual(window.assistance_session.turns, [])
        self.assertEqual(window.reception_agent.task_store.list_tasks(), [])
        speak.assert_not_called()
        with patch.object(window.speech, "speak"):
            window._send_assistance_request()
        self.assertEqual(len(window.reception_agent.task_store.list_tasks()), 1)
        self.assertEqual(window.reception_agent.task_store.journey_summary()["journeys_with_tasks"], 1)
        window.close()

    def test_second_turn_can_use_the_previous_staff_reply(self) -> None:
        window = self._window()

        with patch.object(window.speech, "speak"):
            window._use_manual_assistance_sign()
            window._confirm_assistance_sign()
            window.assistance_session.choose_request("start")
            window._send_assistance_request()
            window.assist_staff_reply.setText("Registration is on the left.")
            window._add_assistance_reply()
            window._continue_assistance_session()

            remembered_turns = list(window.assistance_session.turns)
            uncertain = Prediction(
                label="help",
                confidence=0.43,
                margin=0.01,
                accepted=False,
                alternatives=(("help", 0.43), ("hello", 0.42)),
            )
            window._show_assistance_prediction("asl", uncertain)
            self.assertEqual(window.assistance_session.turns, remembered_turns)
            self.assertEqual(window.assistance_session.stage, AssistanceStage.READY)

            again_index = window.assist_manual_sign.findData("again")
            window.assist_manual_sign.setCurrentIndex(again_index)
            window._use_manual_assistance_sign()
            window._confirm_assistance_sign()
            window.assistance_session.choose_request("show_again")
            window._send_assistance_request()

        latest_action = window.assistance_action_results[-1]
        self.assertTrue(latest_action.used_conversation_memory)
        self.assertIn("Registration is on the left", latest_action.message)
        self.assertEqual(window.assistance_session.stage, AssistanceStage.WAITING_REPLY)
        window.close()

    def test_default_layout_leaves_room_for_camera_and_guided_controls(self) -> None:
        window = self._window()
        window.resize(1540, 900)
        window.show()
        self.app.processEvents()
        window._apply_initial_splitter_sizes()
        self.app.processEvents()

        camera_width, controls_width = window.main_splitter.sizes()
        self.assertGreater(camera_width, 650)
        self.assertGreater(controls_width, 550)
        self.assertEqual(window.tabs.count(), 6)
        window.close()

    def test_staff_desk_can_accept_reply_to_and_complete_a_task(self) -> None:
        window = self._window()
        with patch.object(window.speech, "speak"):
            help_index = window.assist_manual_sign.findData("help")
            window.assist_manual_sign.setCurrentIndex(help_index)
            window._use_manual_assistance_sign()
            window._confirm_assistance_sign()
            window.assistance_session.choose_request("hotel_service")
            window._send_assistance_request()

        self.assertEqual(window.staff_task_table.rowCount(), 1)
        window.staff_task_table.selectRow(0)
        task = window._selected_staff_task()
        self.assertIsNotNone(task)
        task_id = task.id

        window._accept_staff_task()
        self.assertEqual(
            window.reception_agent.task_store.get(task_id).status,
            TaskStatus.ACCEPTED,
        )

        window.staff_task_table.selectRow(0)
        window.staff_reply_text.setText("Registration is beside the entrance.")
        window._reply_to_staff_task()
        saved = window.reception_agent.task_store.get(task_id)
        self.assertEqual(saved.staff_reply, "Registration is beside the entrance.")
        self.assertEqual(window.assistance_session.turns[-1].speaker, "Staff")

        window.staff_task_table.selectRow(0)
        window._complete_staff_task()
        self.assertEqual(
            window.reception_agent.task_store.get(task_id).status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(
            window.reception_agent.task_store.get(task_id).outcome,
            TaskOutcome.UNREVIEWED,
        )
        self.assertEqual(window.staff_task_table.rowCount(), 0)

        window._visitor_request_resolved()
        confirmed = window.reception_agent.task_store.get(task_id)
        self.assertEqual(confirmed.outcome, TaskOutcome.SUCCESS)
        self.assertEqual(confirmed.visitor_outcome, VisitorOutcome.RESOLVED)
        window.close()

    def test_guest_needs_help_reopens_the_hotel_task(self) -> None:
        window = self._window()
        with patch.object(window.speech, "speak"):
            help_index = window.assist_manual_sign.findData("help")
            window.assist_manual_sign.setCurrentIndex(help_index)
            window._use_manual_assistance_sign()
            window._confirm_assistance_sign()
            window.assistance_session.choose_request("hotel_service")
            window._send_assistance_request()

        task_id = window.assistance_action_results[-1].task_id
        window.reception_agent.task_store.update_status(
            task_id, TaskStatus.COMPLETED
        )
        window._visitor_still_needs_help()

        reopened = window.reception_agent.task_store.get(task_id)
        self.assertEqual(reopened.status, TaskStatus.ACCEPTED)
        self.assertEqual(reopened.outcome, TaskOutcome.UNREVIEWED)
        self.assertEqual(reopened.visitor_outcome, VisitorOutcome.NEEDS_HELP)
        self.assertIn("reopened", window.assistance_feedback.lower())
        window.close()

    def test_competition_demo_hides_setup_and_experiment_tabs(self) -> None:
        window = self._window()
        window._toggle_demo_mode()

        self.assertTrue(window.demo_mode_enabled)
        self.assertEqual(window.assist_language.currentData(), "asl")
        self.assertTrue(window.tabs.isTabVisible(window.assistance_tab_index))
        self.assertTrue(window.tabs.isTabVisible(window.staff_tab_index))
        self.assertFalse(window.tabs.isTabVisible(window.training_tab_index))
        self.assertFalse(window.tabs.isTabVisible(window.control_tab_index))
        self.assertEqual(window.assist_manual_sign.count(), 1)
        self.assertEqual(window.assist_manual_sign.currentData(), "help")

        window._use_manual_assistance_sign()
        window._confirm_assistance_sign()
        visible_options = window.assistance_session.available_options(
            frozenset({"hotel_check_in", "hotel_service", "interpreter"})
        )
        self.assertEqual(
            {option.id for option in visible_options},
            {"hotel_check_in", "hotel_service", "interpreter"},
        )
        with self.assertRaises(ValueError):
            window.assistance_session.choose_request(
                "other",
                allowed_ids=frozenset(
                    {"hotel_check_in", "hotel_service", "interpreter"}
                ),
            )

        window._toggle_demo_mode()
        self.assertTrue(window.tabs.isTabVisible(window.training_tab_index))
        self.assertEqual(window.assist_manual_sign.count(), 4)
        window.close()

    def test_current_phase_exposes_only_asl_with_english_output(self) -> None:
        window = self._window()

        for combo in (
            window.use_language,
            window.assist_language,
            window.train_language,
            window.eval_language,
        ):
            self.assertEqual(combo.count(), 1)
            self.assertEqual(combo.currentData(), "asl")
            self.assertFalse(combo.isEnabled())

        self.assertIn("ASL signs", window.scope_label.text())
        self.assertIn("English", window.scope_label.text())
        window.close()

    def test_no_hand_sample_is_allowed_only_for_other_training(self) -> None:
        window = self._window()
        quality = {
            "processed_frames": 20,
            "hand_frames": 0,
            "hand_presence_ratio": 0.0,
        }
        context = {
            "purpose": "train",
            "language": "asl",
            "label": UNKNOWN_LABEL,
            "person_id": "trainer-01",
        }
        with patch.object(window.dataset, "save_sample") as save_sample:
            window._on_sequence_ready(object(), context, quality)
            save_sample.assert_called_once()

        context["label"] = "help"
        with (
            patch.object(window.dataset, "save_sample") as save_sample,
            patch("signbridge.ui.QMessageBox.warning"),
        ):
            window._on_sequence_ready(object(), context, quality)
            save_sample.assert_not_called()
        window.close()

    def test_live_training_requires_explicit_consent(self) -> None:
        window = self._window()
        window.person_id.setText("trainer-01")

        with patch("signbridge.ui.QMessageBox.warning") as warning:
            self.assertIsNone(window._training_context())
            warning.assert_called_once()

        window.training_consent_checkbox.setChecked(True)
        context = window._training_context()
        self.assertIsNotNone(context)
        self.assertTrue(context["consent_confirmed"])
        window.close()

    def test_broken_saved_model_does_not_stop_the_app(self) -> None:
        with patch("signbridge.ui.load_model", side_effect=ValueError("old model")):
            window = self._window()

        self.assertTrue(window.model_load_errors)
        self.assertTrue(all(bundle is None for bundle in window.model_cache.values()))
        window.close()


if __name__ == "__main__":
    unittest.main()
