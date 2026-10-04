from __future__ import annotations

from collections import Counter, deque
from functools import partial
import math
import time
from typing import Any

import cv2
from PySide6.QtCore import QThread, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCloseEvent, QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signbridge.camera import CameraWorker
from signbridge.classifier import load_model, predict_sequence, train_language_model
from signbridge.computer_control import ComputerController
from signbridge.config import (
    MIN_HAND_PRESENCE_RATIO,
    MIN_SAMPLES_PER_CLASS,
    PERSONAL_DEMO_SAMPLES_PER_CLASS,
    RECOMMENDED_SAMPLES_PER_CLASS,
    UNKNOWN_LABEL,
)
from signbridge.dataset import DatasetStore
from signbridge.evaluation import EvaluationStore
from signbridge.speech import SpeechService
from signbridge.validation import ValidationStore
from signbridge.vocabulary import LanguagePack, Vocabulary


APP_STYLE = """
QMainWindow, QWidget {
    background: #07111f;
    color: #e8eef7;
    font-family: "Segoe UI";
    font-size: 14px;
}
QFrame#card {
    background: #0d1b2b;
    border: 1px solid #1d3146;
    border-radius: 16px;
}
QFrame#resultCard {
    background: #10283a;
    border: 1px solid #2b5268;
    border-radius: 14px;
}
QLabel#title {
    color: #ffffff;
    font-size: 28px;
    font-weight: 700;
}
QLabel#subtitle, QLabel#muted {
    color: #9fb1c5;
}
QLabel#cameraState {
    color: #dbe8f6;
    background: #0b1725;
    border: 1px solid #23384c;
    border-radius: 10px;
    padding: 8px 12px;
}
QLabel#result {
    color: #ffffff;
    font-size: 36px;
    font-weight: 750;
}
QLabel#warning {
    background: #2a2210;
    color: #f5d98d;
    border: 1px solid #584719;
    border-radius: 10px;
    padding: 9px 12px;
}
QLabel#success {
    background: #0f2d29;
    color: #94e2ce;
    border: 1px solid #276157;
    border-radius: 10px;
    padding: 8px 12px;
}
QPushButton {
    background: #18314a;
    border: 1px solid #2a4d6d;
    border-radius: 10px;
    color: #eff6ff;
    padding: 10px 14px;
    font-weight: 600;
}
QPushButton:hover { background: #21415f; }
QPushButton:pressed { background: #10283b; }
QPushButton:disabled { color: #60758a; background: #101d2a; border-color: #1c2b39; }
QPushButton#primary {
    background: #12a594;
    border-color: #2cc6b4;
    color: #041713;
    font-size: 16px;
    padding: 13px 18px;
}
QPushButton#primary:hover { background: #28b8a7; }
QPushButton#danger { background: #43212a; border-color: #743948; }
QComboBox, QLineEdit {
    background: #0a1724;
    border: 1px solid #2b4156;
    border-radius: 9px;
    color: #edf5ff;
    padding: 9px 11px;
    min-height: 20px;
}
QComboBox QAbstractItemView {
    background: #122438;
    color: #edf5ff;
    selection-background-color: #1b887d;
}
QTabWidget::pane { border: none; }
QTabBar::tab {
    background: #0a1724;
    border: 1px solid #1e3347;
    color: #90a4b9;
    padding: 10px 18px;
    margin-right: 4px;
    border-radius: 8px;
}
QTabBar::tab:selected { color: #ffffff; background: #17334b; }
QListWidget, QTableWidget {
    background: #091522;
    border: 1px solid #203448;
    border-radius: 10px;
    color: #dce8f5;
    alternate-background-color: #0e1e2d;
    gridline-color: #203448;
}
QHeaderView::section {
    background: #13283a;
    color: #b9c9d9;
    border: none;
    padding: 8px;
}
QProgressBar {
    border: 1px solid #274158;
    border-radius: 7px;
    background: #091522;
    color: #e9f3fb;
    text-align: center;
    min-height: 18px;
}
QProgressBar::chunk { background: #19a999; border-radius: 6px; }
QFrame#sectionCard {
    background: #0a1724;
    border: 1px solid #1c3348;
    border-radius: 13px;
}
QLabel#sectionTitle {
    color: #f5f8fc;
    font-size: 16px;
    font-weight: 700;
}
QLabel#sectionHint {
    color: #8298ae;
    font-size: 13px;
}
QLabel#signBadge {
    color: #dce9f5;
    background: #102338;
    border: 1px solid #244159;
    border-radius: 9px;
    padding: 9px 11px;
}
QLabel#modelStatus {
    color: #f1d88f;
    background: #2a2210;
    border: 1px solid #5a481a;
    border-radius: 9px;
    padding: 8px 10px;
}
QLabel#modelStatus[ready="true"] {
    color: #a9eadc;
    background: #0c2828;
    border-color: #225753;
}
QPushButton#primary:disabled {
    color: #65798c;
    background: #122231;
    border-color: #233749;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical {
    background: #08131f;
    width: 10px;
    margin: 2px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #2b4c65;
    min-height: 36px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: transparent; width: 12px; }
"""


