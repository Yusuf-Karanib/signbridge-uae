from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Callable

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

from signbridge.config import HOLISTIC_MODEL_PATH
from signbridge.landmarks import extract_frame_features, resample_sequence


ALLOWED_VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}
MAX_VIDEO_BYTES = 250 * 1024 * 1024
MAX_VIDEO_SECONDS = 12.0
TARGET_PROCESSING_FPS = 15.0
MIN_PROCESSED_FRAMES = 6


@dataclass(frozen=True)
class ImportedVideo:
    sequence: np.ndarray
    quality: dict


def validate_video_path(path: Path) -> Path:
    path = Path(path)
    if not path.is_file():
        raise ValueError("The selected video cannot be found.")
    if path.suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError("Choose an MP4, MOV, AVI, MKV, M4V or WebM video.")
    if path.stat().st_size > MAX_VIDEO_BYTES:
        raise ValueError("The video is larger than 250 MB. Trim it to one short sign.")
    return path


def _detector_options(model_path: Path) -> vision.HolisticLandmarkerOptions:
    return vision.HolisticLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        min_face_detection_confidence=0.45,
        min_face_landmarks_confidence=0.45,
        min_pose_detection_confidence=0.45,
        min_pose_landmarks_confidence=0.45,
        min_hand_landmarks_confidence=0.45,
        output_face_blendshapes=False,
        output_segmentation_mask=False,
    )


def extract_training_video(
    path: Path,
    *,
    model_path: Path = HOLISTIC_MODEL_PATH,
    result_provider: Callable[[np.ndarray, int], object] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> ImportedVideo:
    """Turn one short, pre-recorded sign into the same features as live capture.

    The caller stores only the returned landmark sequence and quality numbers.
    The original video is never copied into SignBridge.
    """
    path = validate_video_path(path)
    with path.open("rb") as source:
        video_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    if result_provider is None and not Path(model_path).is_file():
        raise ValueError("The MediaPipe model is missing. Run setup.ps1 again.")

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError("The video could not be opened. Try exporting it as MP4.")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    if not np.isfinite(fps) or fps <= 0.0:
        fps = 30.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    estimated_seconds = frame_count / fps if frame_count > 0 else 0.0
    if estimated_seconds > MAX_VIDEO_SECONDS + 0.25:
        capture.release()
        raise ValueError("The video is longer than 12 seconds. Trim it to exactly one sign.")

    sample_every = max(1, int(round(fps / TARGET_PROCESSING_FPS)))
    features: list[np.ndarray] = []
    hand_frames = 0
    decoded_frames = 0
    last_timestamp = -1

    detector = None
    try:
        if result_provider is None:
            detector = vision.HolisticLandmarker.create_from_options(
                _detector_options(Path(model_path))
            )

        while True:
            if should_stop is not None and should_stop():
                raise InterruptedError("Video import cancelled")
            ok, frame = capture.read()
            if not ok:
                break
            frame_index = decoded_frames
            decoded_frames += 1
            seconds = frame_index / fps
            if seconds > MAX_VIDEO_SECONDS:
                raise ValueError(
                    "The video is longer than 12 seconds. Trim it to exactly one sign."
                )
            if frame_index % sample_every:
                continue

            timestamp_ms = max(last_timestamp + 1, int(round(seconds * 1000.0)))
            last_timestamp = timestamp_ms
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if result_provider is not None:
                result = result_provider(rgb, timestamp_ms)
            else:
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                result = detector.detect_for_video(image, timestamp_ms)
            feature, hand_present = extract_frame_features(result)
            features.append(feature)
            hand_frames += int(hand_present)
    finally:
        capture.release()
        if detector is not None:
            detector.close()

    if len(features) < MIN_PROCESSED_FRAMES:
        raise ValueError(
            "Too few usable video frames were found. Use a clear clip lasting about 2–5 seconds."
        )

    ratio = hand_frames / len(features)
    return ImportedVideo(
        sequence=resample_sequence(features),
        quality={
            "source": "imported_video",
            "video_sha256": video_sha256,
            "processed_frames": len(features),
            "hand_frames": hand_frames,
            "hand_presence_ratio": ratio,
            "video_seconds": decoded_frames / fps,
            "raw_video_stored": False,
        },
    )
