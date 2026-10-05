from __future__ import annotations

import math
import sys
import threading
import time
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.components.processors.classifier_options import (
    ClassifierOptions,
)
from mediapipe.tasks.python.core.base_options import BaseOptions
from PySide6.QtCore import QThread, Signal

from signbridge.config import (
    CAPTURE_SECONDS,
    COUNTDOWN_SECONDS,
    GESTURE_MODEL_PATH,
    HOLISTIC_MODEL_PATH,
)
from signbridge.landmarks import (
    draw_hand_points_overlay,
    extract_frame_features,
    gesture_result_to_hand_points,
    resample_sequence,
)


def smooth_hand_tracks(
    current_hands: tuple[np.ndarray, ...],
    previous_hands: tuple[np.ndarray, ...],
) -> tuple[np.ndarray, ...]:
    """Reduce small landmark jitter while still following deliberate movement."""
    if not current_hands or len(current_hands) != len(previous_hands):
        return tuple(np.asarray(hand, dtype=np.float32).copy() for hand in current_hands)

    aligned_previous = previous_hands
    if len(current_hands) == 2:
        direct = sum(
            float(np.linalg.norm(current[0, :2] - previous[0, :2]))
            for current, previous in zip(current_hands, previous_hands)
        )
        swapped_previous = tuple(reversed(previous_hands))
        swapped = sum(
            float(np.linalg.norm(current[0, :2] - previous[0, :2]))
            for current, previous in zip(current_hands, swapped_previous)
        )
        if swapped < direct:
            aligned_previous = swapped_previous

    smoothed: list[np.ndarray] = []
    for current, previous in zip(current_hands, aligned_previous):
        current = np.asarray(current, dtype=np.float32)
        previous = np.asarray(previous, dtype=np.float32)
        wrist_jump = float(np.linalg.norm(current[0, :2] - previous[0, :2]))
        if wrist_jump > 0.20:
            smoothed.append(current.copy())
            continue
        movement = float(
            np.mean(np.linalg.norm(current[:, :2] - previous[:, :2], axis=1))
        )
        alpha = float(np.clip(0.18 + movement * 10.0, 0.18, 0.72))
        smoothed.append(previous + alpha * (current - previous))
    return tuple(smoothed)


def resize_for_tracking(frame: np.ndarray, maximum_width: int = 640) -> np.ndarray:
    """Keep the visible frame sharp while limiting MediaPipe processing cost."""
    height, width = frame.shape[:2]
    if width <= maximum_width:
        return frame
    scale = maximum_width / width
    target_height = max(1, int(round(height * scale)))
    return cv2.resize(
        frame, (maximum_width, target_height), interpolation=cv2.INTER_AREA
    )


def prepare_preview_frame(
    frame: np.ndarray,
    hands: tuple[np.ndarray, ...],
    minimum_width: int = 640,
) -> np.ndarray:
    """Enlarge very small camera frames before drawing a crisp hand overlay.

    This makes the preview less blocky, but it cannot create camera detail that
    was never captured.
    """
    height, width = frame.shape[:2]
    preview = frame
    if width < minimum_width:
        scale = minimum_width / max(1, width)
        target_height = max(1, int(round(height * scale)))
        preview = cv2.resize(
            frame,
            (minimum_width, target_height),
            interpolation=cv2.INTER_LANCZOS4,
        )
    return draw_hand_points_overlay(preview, hands)


def camera_resolution_warning(width: int, height: int) -> str | None:
    """Explain when Windows is supplying too little real camera detail."""
    if width >= 640 and height >= 360:
        return None
    return (
        f"LOW CAMERA QUALITY: Windows supplies only {width}×{height}. "
        "SignBridge smooths the preview, but software cannot restore missing detail. "
        "Update the official camera driver or use a USB webcam."
    )


def is_corrupted_camera_frame(frame: np.ndarray) -> bool:
    """Detect the strong rainbow-noise pattern produced by a broken webcam stream."""
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.size == 0:
        return True
    sample = frame
    if frame.shape[1] > 320:
        sample = resize_for_tracking(frame, maximum_width=320)
    pixels = sample.astype(np.int16)
    chroma = float(np.mean(np.max(pixels, axis=2) - np.min(pixels, axis=2)))
    horizontal_change = float(np.mean(np.abs(pixels[:, 1:] - pixels[:, :-1])))
    vertical_change = float(np.mean(np.abs(pixels[1:] - pixels[:-1])))
    return chroma > 75.0 and max(horizontal_change, vertical_change) > 35.0