class TrainingWorker(QThread):
    complete = Signal(object)
    failed = Signal(str)

    def __init__(self, language: str, pack: LanguagePack, store: DatasetStore):
        super().__init__()
        self.language = language
        self.pack = pack
        self.store = store

    def run(self) -> None:
        try:
            bundle = train_language_model(self.language, self.pack, self.store)
            self.complete.emit(bundle)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.vocabulary = Vocabulary.load()
        self.dataset = DatasetStore()
        self.evaluation = EvaluationStore()
        self.validation = ValidationStore()
        self.speech = SpeechService(self)
        self.model_cache: dict[str, dict | None] = {
            language: load_model(
                language,
                expected_labels=list(self.vocabulary.pack(language).sign_ids)
                + [UNKNOWN_LABEL],
            )
            for language in self.vocabulary.packs
        }
        self.history_entries: list[dict[str, str]] = []
        self.last_spoken: tuple[str, str] | None = None
        self.training_worker: TrainingWorker | None = None
        self.camera_worker = CameraWorker(parent=self)
        self.camera_ok = False
        self.computer_controller = ComputerController()
        self.control_enabled = False
        self.control_armed = False
        self.control_palm_started: float | None = None
        self.control_armed_until = 0.0
        self.control_votes: deque[str | None] = deque(maxlen=7)
        self.control_cursor_position: tuple[float, float] | None = None
        self.control_pinching = False
        self.control_last_click = 0.0
        self.control_last_actions: dict[str, float] = {}
        self.control_previous_gesture: str | None = None

        self.setWindowTitle("SignBridge UAE")
        self.resize(1540, 900)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._connect_events()
        self._refresh_all()
        QTimer.singleShot(200, self._start_selected_camera)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(26, 22, 26, 24)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_group = QVBoxLayout()
        title = QLabel("SignBridge UAE")
        title.setObjectName("title")
        self.subtitle_label = QLabel(
            "8-sign bilingual prototype  •  camera  →  text  →  speech"
        )
        self.subtitle_label.setObjectName("subtitle")
        title_group.addWidget(title)
        title_group.addWidget(self.subtitle_label)
        header.addLayout(title_group)
        header.addStretch()
        self.system_status = QLabel("Starting camera…")
        self.system_status.setObjectName("cameraState")
        header.addWidget(self.system_status)
        self.fullscreen_button = QPushButton("Full screen")
        self.fullscreen_button.setToolTip("Full screen (F11)")
        header.addWidget(self.fullscreen_button)
        self.reset_layout_button = QPushButton("Reset layout")
        self.reset_layout_button.setToolTip("Restore the recommended window and panel sizes")
        header.addWidget(self.reset_layout_button)
        root.addLayout(header)

        scope = QLabel(
            "Prototype scope: 4 ASL signs + 4 Emirati signs. One prompted sign at a time — not conversation translation."
        )
        scope.setWordWrap(True)
        scope.setObjectName("warning")
        root.addWidget(scope)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setToolTip("Drag this divider to resize the camera and controls")
        root.addWidget(self.main_splitter, 1)

        camera_card = QFrame()
        camera_card.setObjectName("card")
        camera_layout = QVBoxLayout(camera_card)
        camera_layout.setContentsMargins(18, 18, 18, 18)
        camera_layout.setSpacing(12)
        camera_header = QHBoxLayout()
        camera_header.setSpacing(8)
        camera_heading = QLabel("Live camera")
        camera_heading.setObjectName("sectionTitle")
        camera_header.addWidget(camera_heading)
        camera_header.addStretch()
        camera_number_label = QLabel("Camera")
        camera_number_label.setObjectName("muted")
        camera_header.addWidget(camera_number_label)
        self.camera_selector = QComboBox()
        self.camera_selector.setToolTip(
            "If the wrong camera opens, choose another number and press Restart"
        )
        for camera_index in range(3):
            self.camera_selector.addItem(str(camera_index), camera_index)
        self.camera_selector.setMaximumWidth(64)
        camera_header.addWidget(self.camera_selector)
        self.restart_camera_button = QPushButton("Restart")
        self.restart_camera_button.setToolTip(
            "Apply the selected camera number and restart the camera connection"
        )
        self.restart_camera_button.setMaximumWidth(100)
        camera_header.addWidget(self.restart_camera_button)
        camera_layout.addLayout(camera_header)
        camera_hint = QLabel("Keep your head, shoulders and both hands inside the frame.")
        camera_hint.setObjectName("sectionHint")
        camera_layout.addWidget(camera_hint)
        self.camera_preview = QLabel("Camera preview will appear here")
        self.camera_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview.setMinimumSize(420, 260)
        self.camera_preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.camera_preview.setStyleSheet(
            "background:#030912; border:1px solid #1f3345; border-radius:12px; color:#63778a;"
        )
        camera_layout.addWidget(self.camera_preview, 1)
        self.camera_performance_label = QLabel("Starting camera…")
        self.camera_performance_label.setObjectName("muted")
        self.camera_performance_label.setWordWrap(True)
        camera_layout.addWidget(self.camera_performance_label)
        camera_bottom = QHBoxLayout()
        self.capture_state_label = QLabel("Waiting for camera")
        self.capture_state_label.setObjectName("muted")
        self.capture_progress = QProgressBar()
        self.capture_progress.setRange(0, 100)
        self.capture_progress.setValue(0)
        self.capture_progress.setMaximumWidth(260)
        camera_bottom.addWidget(self.capture_state_label)
        camera_bottom.addStretch()
        camera_bottom.addWidget(self.capture_progress)
        camera_layout.addLayout(camera_bottom)
        self.main_splitter.addWidget(camera_card)

        side_card = QFrame()
        side_card.setObjectName("card")
        side_card.setMinimumWidth(420)
        side_layout = QVBoxLayout(side_card)
        side_layout.setContentsMargins(14, 14, 14, 14)
        self.tabs = QTabWidget()
        self.tabs.tabBar().setExpanding(True)
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_use_tab(), "Recognize")
        self.tabs.addTab(self._build_training_tab(), "Train model")
        self.tabs.addTab(self._build_evaluation_tab(), "Final test")
        self.tabs.addTab(self._build_control_tab(), "Computer control")
        side_layout.addWidget(self.tabs)
        self.main_splitter.addWidget(side_card)
        self.main_splitter.setStretchFactor(0, 6)
        self.main_splitter.setStretchFactor(1, 5)
        self.main_splitter.setSizes((850, 650))

    @staticmethod
    def _scroll_page() -> tuple[QScrollArea, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 14, 12, 18)
        layout.setSpacing(14)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(page)
        return scroll, layout

    @staticmethod
    def _section_card(
        title: str, hint: str = ""
    ) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("sectionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        if hint:
            description = QLabel(hint)
            description.setWordWrap(True)
            description.setObjectName("sectionHint")
            layout.addWidget(description)
        return card, layout

    def _language_combo(self) -> QComboBox:
        combo = QComboBox()
        for language_id, pack in self.vocabulary.packs.items():
            combo.addItem(pack.name, language_id)
        return combo

    def _build_use_tab(self) -> QWidget:
        tab, layout = self._scroll_page()

        language_card, language_layout = self._section_card(
            "Recognize one sign",
            "1. Choose the language  •  2. Press Record  •  3. Perform one complete sign while the bar fills.",
        )
        language_label = QLabel("Sign language")
        language_label.setObjectName("muted")
        language_layout.addWidget(language_label)
        self.use_language = self._language_combo()
        language_layout.addWidget(self.use_language)
        self.use_model_status = QLabel()
        self.use_model_status.setWordWrap(True)
        self.use_model_status.setObjectName("modelStatus")
        language_layout.addWidget(self.use_model_status)
        layout.addWidget(language_card)

        vocabulary_card, vocabulary_layout = self._section_card(
            "Supported vocabulary",
            "The selected model can return only these four signs.",
        )
        vocabulary_grid = QGridLayout()
        vocabulary_grid.setHorizontalSpacing(10)
        vocabulary_grid.setVerticalSpacing(8)
        self.supported_sign_labels: list[QLabel] = []
        sign_count = max(len(pack.signs) for pack in self.vocabulary.packs.values())
        for index in range(sign_count):
            badge = QLabel("—")
            badge.setObjectName("signBadge")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setMinimumHeight(38)
            self.supported_sign_labels.append(badge)
            vocabulary_grid.addWidget(badge, index // 2, index % 2)
        vocabulary_layout.addLayout(vocabulary_grid)

        result_card = QFrame()
        result_card.setObjectName("resultCard")
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(18, 16, 18, 18)
        result_layout.setSpacing(8)
        result_title = QLabel("Latest result")
        result_title.setObjectName("muted")
        self.result_label = QLabel("—")
        self.result_label.setObjectName("result")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setMinimumHeight(50)
        self.confidence_label = QLabel("No prediction yet")
        self.confidence_label.setObjectName("muted")
        self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.confidence_label)
        result_layout.addWidget(self.confidence_bar)

        self.candidate_prompt = QLabel("Choose the intended sign:")
        self.candidate_prompt.setObjectName("muted")
        self.candidate_prompt.hide()
        result_layout.addWidget(self.candidate_prompt)
        candidate_row = QHBoxLayout()
        candidate_row.setSpacing(10)
        self.candidate_buttons = [QPushButton(), QPushButton()]
        for button in self.candidate_buttons:
            button.clicked.connect(self._commit_candidate)
            button.hide()
            candidate_row.addWidget(button)
        result_layout.addLayout(candidate_row)
        layout.addWidget(result_card)

        self.capture_use_button = QPushButton("Record one sign")
        self.capture_use_button.setObjectName("primary")
        self.capture_use_button.setMinimumHeight(54)
        result_layout.addWidget(self.capture_use_button)

        self.auto_speak_checkbox = QCheckBox(
            "Speak automatically after a confident result"
        )
        self.auto_speak_checkbox.setChecked(False)
        self.auto_speak_checkbox.setToolTip(
            "Leave this off during testing. Press Speak result after checking the text."
        )
        layout.addWidget(self.auto_speak_checkbox)
        layout.addWidget(vocabulary_card)

        history_card, history_layout = self._section_card(
            "Session history",
            "This is a temporary list of isolated results, not a translated sentence.",
        )
        self.history_list = QListWidget()
        self.history_list.setMinimumHeight(105)
        self.history_list.setMaximumHeight(150)
        history_layout.addWidget(self.history_list)
        history_buttons = QHBoxLayout()
        history_buttons.setSpacing(8)
        self.undo_button = QPushButton("Undo")
        self.clear_button = QPushButton("Clear")
        self.replay_button = QPushButton("Speak result")
        history_buttons.addWidget(self.replay_button, 2)
        history_buttons.addWidget(self.undo_button, 1)
        history_buttons.addWidget(self.clear_button, 1)
        history_layout.addLayout(history_buttons)
        self.voice_status = QLabel("Voice ready")
        self.voice_status.setObjectName("muted")
        history_layout.addWidget(self.voice_status)
        layout.addWidget(history_card)
        layout.addStretch()
        return tab

    def _build_evaluation_tab(self) -> QWidget:
        tab, layout = self._scroll_page()

        notice = QLabel(
            "Use only people who were never recorded for training. Final-test results never become training data."
        )
        notice.setWordWrap(True)
        notice.setObjectName("warning")
        layout.addWidget(notice)

        setup_card, setup_layout = self._section_card(
            "1. Prepare one test attempt",
            "Tell the app what the untouched tester is expected to perform.",
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.addWidget(QLabel("Language"), 0, 0)
        self.eval_language = self._language_combo()
        grid.addWidget(self.eval_language, 0, 1)
        grid.addWidget(QLabel("Tester ID"), 1, 0)
        self.eval_person_id = QLineEdit()
        self.eval_person_id.setPlaceholderText("Example: final-01")
        grid.addWidget(self.eval_person_id, 1, 1)
        grid.addWidget(QLabel("Expected sign"), 2, 0)
        self.eval_expected_sign = QComboBox()
        grid.addWidget(self.eval_expected_sign, 2, 1)
        grid.addWidget(QLabel("Test condition"), 3, 0)
        self.eval_condition = QComboBox()
        self.eval_condition.addItems(
            (
                "Normal indoor",
                "Dim lighting",
                "Bright background",
                "Cluttered background",
                "Different distance",
            )
        )
        grid.addWidget(self.eval_condition, 3, 1)
        grid.setColumnStretch(1, 1)
        setup_layout.addLayout(grid)
        layout.addWidget(setup_card)

        self.record_evaluation_button = QPushButton("Record final-test attempt")
        self.record_evaluation_button.setObjectName("primary")
        self.record_evaluation_button.setMinimumHeight(52)
        layout.addWidget(self.record_evaluation_button)

        result_card, result_layout = self._section_card("Latest attempt")
        self.evaluation_result = QLabel("No final-test attempt yet")
        self.evaluation_result.setWordWrap(True)
        self.evaluation_result.setObjectName("muted")
        self.evaluation_result.setMinimumHeight(38)
        result_layout.addWidget(self.evaluation_result)
        layout.addWidget(result_card)

        score_card, score_layout = self._section_card(
            "2. Current-model results",
            "A score appears only from attempts made with this exact trained model.",
        )
        self.evaluation_table = QTableWidget(0, 3)
        self.evaluation_table.setHorizontalHeaderLabels(("Expected", "Attempts", "Correct"))
        self.evaluation_table.verticalHeader().setVisible(False)
        self.evaluation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.evaluation_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.evaluation_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.evaluation_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.evaluation_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.evaluation_table.setMinimumHeight(260)
        self.evaluation_table.setMaximumHeight(310)
        score_layout.addWidget(self.evaluation_table)

        self.evaluation_summary = QLabel()
        self.evaluation_summary.setWordWrap(True)
        self.evaluation_summary.setObjectName("muted")
        score_layout.addWidget(self.evaluation_summary)
        layout.addWidget(score_card)
        layout.addStretch()
        return tab

    def _build_training_tab(self) -> QWidget:
        tab, layout = self._scroll_page()

        notice = QLabel(
            "Validate each exact sign with a fluent signer before collecting many examples. The app stores landmarks, not camera video."
        )
        notice.setWordWrap(True)
        notice.setObjectName("warning")
        layout.addWidget(notice)

        setup_card, setup_layout = self._section_card(
            "1. Choose the training example",
            "Keep one consistent Person ID for the same person across every sign.",
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.addWidget(QLabel("Language"), 0, 0)
        self.train_language = self._language_combo()
        grid.addWidget(self.train_language, 0, 1)
        grid.addWidget(QLabel("Person ID"), 1, 0)
        self.person_id = QLineEdit()
        self.person_id.setPlaceholderText("Example: yusuf or tester-02")
        grid.addWidget(self.person_id, 1, 1)
        grid.addWidget(QLabel("Sign to record"), 2, 0)
        self.train_sign = QComboBox()
        grid.addWidget(self.train_sign, 2, 1)
        grid.setColumnStretch(1, 1)
        setup_layout.addLayout(grid)
        self.reference_link = QLabel()
        self.reference_link.setOpenExternalLinks(True)
        self.reference_link.setWordWrap(True)
        self.reference_link.setObjectName("muted")
        setup_layout.addWidget(self.reference_link)
        layout.addWidget(setup_card)

        review_card, review_layout = self._section_card(
            "2. Confirm the sign form",
            "Record who checked the exact movement before marking it reviewed.",
        )
        self.validator_name = QLineEdit()
        self.validator_name.setPlaceholderText("Fluent signer / interpreter name")
        review_layout.addWidget(self.validator_name)
        self.mark_reviewed_button = QPushButton("Mark selected sign reviewed")
        review_layout.addWidget(self.mark_reviewed_button)
        layout.addWidget(review_card)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        self.record_training_button = QPushButton("Record training sample")
        self.record_training_button.setObjectName("primary")
        self.record_training_button.setMinimumHeight(52)
        self.delete_last_button = QPushButton("Remove last sample")
        self.delete_last_button.setObjectName("danger")
        button_row.addWidget(self.record_training_button, 2)
        button_row.addWidget(self.delete_last_button, 1)
        layout.addLayout(button_row)

        progress_card, progress_layout = self._section_card(
            "3. Collection progress",
            f"Personalized demo: {PERSONAL_DEMO_SAMPLES_PER_CLASS}–30 per class. "
            f"Stronger multi-person target: {RECOMMENDED_SAMPLES_PER_CLASS} total per class.",
        )
        self.training_table = QTableWidget(0, 3)
        self.training_table.setHorizontalHeaderLabels(("Sign", "Samples", "Form review"))
        self.training_table.verticalHeader().setVisible(False)
        self.training_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.training_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.training_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.training_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.training_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.training_table.setMinimumHeight(270)
        self.training_table.setMaximumHeight(320)
        progress_layout.addWidget(self.training_table)
        self.training_status = QLabel()
        self.training_status.setWordWrap(True)
        self.training_status.setObjectName("muted")
        progress_layout.addWidget(self.training_status)
        layout.addWidget(progress_card)

        model_card, model_layout = self._section_card(
            "4. Build the recognition model",
            "Retrain after adding or removing examples.",
        )
        self.train_model_button = QPushButton("Train or update this language model")
        self.train_model_button.setMinimumHeight(46)
        model_layout.addWidget(self.train_model_button)
        layout.addWidget(model_card)
        layout.addStretch()
        return tab

    def _build_control_tab(self) -> QWidget:
        tab, layout = self._scroll_page()

        notice = QLabel(
            "Computer control uses generic hand gestures. They are shortcuts, not ASL or Emirati signs."
        )
        notice.setWordWrap(True)
        notice.setObjectName("warning")
        layout.addWidget(notice)

        safety_card, safety_layout = self._section_card(
            "1. Turn control on safely",
            "Control starts OFF. Turn it on, then hold an open palm for 1.5 seconds. Leaving this tab stops it.",
        )
        self.control_enable_button = QPushButton("Turn computer control on")
        self.control_enable_button.setObjectName("primary")
        self.control_enable_button.setMinimumHeight(52)
        self.control_enable_button.setEnabled(self.computer_controller.is_supported)
        safety_layout.addWidget(self.control_enable_button)
        self.control_arm_status = QLabel(
            "OFF — gestures can be seen, but they cannot control the computer."
        )
        self.control_arm_status.setWordWrap(True)
        self.control_arm_status.setObjectName("modelStatus")
        safety_layout.addWidget(self.control_arm_status)
        layout.addWidget(safety_card)

        mode_card, mode_layout = self._section_card(
            "2. Choose what the hand controls"
        )
        self.control_mode = QComboBox()
        self.control_mode.addItem("Volume and slides", "media")
        self.control_mode.addItem("Mouse pointer and click", "mouse")
        mode_layout.addWidget(self.control_mode)
        self.control_mode_help = QLabel()
        self.control_mode_help.setWordWrap(True)
        self.control_mode_help.setObjectName("sectionHint")
        mode_layout.addWidget(self.control_mode_help)
        layout.addWidget(mode_card)

        tracking_card, tracking_layout = self._section_card(
            "3. Live gesture tracking",
            "The result is steadied across seven camera frames to reduce accidental actions.",
        )
        self.control_detected = QLabel("No hand gesture yet")
        self.control_detected.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.control_detected.setObjectName("sectionTitle")
        tracking_layout.addWidget(self.control_detected)
        self.control_confidence = QProgressBar()
        self.control_confidence.setRange(0, 100)
        self.control_confidence.setValue(0)
        tracking_layout.addWidget(self.control_confidence)
        layout.addWidget(tracking_card)

        history_card, history_layout = self._section_card(
            "Recent control actions",
            "Only actions actually sent to Windows appear here.",
        )
        self.control_history = QListWidget()
        self.control_history.setMinimumHeight(105)
        self.control_history.setMaximumHeight(150)
        history_layout.addWidget(self.control_history)
        layout.addWidget(history_card)
        layout.addStretch()
        self._refresh_control_mode_help()
        return tab

    def _connect_events(self) -> None:
        self.camera_worker.frame_ready.connect(self._on_frame)
        self.camera_worker.camera_status.connect(self._on_camera_status)
        self.camera_worker.performance_status.connect(self._on_camera_performance)
        self.camera_worker.gesture_ready.connect(self._on_control_gesture)
        self.camera_worker.capture_state.connect(self._on_capture_state)
        self.camera_worker.sequence_ready.connect(self._on_sequence_ready)
        self.speech.status_changed.connect(self.voice_status.setText)

        self.use_language.currentIndexChanged.connect(self._refresh_use_tab)
        self.train_language.currentIndexChanged.connect(self._refresh_training_tab)
        self.eval_language.currentIndexChanged.connect(self._refresh_evaluation_tab)
        self.train_sign.currentIndexChanged.connect(self._refresh_training_status)
        self.capture_use_button.clicked.connect(self._capture_for_use)
        self.record_training_button.clicked.connect(self._capture_training_sample)
        self.record_evaluation_button.clicked.connect(self._capture_evaluation_sample)
        self.delete_last_button.clicked.connect(self._remove_last_sample)
        self.train_model_button.clicked.connect(self._train_model)
        self.mark_reviewed_button.clicked.connect(self._mark_sign_reviewed)
        self.undo_button.clicked.connect(self._undo_history)
        self.clear_button.clicked.connect(self._clear_history)
        self.replay_button.clicked.connect(self._speak_current_result)
        self.fullscreen_button.clicked.connect(self._toggle_full_screen)
        self.reset_layout_button.clicked.connect(self._reset_layout)
        self.restart_camera_button.clicked.connect(self._restart_camera)
        self.control_enable_button.clicked.connect(self._toggle_computer_control)
        self.control_mode.currentIndexChanged.connect(self._on_control_mode_changed)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _toggle_full_screen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self._update_responsive_labels()

    def _reset_layout(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        screen = self.screen().availableGeometry()
        width = min(1540, max(960, screen.width() - 80))
        height = min(900, max(640, screen.height() - 80))
        self.resize(width, height)
        self.move(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2,
        )
        self.main_splitter.setSizes((int(width * 0.57), int(width * 0.43)))
        self._update_responsive_labels()

    def _update_responsive_labels(self) -> None:
        compact = self.width() < 1180
        tab_names = (
            ("Use", "Train", "Test", "Control")
            if compact
            else ("Recognize", "Train model", "Final test", "Computer control")
        )
        for index, name in enumerate(tab_names):
            self.tabs.setTabText(index, name)
        self.subtitle_label.setVisible(not compact)
        self.reset_layout_button.setText("Reset" if compact else "Reset layout")
        if self.isFullScreen():
            self.fullscreen_button.setText("Exit full")
        else:
            self.fullscreen_button.setText("Full" if compact else "Full screen")
        self.system_status.setMaximumWidth(165 if compact else 240)
        self.fullscreen_button.setMaximumWidth(105 if compact else 140)
        self.reset_layout_button.setMaximumWidth(105 if compact else 140)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        if hasattr(self, "tabs"):
            self._update_responsive_labels()

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_F11:
            self._toggle_full_screen()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self._toggle_full_screen()
            event.accept()
            return
        super().keyPressEvent(event)

    @staticmethod
    def _combo_language(combo: QComboBox) -> str:
        return str(combo.currentData())

    def _pack_for_combo(self, combo: QComboBox) -> LanguagePack:
        return self.vocabulary.pack(self._combo_language(combo))

    def _refresh_all(self) -> None:
        self._refresh_use_tab()
        self._refresh_training_tab()
        self._refresh_evaluation_tab()
        self._refresh_control_ui()
        self._render_history()

    def _refresh_use_tab(self) -> None:
        language = self._combo_language(self.use_language)
        pack = self.vocabulary.pack(language)
        direction = (
            Qt.LayoutDirection.RightToLeft
            if pack.direction == "rtl"
            else Qt.LayoutDirection.LeftToRight
        )
        for badge, sign in zip(self.supported_sign_labels, pack.signs):
            badge.setText(f"{sign.output}  ·  {sign.gloss}")
            badge.setLayoutDirection(direction)
        bundle = self.model_cache.get(language)
        reviewed = self.validation.reviewed_count(language, pack.sign_ids)
        if bundle is None:
            model_text = "Not trained yet. Open Train model to record examples."
        else:
            metrics = bundle.get("metrics", {})
            if metrics.get("validated_on_unseen_people"):
                score = metrics.get("balanced_accuracy", 0.0) * 100
                model_text = f"Model trained • unseen-person score: {score:.1f}%"
            else:
                model_text = "Model trained • unseen-person testing is still required."
        self.use_model_status.setProperty("ready", bundle is not None)
        self.use_model_status.style().unpolish(self.use_model_status)
        self.use_model_status.style().polish(self.use_model_status)
        self.use_model_status.setText(
            f"{model_text} • sign forms reviewed: {reviewed}/{len(pack.sign_ids)}"
        )
        self.capture_use_button.setEnabled(self.camera_ok and bundle is not None)
        self._hide_candidates()

    def _refresh_training_tab(self) -> None:
        language = self._combo_language(self.train_language)
        pack = self.vocabulary.pack(language)
        current_label = self.train_sign.currentData()
        self.train_sign.blockSignals(True)
        self.train_sign.clear()
        for sign in pack.signs:
            self.train_sign.addItem(f"{sign.output} ({sign.gloss})", sign.id)
        self.train_sign.addItem("OTHER / NO SIGN", UNKNOWN_LABEL)
        if current_label:
            index = self.train_sign.findData(current_label)
            if index >= 0:
                self.train_sign.setCurrentIndex(index)
        self.train_sign.blockSignals(False)
        self._refresh_training_status()

    def _refresh_training_status(self) -> None:
        language = self._combo_language(self.train_language)
        pack = self.vocabulary.pack(language)
        counts = self.dataset.counts(language)
        labels = list(pack.sign_ids) + [UNKNOWN_LABEL]
        self.training_table.setRowCount(len(labels))
        for row, label in enumerate(labels):
            if label == UNKNOWN_LABEL:
                display = "OTHER / NO SIGN"
                review = "Not applicable"
            else:
                sign = pack.sign_for_id(label)
                display = f"{sign.output} · {sign.gloss}"
                review = "Reviewed" if self.validation.is_reviewed(language, label) else "Needed"
            count = counts.get(label, 0)
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            review_item = QTableWidgetItem(review)
            review_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if review == "Reviewed":
                review_item.setForeground(QColor("#7bd9c3"))
            elif review == "Needed":
                review_item.setForeground(QColor("#efc866"))
            self.training_table.setItem(row, 0, QTableWidgetItem(display))
            self.training_table.setItem(row, 1, count_item)
            self.training_table.setItem(row, 2, review_item)

        minimum_ready = all(counts.get(label, 0) >= MIN_SAMPLES_PER_CLASS for label in labels)
        people = len(self.dataset.people(language))
        reviewed = self.validation.reviewed_count(language, pack.sign_ids)
        bundle = self.model_cache.get(language)
        selected_label = str(self.train_sign.currentData())
        if selected_label == UNKNOWN_LABEL:
            reference_text = "Language reference"
            reference_url = pack.reference_url
        else:
            selected_sign = pack.sign_for_id(selected_label)
            reference_text = f"Exact source for {selected_sign.output}"
            reference_url = selected_sign.reference_url or pack.reference_url
        self.reference_link.setText(
            f'Reference: <a style="color:#66d7c7" href="{reference_url}">{reference_text}</a>'
        )
        parts = [
            f"People recorded: {people}",
            f"forms reviewed: {reviewed}/{len(pack.sign_ids)}",
            "minimum samples reached" if minimum_ready else "more samples needed",
        ]
        if people == 1:
            parts.append("personalized data only")
        if bundle:
            metrics = bundle.get("metrics", {})
            if metrics.get("validated_on_unseen_people"):
                parts.append(
                    f"unseen-person score {metrics.get('balanced_accuracy', 0.0) * 100:.1f}%"
                )
            else:
                parts.append("unseen-person test pending")
        self.training_status.setText(" • ".join(parts))

    def _refresh_evaluation_tab(self) -> None:
        language = self._combo_language(self.eval_language)
        pack = self.vocabulary.pack(language)
        current_label = self.eval_expected_sign.currentData()
        self.eval_expected_sign.blockSignals(True)
        self.eval_expected_sign.clear()
        for sign in pack.signs:
            self.eval_expected_sign.addItem(f"{sign.output} ({sign.gloss})", sign.id)
        self.eval_expected_sign.addItem("OTHER / NO SIGN", UNKNOWN_LABEL)
        if current_label:
            index = self.eval_expected_sign.findData(current_label)
            if index >= 0:
                self.eval_expected_sign.setCurrentIndex(index)
        self.eval_expected_sign.blockSignals(False)

        labels = list(pack.sign_ids) + [UNKNOWN_LABEL]
        self.evaluation_table.setRowCount(len(labels))
        bundle = self.model_cache.get(language)
        if bundle is None:
            self.record_evaluation_button.setEnabled(False)
            self.evaluation_summary.setText(
                "Train this language first. Final testing will then start with an empty report."
            )
            for row, label in enumerate(labels):
                display = (
                    "OTHER / NO SIGN"
                    if label == UNKNOWN_LABEL
                    else pack.sign_for_id(label).output
                )
                self.evaluation_table.setItem(row, 0, QTableWidgetItem(display))
                self.evaluation_table.setItem(row, 1, QTableWidgetItem("0"))
                self.evaluation_table.setItem(row, 2, QTableWidgetItem("—"))
            return

        model_created_at = str(bundle.get("created_at", "unknown-model"))
        summary = self.evaluation.summary(language, pack.sign_ids, model_created_at)
        for row, label in enumerate(labels):
            if label == UNKNOWN_LABEL:
                display = "OTHER / NO SIGN"
                attempts = int(summary["unknown_attempts"])
                score = summary["unknown_rejection"]
            else:
                display = pack.sign_for_id(label).output
                attempts = int(summary["label_attempts"].get(label, 0))
                score = summary["per_sign_recall"].get(label)
            score_text = "—" if score is None else f"{float(score) * 100:.0f}%"
            attempts_item = QTableWidgetItem(str(attempts))
            attempts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item = QTableWidgetItem(score_text)
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.evaluation_table.setItem(row, 0, QTableWidgetItem(display))
            self.evaluation_table.setItem(row, 1, attempts_item)
            self.evaluation_table.setItem(row, 2, score_item)

        def percent(value: Any) -> str:
            return "pending" if value is None else f"{float(value) * 100:.1f}%"

        average_ms = summary["average_processing_ms"]
        latency_text = (
            "pending" if average_ms is None else f"{float(average_ms):.0f} ms"
        )

        self.evaluation_summary.setText(
            " • ".join(
                (
                    f"Current-model attempts: {summary['attempts']}",
                    f"untouched people: {summary['people']}",
                    f"balanced accuracy: {percent(summary['balanced_accuracy'])}",
                    f"accepted precision: {percent(summary['accepted_precision'])}",
                    f"unknown rejection: {percent(summary['unknown_rejection'])}",
                    f"average model processing: {latency_text}",
                )
            )
        )
        self.record_evaluation_button.setEnabled(self.camera_ok)

    @staticmethod
    def _gesture_name_for_people(name: str | None) -> str:
        return {
            "Open_Palm": "Open palm",
            "Closed_Fist": "Closed fist",
            "Pointing_Up": "Pointing up",
            "Thumb_Up": "Thumb up",
            "Thumb_Down": "Thumb down",
            "Victory": "Victory",
            "ILoveYou": "I love you gesture",
        }.get(name or "", "No clear gesture")

    def _refresh_control_mode_help(self) -> None:
        if str(self.control_mode.currentData()) == "mouse":
            text = (
                "Move: guide the pointer with your index fingertip. "
                "Click: touch your thumb and index fingertip together."
            )
        else:
            text = (
                "Thumb up/down: volume. Victory: next slide. "
                "Pointing up: previous slide."
            )
        self.control_mode_help.setText(text)

    def _refresh_control_ui(self) -> None:
        available = self.computer_controller.is_supported and self.camera_ok
        self.control_enable_button.setEnabled(available)
        if self.control_enabled:
            self.control_enable_button.setText("Stop computer control")
            self.control_enable_button.setObjectName("danger")
        else:
            self.control_enable_button.setText("Turn computer control on")
            self.control_enable_button.setObjectName("primary")
        self.control_enable_button.style().unpolish(self.control_enable_button)
        self.control_enable_button.style().polish(self.control_enable_button)

        if not self.computer_controller.is_supported:
            status = "Unavailable — this control version currently supports Windows only."
        elif not self.camera_ok:
            status = "OFF — start the camera before enabling computer control."
        elif not self.control_enabled:
            status = "OFF — gestures can be seen, but they cannot control the computer."
        elif self.control_armed:
            status = "ARMED — move carefully. Leave this tab or press Stop to disable it."
        else:
            status = "ON but locked — hold an open palm for 1.5 seconds to arm it."
        self.control_arm_status.setText(status)
        self.control_arm_status.setProperty("ready", self.control_armed)
        self.control_arm_status.style().unpolish(self.control_arm_status)
        self.control_arm_status.style().polish(self.control_arm_status)

    def _toggle_computer_control(self) -> None:
        if self.control_enabled:
            self._disable_computer_control("Stopped by you.")
            return
        if not self.camera_ok or not self.computer_controller.is_supported:
            return
        self.control_enabled = True
        self.control_armed = False
        self.control_palm_started = None
        self.control_votes.clear()
        self.control_previous_gesture = None
        self.control_cursor_position = None
        self.control_pinching = False
        self._refresh_control_ui()

    def _disable_computer_control(self, reason: str) -> None:
        was_enabled = self.control_enabled
        self.control_enabled = False
        self.control_armed = False
        self.control_palm_started = None
        self.control_armed_until = 0.0
        self.control_votes.clear()
        self.control_previous_gesture = None
        self.control_cursor_position = None
        self.control_pinching = False
        self._refresh_control_ui()
        if was_enabled and reason:
            self.control_arm_status.setText(f"OFF — {reason}")

    def _on_tab_changed(self, index: int) -> None:
        if index != 3 and self.control_enabled:
            self._disable_computer_control("Leaving the Computer control tab stopped it.")

    def _on_control_mode_changed(self) -> None:
        self._refresh_control_mode_help()
        self.control_votes.clear()
        self.control_cursor_position = None
        self.control_pinching = False
        if self.control_enabled:
            self.control_armed = False
            self.control_palm_started = None
            self._refresh_control_ui()

    def _stable_control_gesture(self, name: str, score: float) -> str | None:
        vote = name if score >= 0.65 and name != "None" else None
        self.control_votes.append(vote)
        if len(self.control_votes) < 5:
            return None
        gesture, count = Counter(self.control_votes).most_common(1)[0]
        return gesture if gesture is not None and count >= 5 else None

    def _on_control_gesture(self, payload: dict[str, Any]) -> None:
        now = float(payload.get("timestamp", time.monotonic()))
        name = str(payload.get("name", "None"))
        score = float(payload.get("score", 0.0))
        hands = tuple(payload.get("hands") or ())
        stable = self._stable_control_gesture(name, score)

        readable = self._gesture_name_for_people(name if score >= 0.35 else None)
        steady = " • steady" if stable == name else ""
        self.control_detected.setText(f"{readable}{steady}")
        self.control_confidence.setValue(int(max(0.0, min(1.0, score)) * 100))

        if not self.control_enabled:
            return
        if self.control_armed and now > self.control_armed_until:
            self.control_armed = False
            self.control_palm_started = None
            self.control_previous_gesture = None
            self._refresh_control_ui()

        if not self.control_armed:
            if stable == "Open_Palm":
                if self.control_palm_started is None:
                    self.control_palm_started = now
                held_for = now - self.control_palm_started
                if held_for >= 1.5:
                    self.control_armed = True
                    self.control_armed_until = now + 10.0
                    self.control_palm_started = None
                    self.control_votes.clear()
                    self.control_previous_gesture = None
                    self._record_control_action("Control armed")
                    self._refresh_control_ui()
                else:
                    remaining = max(0.1, 1.5 - held_for)
                    self.control_arm_status.setText(
                        f"Keep holding the open palm — {remaining:.1f} seconds"
                    )
            else:
                self.control_palm_started = None
                self.control_arm_status.setText(
                    "ON but locked — hold an open palm for 1.5 seconds to arm it."
                )
            return

        if hands:
            self.control_armed_until = now + 10.0
        mode = str(self.control_mode.currentData())
        if mode == "mouse":
            self._run_mouse_control(payload, now)
        else:
            self._run_media_control(stable, now)

    def _run_media_control(self, gesture: str | None, now: float) -> None:
        if gesture is None or gesture == "Open_Palm":
            self.control_previous_gesture = gesture
            return
        actions = {
            "Thumb_Up": ("Volume up", self.computer_controller.volume_up, 0.45),
            "Thumb_Down": (
                "Volume down",
                self.computer_controller.volume_down,
                0.45,
            ),
            "Victory": ("Next slide", self.computer_controller.next_slide, 1.0),
            "Pointing_Up": (
                "Previous slide",
                self.computer_controller.previous_slide,
                1.0,
            ),
        }
        action = actions.get(gesture)
        if action is None:
            self.control_previous_gesture = gesture
            return
        label, callback, cooldown = action
        is_slide_action = gesture in {"Victory", "Pointing_Up"}
        if is_slide_action and self.control_previous_gesture == gesture:
            return
        if now - self.control_last_actions.get(gesture, 0.0) < cooldown:
            return
        self.control_previous_gesture = gesture
        if callback():
            self.control_last_actions[gesture] = now
            self._record_control_action(label)

    @staticmethod
    def _distance(point_a: Any, point_b: Any) -> float:
        return math.hypot(
            float(point_a[0]) - float(point_b[0]),
            float(point_a[1]) - float(point_b[1]),
        )

    def _run_mouse_control(self, payload: dict[str, Any], now: float) -> None:
        hands = tuple(payload.get("hands") or ())
        if not hands:
            self.control_pinching = False
            return
        hand_index = min(max(0, int(payload.get("hand_index", 0))), len(hands) - 1)
        points = hands[hand_index]
        if len(points) < 21:
            return

        margin = 0.12
        raw_x = 1.0 - float(points[8][0])
        raw_y = float(points[8][1])
        target_x = max(0.0, min(1.0, (raw_x - margin) / (1.0 - 2 * margin)))
        target_y = max(0.0, min(1.0, (raw_y - margin) / (1.0 - 2 * margin)))
        if self.control_cursor_position is None:
            smooth_x, smooth_y = target_x, target_y
        else:
            previous_x, previous_y = self.control_cursor_position
            smooth_x = previous_x + 0.32 * (target_x - previous_x)
            smooth_y = previous_y + 0.32 * (target_y - previous_y)
        self.control_cursor_position = (smooth_x, smooth_y)
        self.computer_controller.move_pointer(smooth_x, smooth_y)

        palm_size = self._distance(points[0], points[9])
        pinch_size = self._distance(points[4], points[8])
        pinching = palm_size > 0.01 and pinch_size / palm_size < 0.32
        if pinching and not self.control_pinching and now - self.control_last_click >= 0.6:
            if self.computer_controller.click():
                self.control_last_click = now
                self._record_control_action("Mouse click")
        self.control_pinching = pinching

    def _record_control_action(self, label: str) -> None:
        self.control_history.insertItem(0, label)
        while self.control_history.count() > 6:
            self.control_history.takeItem(self.control_history.count() - 1)

    def _on_frame(self, frame: Any) -> None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        image = QImage(rgb.data, width, height, channels * width, QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(image).scaled(
            self.camera_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.camera_preview.setPixmap(pixmap)

    def _start_selected_camera(self) -> None:
        camera_index = int(self.camera_selector.currentData())
        if self.control_enabled:
            self._disable_computer_control("Restarting the camera stopped it.")
        self.camera_ok = False
        self.system_status.setText(f"Starting camera {camera_index}…")
        self.system_status.setToolTip("")
        self.camera_performance_label.setText(
            f"Connecting to camera {camera_index}. The first picture may take a moment."
        )
        self.camera_preview.clear()
        self.camera_preview.setText("Starting camera…")
        self.restart_camera_button.setEnabled(False)
        self._set_capture_buttons(False)
        if not self.camera_worker.start_camera(camera_index):
            self.restart_camera_button.setEnabled(True)
            self.system_status.setText("Camera is still stopping")
            self.camera_performance_label.setText(
                "Wait a moment, then press Restart again."
            )

    def _restart_camera(self) -> None:
        if self.control_enabled:
            self._disable_computer_control("Restarting the camera stopped it.")
        self.camera_ok = False
        self.restart_camera_button.setEnabled(False)
        self.system_status.setText("Restarting camera…")
        self.camera_performance_label.setText("Closing the old camera connection…")
        self._set_capture_buttons(False)
        if self.camera_worker.isRunning() and not self.camera_worker.stop():
            self.restart_camera_button.setEnabled(True)
            self.system_status.setText("Camera did not stop")
            self.camera_performance_label.setText(
                "Close other camera apps, wait a moment and press Restart again."
            )
            return
        self._start_selected_camera()

    def _on_camera_performance(self, message: str) -> None:
        self.camera_performance_label.setText(message)
        self.system_status.setToolTip(message)
        parts = [part.strip() for part in message.split("•")]
        self.system_status.setText(" • ".join(parts[:2]))

    def _on_camera_status(self, message: str, ok: bool) -> None:
        self.camera_ok = ok
        summary = message.split("•", 1)[0].split(".", 1)[0].strip()
        if not ok and ":" in summary:
            summary = summary.split(":", 1)[0]
        self.system_status.setText(summary)
        self.system_status.setToolTip(message)
        self.camera_performance_label.setText(message)
        self.capture_state_label.setText("Ready to record" if ok else "Camera unavailable")
        self.restart_camera_button.setEnabled(True)
        if not ok:
            self.camera_preview.clear()
            self.camera_preview.setText(message)
        self.capture_use_button.setEnabled(
            ok
            and self.model_cache.get(self._combo_language(self.use_language))
            is not None
        )
        self.record_training_button.setEnabled(ok)
        self.record_evaluation_button.setEnabled(
            ok
            and self.model_cache.get(self._combo_language(self.eval_language))
            is not None
        )
        if not ok and self.control_enabled:
            self._disable_computer_control("The camera stopped.")
        else:
            self._refresh_control_ui()

    def _on_capture_state(self, message: str, progress: int) -> None:
        self.capture_state_label.setText(message)
        self.capture_progress.setValue(progress)

    def _set_capture_buttons(self, enabled: bool) -> None:
        use_has_model = self.model_cache.get(self._combo_language(self.use_language)) is not None
        evaluation_has_model = (
            self.model_cache.get(self._combo_language(self.eval_language)) is not None
        )
        self.capture_use_button.setEnabled(enabled and self.camera_ok and use_has_model)
        self.record_training_button.setEnabled(enabled and self.camera_ok)
        self.record_evaluation_button.setEnabled(
            enabled and self.camera_ok and evaluation_has_model
        )

    def _capture_for_use(self) -> None:
        language = self._combo_language(self.use_language)
        if self.model_cache.get(language) is None:
            QMessageBox.information(
                self,
                "Training needed",
                "This language has no trained model yet. Open Train model first.",
            )
            self.tabs.setCurrentIndex(1)
            return
        if self.camera_worker.request_capture({"purpose": "predict", "language": language}):
            self._set_capture_buttons(False)
            self._hide_candidates()
            self.result_label.setText("Get ready")

    def _capture_training_sample(self) -> None:
        person = self.person_id.text().strip()
        if not person:
            QMessageBox.warning(self, "Person ID needed", "Enter a short ID for this person.")
            self.person_id.setFocus()
            return
        language = self._combo_language(self.train_language)
        try:
            normalized_person = DatasetStore.safe_component(person)
        except ValueError as exc:
            QMessageBox.warning(self, "Person ID needed", str(exc))
            return
        final_test_people = {
            item.casefold() for item in self.evaluation.people(language)
        }
        if normalized_person.casefold() in final_test_people:
            QMessageBox.warning(
                self,
                "Keep final testing separate",
                "This person has already been used for final testing and cannot be added to training.",
            )
            return
        context = {
            "purpose": "train",
            "language": language,
            "label": str(self.train_sign.currentData()),
            "person_id": normalized_person,
        }
        if self.camera_worker.request_capture(context):
            self._set_capture_buttons(False)

    def _capture_evaluation_sample(self) -> None:
        language = self._combo_language(self.eval_language)
        if self.model_cache.get(language) is None:
            QMessageBox.information(
                self,
                "Training needed",
                "Train this language before starting the final test.",
            )
            return
        person = self.eval_person_id.text().strip()
        if not person:
            QMessageBox.warning(
                self, "Tester ID needed", "Enter a short ID for this final-test person."
            )
            self.eval_person_id.setFocus()
            return
        try:
            normalized_person = DatasetStore.safe_component(person)
        except ValueError as exc:
            QMessageBox.warning(self, "Tester ID needed", str(exc))
            return
        training_people = {
            item.casefold() for item in self.dataset.people(language)
        }
        if normalized_person.casefold() in training_people:
            QMessageBox.warning(
                self,
                "This is not an untouched tester",
                "This person already has training data. Use somebody who was never recorded for training.",
            )
            return
        context = {
            "purpose": "evaluate",
            "language": language,
            "label": str(self.eval_expected_sign.currentData()),
            "person_id": normalized_person,
            "condition": self.eval_condition.currentText(),
        }
        if self.camera_worker.request_capture(context):
            self._set_capture_buttons(False)
            self.evaluation_result.setText("Get ready and perform the expected sign once")

    def _on_sequence_ready(self, sequence: Any, context: dict, quality: dict) -> None:
        self._set_capture_buttons(True)
        ratio = float(quality.get("hand_presence_ratio", 0.0))
        purpose = context.get("purpose")

        # Final testing must include every attempt. Discarding a difficult capture
        # would make the reported accuracy look better than the real system.
        if purpose == "evaluate":
            self._record_evaluation_result(sequence, context, ratio)
            self.capture_progress.setValue(0)
            return

        if ratio < MIN_HAND_PRESENCE_RATIO:
            QMessageBox.warning(
                self,
                "Hands were not clear",
                "The camera could not see a hand for enough of the recording. Keep your hands inside the frame and try again.",
            )
            self.capture_state_label.setText("Try again with hands visible")
            self.capture_progress.setValue(0)
            return

        if purpose == "train":
            self.dataset.save_sample(
                language=context["language"],
                label=context["label"],
                person_id=context["person_id"],
                sequence=sequence,
                quality=quality,
            )
            self.capture_state_label.setText("Training sample saved")
            self.capture_progress.setValue(0)
            self._refresh_training_status()
            return

        language = context["language"]
        bundle = self.model_cache.get(language)
        if bundle is None:
            return
        prediction = predict_sequence(bundle, sequence)
        self._show_prediction(language, prediction)
        self.capture_progress.setValue(0)

    def _record_evaluation_result(
        self, sequence: Any, context: dict, hand_presence_ratio: float
    ) -> None:
        language = str(context["language"])
        bundle = self.model_cache.get(language)
        if bundle is None:
            self.evaluation_result.setText("The model is unavailable. This attempt was not saved.")
            return

        started = time.perf_counter()
        prediction = predict_sequence(bundle, sequence)
        processing_ms = (time.perf_counter() - started) * 1000
        expected = str(context["label"])
        model_created_at = str(bundle.get("created_at", "unknown-model"))
        self.evaluation.save_attempt(
            language=language,
            expected_label=expected,
            person_id=str(context["person_id"]),
            predicted_label=prediction.label,
            accepted=prediction.accepted,
            confidence=prediction.confidence,
            margin=prediction.margin,
            model_created_at=model_created_at,
            condition=str(context.get("condition", "Normal indoor")),
            processing_ms=processing_ms,
        )

        pack = self.vocabulary.pack(language)
        expected_text = (
            "OTHER / NO SIGN"
            if expected == UNKNOWN_LABEL
            else pack.sign_for_id(expected).output
        )
        if prediction.accepted:
            predicted_text = pack.sign_for_id(prediction.label).output
            model_result = (
                f"model accepted {predicted_text} ({prediction.confidence * 100:.0f}%)"
            )
        else:
            model_result = f"model rejected it ({prediction.confidence * 100:.0f}% best match)"
        correct = (
            expected == UNKNOWN_LABEL
            and not prediction.accepted
        ) or (
            expected != UNKNOWN_LABEL
            and prediction.accepted
            and prediction.label == expected
        )
        visibility_note = (
            " Hands were not visible for most of the attempt; it still counts."
            if hand_presence_ratio < MIN_HAND_PRESENCE_RATIO
            else ""
        )
        outcome = "Correct" if correct else "Incorrect"
        self.evaluation_result.setText(
            f"{outcome} — expected {expected_text}; {model_result}.{visibility_note}"
        )
        self.evaluation.write_report(language, pack.sign_ids, model_created_at)
        self._refresh_evaluation_tab()

    def _show_prediction(self, language: str, prediction: Any) -> None:
        pack = self.vocabulary.pack(language)
        self.confidence_bar.setValue(int(prediction.confidence * 100))
        if prediction.accepted:
            self._commit_sign(
                language, prediction.label, prediction.confidence, confirmed=False
            )
            return

        self.result_label.setText("Not sure")
        self.last_spoken = None
        self.confidence_label.setText(
            f"Best match: {prediction.confidence * 100:.0f}% • nothing was added or spoken"
        )
        self._render_history()
        real_options = [item for item in prediction.alternatives if item[0] != UNKNOWN_LABEL][:2]
        self.candidate_prompt.show()
        for button, option in zip(self.candidate_buttons, real_options):
            label, score = option
            sign = pack.sign_for_id(label)
            button.setText(f"{sign.output}  ({score * 100:.0f}%)")
            button.setProperty("candidate_language", language)
            button.setProperty("candidate_label", label)
            button.setProperty("candidate_confidence", score)
            button.show()
        for button in self.candidate_buttons[len(real_options):]:
            button.hide()

    def _hide_candidates(self) -> None:
        self.candidate_prompt.hide()
        for button in self.candidate_buttons:
            button.hide()

    def _commit_candidate(self) -> None:
        button = self.sender()
        if not isinstance(button, QPushButton):
            return
        language = button.property("candidate_language")
        label = button.property("candidate_label")
        confidence = button.property("candidate_confidence")
        if language and label and confidence is not None:
            self._commit_sign(
                str(language), str(label), float(confidence), confirmed=True
            )

    def _commit_sign(
        self, language: str, label: str, confidence: float, *, confirmed: bool
    ) -> None:
        pack = self.vocabulary.pack(language)
        sign = pack.sign_for_id(label)
        self.result_label.setText(sign.output)
        self.result_label.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if pack.direction == "rtl"
            else Qt.LayoutDirection.LeftToRight
        )
        self.confidence_label.setText(f"Confidence: {confidence * 100:.0f}%")
        self.confidence_bar.setValue(int(confidence * 100))
        self.history_entries.append(
            {"language": language, "label": label, "text": sign.output, "locale": pack.locale}
        )
        self.last_spoken = (sign.output, pack.locale)
        self._render_history()
        if confirmed or self.auto_speak_checkbox.isChecked():
            self.speech.speak(sign.output, pack.locale)
        else:
            self.voice_status.setText("Text ready — press Speak result after checking it")
        self._hide_candidates()

    def _speak_current_result(self) -> None:
        if self.last_spoken is not None:
            self.speech.speak(*self.last_spoken)

    def _render_history(self) -> None:
        self.history_list.clear()
        for entry in self.history_entries:
            pack = self.vocabulary.pack(entry["language"])
            item = QListWidgetItem(f"{pack.short_name}: {entry['text']}")
            if pack.direction == "rtl":
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.history_list.addItem(item)
        self.history_list.scrollToBottom()
        has_history = bool(self.history_entries)
        self.undo_button.setEnabled(has_history)
        self.clear_button.setEnabled(has_history)
        self.replay_button.setEnabled(self.last_spoken is not None)

    def _undo_history(self) -> None:
        if self.history_entries:
            self.history_entries.pop()
        if self.history_entries:
            last = self.history_entries[-1]
            self.last_spoken = (last["text"], last["locale"])
        else:
            self.last_spoken = None
        self._render_history()

    def _clear_history(self) -> None:
        self.history_entries.clear()
        self.last_spoken = None
        self.result_label.setText("—")
        self.confidence_label.setText("No prediction yet")
        self.confidence_bar.setValue(0)
        self._hide_candidates()
        self._render_history()

    def _remove_last_sample(self) -> None:
        language = self._combo_language(self.train_language)
        label = str(self.train_sign.currentData())
        answer = QMessageBox.question(
            self,
            "Remove last sample?",
            "The latest sample for this sign will be moved to the recoverable trash folder.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        destination = self.dataset.move_last_to_trash(language, label)
        if destination is None:
            QMessageBox.information(self, "Nothing to remove", "No sample exists for this sign.")
        self._refresh_training_status()

    def _mark_sign_reviewed(self) -> None:
        language = self._combo_language(self.train_language)
        label = str(self.train_sign.currentData())
        if label == UNKNOWN_LABEL:
            QMessageBox.information(self, "No review needed", "OTHER / NO SIGN is not a language sign.")
            return
        validator = self.validator_name.text().strip()
        if not validator:
            QMessageBox.warning(
                self,
                "Validator name needed",
                "Enter the fluent signer or qualified interpreter who checked this exact sign form.",
            )
            return
        answer = QMessageBox.question(
            self,
            "Confirm language review",
            "Only confirm if a fluent signer or qualified interpreter checked the exact movement you will record. Continue?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.validation.mark_reviewed(language, label, validator)
        self._refresh_all()

    def _train_model(self) -> None:
        if self.training_worker and self.training_worker.isRunning():
            return
        language = self._combo_language(self.train_language)
        pack = self.vocabulary.pack(language)
        counts = self.dataset.counts(language)
        labels = list(pack.sign_ids) + [UNKNOWN_LABEL]
        missing = [label for label in labels if counts.get(label, 0) < MIN_SAMPLES_PER_CLASS]
        if missing:
            QMessageBox.warning(
                self,
                "More examples needed",
                f"Record at least {MIN_SAMPLES_PER_CLASS} examples for every sign and for OTHER / NO SIGN.",
            )
            return
        people = len(self.dataset.people(language))
        reviewed = self.validation.reviewed_count(language, pack.sign_ids)
        early_reasons = []
        if any(
            counts.get(label, 0) < PERSONAL_DEMO_SAMPLES_PER_CLASS
            for label in labels
        ):
            early_reasons.append(
                f"fewer than {PERSONAL_DEMO_SAMPLES_PER_CLASS} examples for some classes"
            )
        if people < 5:
            early_reasons.append(
                "only one training person" if people == 1 else "fewer than 5 training people"
            )
        if reviewed < len(pack.sign_ids):
            early_reasons.append("some sign forms are not reviewed by a fluent signer")
        if early_reasons:
            answer = QMessageBox.question(
                self,
                "Train an early model?",
                "This can still be a personalized demonstration, but it is not validated "
                "for new people because it has "
                + ", ".join(early_reasons)
                + ". Train it anyway?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.train_model_button.setEnabled(False)
        self.training_status.setText("Training model…")
        self.training_worker = TrainingWorker(language, pack, self.dataset)
        self.training_worker.complete.connect(partial(self._training_complete, language))
        self.training_worker.failed.connect(self._training_failed)
        self.training_worker.start()

    def _training_complete(self, language: str, bundle: dict) -> None:
        self.model_cache[language] = bundle
        self.train_model_button.setEnabled(True)
        self._refresh_all()
        metrics = bundle.get("metrics", {})
        if metrics.get("validated_on_unseen_people"):
            score = metrics.get("balanced_accuracy", 0.0) * 100
            message = f"Model trained. Unseen-person balanced accuracy: {score:.1f}%."
        else:
            message = "Model trained, but it is not validated on unseen people yet."
        QMessageBox.information(self, "Training complete", message)

    def _training_failed(self, message: str) -> None:
        self.train_model_button.setEnabled(True)
        self.training_status.setText("Training failed")
        QMessageBox.critical(self, "Training failed", message)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._disable_computer_control("")
        self.speech.stop()
        self.camera_worker.stop()
        if self.training_worker and self.training_worker.isRunning():
            self.training_worker.wait(3000)
        event.accept()
