from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
MODEL_ASSETS_DIR = ASSETS_DIR / "models"
HOLISTIC_MODEL_PATH = MODEL_ASSETS_DIR / "holistic_landmarker.task"
GESTURE_MODEL_PATH = MODEL_ASSETS_DIR / "gesture_recognizer.task"
VOCABULARY_PATH = PROJECT_ROOT / "config" / "vocabulary.json"

DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
TRASH_DIR = DATA_DIR / "trash"
VALIDATION_PATH = DATA_DIR / "validation.json"
EVALUATIONS_DIR = DATA_DIR / "evaluations"

TRAINED_MODELS_DIR = PROJECT_ROOT / "models"

SEQUENCE_LENGTH = 32
CAPTURE_SECONDS = 1.8
COUNTDOWN_SECONDS = 2.0
UNKNOWN_LABEL = "__unknown__"

MIN_SAMPLES_PER_CLASS = 5
PERSONAL_DEMO_SAMPLES_PER_CLASS = 20
RECOMMENDED_SAMPLES_PER_CLASS = 60
MIN_HAND_PRESENCE_RATIO = 0.45

DEFAULT_CONFIDENCE_THRESHOLD = 0.82
DEFAULT_MARGIN_THRESHOLD = 0.12


def ensure_project_directories() -> None:
    for path in (
        MODEL_ASSETS_DIR,
        SAMPLES_DIR,
        TRASH_DIR,
        EVALUATIONS_DIR,
        TRAINED_MODELS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)