def configure_camera(camera: cv2.VideoCapture) -> None:
    """Request useful defaults without forcing an unsupported pixel format."""
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_FPS, 30)


class CameraWorker(QThread):
    frame_ready = Signal(object)
    camera_status = Signal(str, bool)
    performance_status = Signal(str)
    gesture_ready = Signal(object)
    capture_state = Signal(str, int)
    sequence_ready = Signal(object, object, object)

    def __init__(self, camera_index: int = 0, parent: Any = None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._capture_request: dict | None = None
        self._last_countdown_value: int | None = None

    def request_capture(self, context: dict) -> bool:
        with self._state_lock:
            if self._capture_request is not None:
                return False
            now = time.monotonic()
            self._capture_request = {
                "context": dict(context),
                "countdown_end": now + COUNTDOWN_SECONDS,
                "capture_end": now + COUNTDOWN_SECONDS + CAPTURE_SECONDS,
                "frames": [],
                "hand_frames": 0,
                "started": False,
            }
            self._last_countdown_value = None
        return True

    def cancel_capture(self) -> None:
        with self._state_lock:
            self._capture_request = None
        self.capture_state.emit("Ready", 0)

    def _capture_is_pending(self) -> bool:
        with self._state_lock:
            return self._capture_request is not None

    def start_camera(self, camera_index: int | None = None) -> bool:
        """Start a fresh camera session after a previous stop or failure."""
        if self.isRunning():
            return False
        if camera_index is not None:
            self.camera_index = max(0, int(camera_index))
        with self._state_lock:
            self._capture_request = None
            self._last_countdown_value = None
        self._stop_event.clear()
        self.start()
        return True

    def stop(self) -> bool:
        self.cancel_capture()
        self._stop_event.set()
        return self.wait(5000)

    @staticmethod
    def _open_camera(index: int) -> tuple[cv2.VideoCapture, str]:
        if sys.platform.startswith("win"):
            camera = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if camera.isOpened():
                return camera, "DirectShow"
            camera.release()
            camera = cv2.VideoCapture(index, cv2.CAP_MSMF)
            if camera.isOpened():
                return camera, "Media Foundation"
            camera.release()
        return cv2.VideoCapture(index), "automatic backend"

    def _advance_capture(self, feature: np.ndarray, hand_present: bool) -> None:
        completed: tuple[np.ndarray, dict, dict] | None = None
        state_to_emit: tuple[str, int] | None = None
        with self._state_lock:
            request = self._capture_request
            if request is None:
                return
            now = time.monotonic()
            if now < request["countdown_end"]:
                seconds = max(1, math.ceil(request["countdown_end"] - now))
                if seconds != self._last_countdown_value:
                    self._last_countdown_value = seconds
                    state_to_emit = (f"Get ready: {seconds}", 0)
            elif now < request["capture_end"]:
                request["started"] = True
                request["frames"].append(feature)
                if hand_present:
                    request["hand_frames"] += 1
                elapsed = CAPTURE_SECONDS - (request["capture_end"] - now)
                progress = int(max(0.0, min(1.0, elapsed / CAPTURE_SECONDS)) * 100)
                state_to_emit = ("Signing…", progress)
            else:
                frames = request["frames"]
                context = request["context"]
                hand_frames = request["hand_frames"]
                self._capture_request = None
                self._last_countdown_value = None
                if frames:
                    sequence = resample_sequence(frames)
                    quality = {
                        "processed_frames": len(frames),
                        "hand_frames": hand_frames,
                        "hand_presence_ratio": hand_frames / len(frames),
                    }
                    completed = (sequence, context, quality)
                else:
                    state_to_emit = ("No frames captured. Try again.", 0)

        if state_to_emit:
            self.capture_state.emit(*state_to_emit)
        if completed:
            self.capture_state.emit("Capture complete", 100)
            self.sequence_ready.emit(*completed)

    def run(self) -> None:
        missing_models = [
            path.name
            for path in (HOLISTIC_MODEL_PATH, GESTURE_MODEL_PATH)
            if not path.exists()
        ]
        if missing_models:
            self.camera_status.emit(
                "MediaPipe model is missing. Run setup.ps1 again: "
                + ", ".join(missing_models),
                False,
            )
            return

        camera, backend_name = self._open_camera(self.camera_index)
        if not camera.isOpened():
            self.camera_status.emit(
                f"Camera {self.camera_index} unavailable. Try another camera number or close other camera apps.",
                False,
            )
            return
        # Request a detailed preview. Do not force a video encoding: this
        # laptop's camera exposes YUY2/RGB24 only, while other webcams may use
        # MJPEG. Forcing the wrong encoding can produce colored noise.
        configure_camera(camera)
        capture_width = max(1, int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)))
        capture_height = max(1, int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        last_preview = 0.0
        metric_started = time.monotonic()
        source_frames = 0
        corrupted_frames = 0
        reconnect_attempts = 0
        hand_tracking_frames = 0
        hand_tracking_latency_ms = 0.0
        metrics_lock = threading.Lock()
        latest_hands: tuple[np.ndarray, ...] = ()
        previous_hands: tuple[np.ndarray, ...] = ()
        result_lock = threading.Lock()
        callback_failed = threading.Event()

        def handle_gesture_result(
            result: object, _output_image: mp.Image, timestamp_ms: int
        ) -> None:
            nonlocal latest_hands, previous_hands
            nonlocal hand_tracking_frames, hand_tracking_latency_ms
            if self._stop_event.is_set():
                return
            try:
                callback_time = time.monotonic()
                latency_ms = max(0.0, callback_time * 1000.0 - timestamp_ms)
                raw_hands = gesture_result_to_hand_points(result)
                smoothed_hands = smooth_hand_tracks(raw_hands, previous_hands)
                previous_hands = smoothed_hands
                with result_lock:
                    latest_hands = smoothed_hands

                gesture_name = "None"
                gesture_score = 0.0
                gesture_hand = 0
                for hand_index, categories in enumerate(
                    getattr(result, "gestures", None) or []
                ):
                    if not categories:
                        continue
                    top = categories[0]
                    score = float(top.score or 0.0)
                    if score > gesture_score:
                        gesture_name = str(top.category_name or "None")
                        gesture_score = score
                        gesture_hand = hand_index
                self.gesture_ready.emit(
                    {
                        "name": gesture_name,
                        "score": gesture_score,
                        "hand_index": gesture_hand,
                        "hands": smoothed_hands,
                        "timestamp": callback_time,
                    }
                )
                with metrics_lock:
                    hand_tracking_frames += 1
                    hand_tracking_latency_ms += latency_ms
            except Exception as exc:
                callback_failed.set()
                self.camera_status.emit(f"Hand tracking stopped: {exc}", False)

        def handle_holistic_result(
            result: object, _output_image: mp.Image, _timestamp_ms: int
        ) -> None:
            if self._stop_event.is_set():
                return
            try:
                feature, hand_present = extract_frame_features(result)
                self._advance_capture(feature, hand_present)
            except Exception as exc:
                callback_failed.set()
                self.camera_status.emit(f"Sign capture stopped: {exc}", False)

        holistic_options = vision.HolisticLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(HOLISTIC_MODEL_PATH)),
            running_mode=vision.RunningMode.LIVE_STREAM,
            min_face_detection_confidence=0.45,
            min_face_landmarks_confidence=0.45,
            min_pose_detection_confidence=0.45,
            min_pose_landmarks_confidence=0.45,
            min_hand_landmarks_confidence=0.45,
            output_face_blendshapes=False,
            output_segmentation_mask=False,
            result_callback=handle_holistic_result,
        )
        gesture_options = vision.GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=str(GESTURE_MODEL_PATH)),
            running_mode=vision.RunningMode.LIVE_STREAM,
            num_hands=2,
            min_hand_detection_confidence=0.45,
            min_hand_presence_confidence=0.45,
            min_tracking_confidence=0.40,
            canned_gesture_classifier_options=ClassifierOptions(
                max_results=1,
                score_threshold=0.35,
            ),
            result_callback=handle_gesture_result,
        )
        last_timestamp = 0
        try:
            with (
                vision.GestureRecognizer.create_from_options(
                    gesture_options
                ) as gesture_recognizer,
                vision.HolisticLandmarker.create_from_options(
                    holistic_options
                ) as holistic_landmarker,
            ):
                self.camera_status.emit(
                    f"Camera {self.camera_index} ready • {backend_name}", True
                )
                while not self._stop_event.is_set() and not callback_failed.is_set():
                    ok, frame = camera.read()
                    if not ok:
                        self.camera_status.emit("Camera frame was lost.", False)
                        time.sleep(0.1)
                        continue
                    if is_corrupted_camera_frame(frame):
                        corrupted_frames += 1
                        if corrupted_frames < 3:
                            self.performance_status.emit(
                                "Ignoring a broken camera frame…"
                            )
                            continue
                        reconnect_attempts += 1
                        if reconnect_attempts > 3:
                            self.camera_status.emit(
                                "Camera kept sending corrupted frames. Close other camera apps, then press Restart.",
                                False,
                            )
                            break
                        self.performance_status.emit(
                            f"Camera sent corrupted frames • reconnecting ({reconnect_attempts}/3)…"
                        )
                        camera.release()
                        time.sleep(0.5)
                        camera, backend_name = self._open_camera(self.camera_index)
                        if not camera.isOpened():
                            self.camera_status.emit(
                                "Camera reconnect failed. Close other camera apps, then press Restart.",
                                False,
                            )
                            break
                        configure_camera(camera)
                        corrupted_frames = 0
                        continue
                    corrupted_frames = 0
                    reconnect_attempts = 0
                    now = time.monotonic()
                    source_frames += 1
                    capture_height, capture_width = frame.shape[:2]

                    # Keep the visible video independent from MediaPipe. The
                    # tracker is allowed to skip frames under load, but the
                    # person should still see a smooth camera preview.
                    if now - last_preview >= 1.0 / 24.0:
                        with result_lock:
                            hands_for_preview = latest_hands
                        # Upscale a low-resolution source before drawing. Drawing
                        # first would enlarge the overlay itself and make the dots
                        # and lines look pixelated and oversized.
                        display = prepare_preview_frame(frame, hands_for_preview)
                        self.frame_ready.emit(cv2.flip(display, 1))
                        last_preview = now

                    tracking_frame = resize_for_tracking(frame)
                    rgb = cv2.cvtColor(tracking_frame, cv2.COLOR_BGR2RGB)
                    rgb = np.ascontiguousarray(rgb)
                    timestamp = int(time.monotonic() * 1000)
                    if timestamp <= last_timestamp:
                        timestamp = last_timestamp + 1
                    last_timestamp = timestamp
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    gesture_recognizer.recognize_async(mp_image, timestamp)
                    if self._capture_is_pending():
                        holistic_landmarker.detect_async(mp_image, timestamp)

                    metric_elapsed = now - metric_started
                    if metric_elapsed >= 2.0:
                        with metrics_lock:
                            tracked = hand_tracking_frames
                            latency_total = hand_tracking_latency_ms
                            hand_tracking_frames = 0
                            hand_tracking_latency_ms = 0.0
                        preview_fps = source_frames / metric_elapsed
                        tracking_fps = tracked / metric_elapsed
                        average_latency = latency_total / max(1, tracked)
                        resolution_warning = camera_resolution_warning(
                            capture_width, capture_height
                        )
                        if resolution_warning:
                            status = (
                                f"Camera {self.camera_index} • {capture_width}×{capture_height} • "
                                f"{preview_fps:.0f} preview FPS • {tracking_fps:.0f} hand FPS • "
                                f"{resolution_warning}"
                            )
                        elif preview_fps < 8.0:
                            status = (
                                f"Camera {self.camera_index} slow • {capture_width}×{capture_height} • "
                                f"{preview_fps:.0f} preview FPS • "
                                "close browser/meeting camera tabs and improve lighting"
                            )
                        else:
                            status = (
                                f"Camera {self.camera_index} • {capture_width}×{capture_height} • "
                                f"{preview_fps:.0f} preview FPS • "
                                f"{tracking_fps:.0f} hand FPS • {average_latency:.0f} ms"
                            )
                        self.performance_status.emit(status)
                        metric_started = now
                        source_frames = 0
        except Exception as exc:  # Camera failures must be shown in the UI.
            self.camera_status.emit(f"Camera processing stopped: {exc}", False)
        finally:
            camera.release()

