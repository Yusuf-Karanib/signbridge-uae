from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase

from signbridge.agent import ReceptionAgent
from signbridge.config import SEQUENCE_LENGTH, UNKNOWN_LABEL
from signbridge.dataset import DatasetStore
from signbridge.evaluation import EvaluationStore
from signbridge.integrations import AgentSettingsStore
from signbridge.landmarks import FEATURE_DIM
from signbridge.tasks import TaskStore
from signbridge.ui import MainWindow, PopSignImportWorker
from signbridge.popsign_import import PopSignClip
from signbridge.video_import import ImportedVideo


class EvaluationUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])
        for font in ("segoeui.ttf", "segoeuib.ttf"):
            path = Path("C:/Windows/Fonts") / font
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))

    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.window = MainWindow(
            reception_agent=ReceptionAgent(TaskStore.in_memory()),
            settings_store=AgentSettingsStore.in_memory(),
            auto_start_camera=False,
            dataset_store=DatasetStore(root / "samples", root / "trash"),
            evaluation_store=EvaluationStore(root / "evaluations"),
        )
        self.addCleanup(self.window.close)
        self.window.model_cache["asl"] = {
            "created_at": "model-a", "people": ["trainer-01"],
            "pipeline": SimpleNamespace(
                predict_proba=lambda _x: np.asarray([[0.99, 0.01]]),
                named_steps={"classifier": SimpleNamespace(classes_=["help", UNKNOWN_LABEL])},
            ),
        }
        self.window.eval_person_id.setText("tester-01")
        self.window.evaluation_consent_checkbox.setChecked(True)
        self.window._refresh_evaluation_tab()
        self.window.eval_expected_sign.setCurrentIndex(
            self.window.eval_expected_sign.findData("help")
        )
        self.sequence = np.zeros((SEQUENCE_LENGTH, FEATURE_DIM), dtype=np.float32)

    def _context(self) -> dict:
        context = self.window._evaluation_context()
        self.assertIsNotNone(context)
        context["capture_source"] = "imported_video"
        return context

    def test_test_video_saves_only_evaluation_and_never_speaks_or_creates_task(self) -> None:
        self.assertFalse(self.window.camera_ok)
        self.assertTrue(self.window.import_evaluation_video_button.isEnabled())
        self.window.video_import_context = self._context()
        with patch.object(self.window.speech, "speak") as speak:
            self.window._video_import_complete(
                self.sequence, {"hand_presence_ratio": 1.0, "video_sha256": "test-clip"}
            )
        attempts = self.window.evaluation.load_attempts("asl", "model-a")
        self.assertEqual(len(attempts), 1)
        self.assertTrue(attempts[0].accepted)
        self.assertEqual(attempts[0].capture_source, "imported_video")
        self.assertEqual(attempts[0].video_sha256, "test-clip")
        self.assertEqual(self.window.dataset.load_records(), [])
        self.assertEqual(self.window.reception_agent.task_store.summary()["total"], 0)
        speak.assert_not_called()

    def test_final_test_controls_fit_the_smallest_supported_window(self) -> None:
        self.window.resize(960, 640)
        self.window.show()
        self.window.tabs.setCurrentIndex(self.window.evaluation_tab_index)
        self.app.processEvents()
        self.window._apply_initial_splitter_sizes()
        self.app.processEvents()
        page = self.window.tabs.widget(self.window.evaluation_tab_index)
        self.assertLessEqual(page.widget().width(), page.viewport().width())

    def test_low_visibility_counts_as_rejection_in_final_test(self) -> None:
        self.window.video_import_context = self._context()
        self.window._video_import_complete(
            self.sequence, {"hand_presence_ratio": 0.0, "video_sha256": "dark-clip"}
        )
        attempts = self.window.evaluation.load_attempts("asl")
        self.assertEqual(len(attempts), 1)
        self.assertFalse(attempts[0].accepted)
        summary = self.window.evaluation.summary("asl", ("help",), "model-a")
        self.assertEqual(summary["per_sign_recall"]["help"], 0.0)
        self.assertEqual(summary["low_visibility_attempts"], 1)

    def test_model_training_person_is_blocked_even_if_their_samples_are_absent(self) -> None:
        self.window.eval_person_id.setText("TRAINER-01")
        self.window.evaluation_consent_checkbox.setChecked(True)
        with patch("signbridge.ui.QMessageBox.warning") as warning:
            self.assertIsNone(self.window._evaluation_context())
        warning.assert_called_once()

    def test_reusing_training_clip_with_another_person_id_is_blocked(self) -> None:
        self.window.dataset.save_sample(
            "asl", "help", "different-id", self.sequence,
            quality={"video_sha256": "same-bytes"},
        )
        self.window.video_import_context = self._context()
        with patch("signbridge.ui.QMessageBox.warning"):
            self.window._video_import_complete(
                self.sequence, {"hand_presence_ratio": 1.0, "video_sha256": "same-bytes"}
            )
        self.assertEqual(self.window.evaluation.load_attempts("asl"), [])

    def test_model_hash_blocks_a_training_clip_after_sample_removal(self) -> None:
        self.window.model_cache["asl"]["training_video_hashes"] = ["old-training-clip"]
        self.window.video_import_context = self._context()
        with patch("signbridge.ui.QMessageBox.warning"):
            self.window._video_import_complete(
                self.sequence, {"hand_presence_ratio": 1.0, "video_sha256": "old-training-clip"}
            )
        self.assertEqual(self.window.evaluation.load_attempts("asl"), [])

    def test_same_clip_cannot_inflate_current_model_test_count(self) -> None:
        self.window.video_import_context = self._context()
        quality = {"hand_presence_ratio": 1.0, "video_sha256": "repeat-clip"}
        self.window._video_import_complete(self.sequence, quality)
        with patch("signbridge.ui.QMessageBox.warning"):
            self.window._video_import_complete(self.sequence, quality)
        self.assertEqual(len(self.window.evaluation.load_attempts("asl")), 1)

    def test_final_test_clip_cannot_be_moved_into_training_under_an_alias(self) -> None:
        context = self._context()
        quality = {"hand_presence_ratio": 1.0, "video_sha256": "reserved-test-clip"}
        self.window.video_import_context = context
        self.window._video_import_complete(self.sequence, quality)
        self.window.video_import_context = {
            "purpose": "train", "language": "asl", "label": "help",
            "person_id": "new-alias", "consent_confirmed": True,
        }
        with patch("signbridge.ui.QMessageBox.warning"):
            self.window._video_import_complete(self.sequence, quality)
        self.assertEqual(self.window.dataset.load_records(), [])

    def test_model_change_during_import_does_not_mix_test_results(self) -> None:
        self.window.video_import_context = self._context()
        self.window.model_cache["asl"]["created_at"] = "model-b"
        self.window._video_import_complete(self.sequence, {"hand_presence_ratio": 1.0})
        self.assertEqual(self.window.evaluation.load_attempts("asl"), [])
        self.assertIn("model changed", self.window.evaluation_result.text())

    def test_test_permission_is_required_and_resets_for_a_different_person(self) -> None:
        self.window.eval_person_id.setText("tester-02")
        self.assertFalse(self.window.evaluation_consent_checkbox.isChecked())
        with patch("signbridge.ui.QMessageBox.warning"):
            self.assertIsNone(self.window._evaluation_context())

    def test_popsign_worker_cannot_reuse_a_final_test_clip_under_another_id(self) -> None:
        clip = PopSignClip(Path("clip.mp4"), "help", "popsign-person", "clip-id")
        worker = PopSignImportWorker(
            (clip,), self.window.dataset, reserved_video_hashes={"final-test-hash"}
        )
        failures = []
        worker.failed.connect(failures.append)
        with patch("signbridge.ui.extract_training_video", return_value=ImportedVideo(
            self.sequence, {"video_sha256": "final-test-hash", "hand_presence_ratio": 1.0}
        )):
            worker.run()
        self.assertEqual(self.window.dataset.load_records(), [])
        self.assertEqual(len(failures), 1)
        self.assertIn("reserved final-test", failures[0])

    def test_camera_status_does_not_unlock_controls_during_video_import(self) -> None:
        worker = Mock()
        worker.isRunning.return_value = True
        self.window.video_import_worker = worker
        self.window._on_camera_status("Camera unavailable", False)
        self.assertFalse(self.window.import_evaluation_video_button.isEnabled())
        self.assertFalse(self.window.train_model_button.isEnabled())
        self.assertFalse(self.window.assist_use_manual_button.isEnabled())
        self.window.video_import_worker = None

    def test_closing_waits_for_training_without_destroying_a_running_thread(self) -> None:
        from PySide6.QtGui import QCloseEvent

        worker = Mock()
        worker.isRunning.return_value = True
        self.window.training_worker = worker
        event = QCloseEvent()
        with patch("signbridge.ui.QTimer.singleShot") as schedule:
            self.window.closeEvent(event)
        self.assertFalse(event.isAccepted())
        schedule.assert_called_once()
        worker.wait.assert_not_called()
        self.window.training_worker = None

    def test_camera_failure_stays_visible_in_final_test_evidence(self) -> None:
        context = self._context()
        self.window._on_capture_failed(context, "Tracker stopped")
        summary = self.window.evaluation.summary("asl", ("help",), "model-a")
        self.assertEqual(summary["attempts"], 1)
        self.assertEqual(summary["capture_failures"], 1)
        self.assertEqual(summary["per_sign_recall"]["help"], 0.0)


if __name__ == "__main__":
    unittest.main()
