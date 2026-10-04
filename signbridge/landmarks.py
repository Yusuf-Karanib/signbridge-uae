from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from signbridge.config import SEQUENCE_LENGTH


FEATURE_VERSION = "holistic-hands-pose-v1"
POSE_IDS = (0, 11, 12, 13, 14, 15, 16)
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)
POSE_CONNECTIONS = ((11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (0, 11), (0, 12))
POSE_DRAW_IDS = tuple(sorted({index for pair in POSE_CONNECTIONS for index in pair}))

# 7 pose points × (x, y, z, visibility) + 2 hands ×
# (21 local points × xyz + global wrist xy + detected mask).
FEATURE_DIM = 7 * 4 + 2 * (21 * 3 + 2 + 1)


def _landmark_xyz(landmark: object) -> tuple[float, float, float]:
    return float(landmark.x), float(landmark.y), float(landmark.z)


def _pose_anchor(pose: Sequence[object]) -> tuple[np.ndarray, float]:
    if len(pose) > 12:
        left = np.asarray(_landmark_xyz(pose[11]), dtype=np.float32)
        right = np.asarray(_landmark_xyz(pose[12]), dtype=np.float32)
        origin = (left + right) / 2.0
        scale = float(np.linalg.norm(left[:2] - right[:2]))
        if scale >= 0.04:
            return origin, scale
    return np.asarray((0.5, 0.4, 0.0), dtype=np.float32), 0.25


def _hand_features(
    hand: Sequence[object], origin: np.ndarray, body_scale: float
) -> np.ndarray:
    block_size = 21 * 3 + 2 + 1
    if len(hand) < 21:
        return np.zeros(block_size, dtype=np.float32)

    points = np.asarray([_landmark_xyz(item) for item in hand[:21]], dtype=np.float32)
    wrist = points[0]
    palm_a = np.linalg.norm(points[9, :2] - wrist[:2])
    palm_b = np.linalg.norm(points[5, :2] - points[17, :2])
    palm_scale = float(max((palm_a + palm_b) / 2.0, 0.025))

    local = (points - wrist) / palm_scale
    local = np.clip(local, -6.0, 6.0).reshape(-1)
    global_wrist = np.asarray(
        ((wrist[0] - origin[0]) / body_scale, (wrist[1] - origin[1]) / body_scale),
        dtype=np.float32,
    )
    return np.concatenate((local, global_wrist, np.ones(1, dtype=np.float32)))


def extract_frame_features(result: object) -> tuple[np.ndarray, bool]:
    pose = result.pose_landmarks or []
    left_hand = result.left_hand_landmarks or []
    right_hand = result.right_hand_landmarks or []
    origin, body_scale = _pose_anchor(pose)

    pose_values: list[float] = []
    for index in POSE_IDS:
        if len(pose) > index:
            item = pose[index]
            x, y, z = _landmark_xyz(item)
            visibility = float(getattr(item, "visibility", 1.0) or 0.0)
            pose_values.extend(
                (
                    (x - origin[0]) / body_scale,
                    (y - origin[1]) / body_scale,
                    (z - origin[2]) / body_scale,
                    visibility,
                )
            )
        else:
            pose_values.extend((0.0, 0.0, 0.0, 0.0))

    vector = np.concatenate(
        (
            np.asarray(pose_values, dtype=np.float32),
            _hand_features(left_hand, origin, body_scale),
            _hand_features(right_hand, origin, body_scale),
        )
    )
    if vector.shape != (FEATURE_DIM,):
        raise RuntimeError(f"Feature shape changed: {vector.shape}, expected {(FEATURE_DIM,)}")
    hand_present = len(left_hand) >= 21 or len(right_hand) >= 21
    return vector, hand_present


def resample_sequence(
    frames: Sequence[np.ndarray], target_length: int = SEQUENCE_LENGTH
) -> np.ndarray:
    if not frames:
        raise ValueError("Cannot resample an empty sequence")
    data = np.asarray(frames, dtype=np.float32)
    if data.ndim != 2 or data.shape[1] != FEATURE_DIM:
        raise ValueError(f"Expected frames shaped (n, {FEATURE_DIM}), received {data.shape}")
    if len(data) == 1:
        return np.repeat(data, target_length, axis=0)

    old_axis = np.linspace(0.0, 1.0, num=len(data), dtype=np.float32)
    new_axis = np.linspace(0.0, 1.0, num=target_length, dtype=np.float32)
    output = np.empty((target_length, FEATURE_DIM), dtype=np.float32)
    for column in range(FEATURE_DIM):
        output[:, column] = np.interp(new_axis, old_axis, data[:, column])
    return output


def sequence_to_model_vector(sequence: np.ndarray) -> np.ndarray:
    sequence = np.asarray(sequence, dtype=np.float32)
    if sequence.shape != (SEQUENCE_LENGTH, FEATURE_DIM):
        raise ValueError(
            f"Expected sequence {(SEQUENCE_LENGTH, FEATURE_DIM)}, received {sequence.shape}"
        )
    velocity = np.diff(sequence, axis=0, prepend=sequence[:1])
    velocity = np.clip(velocity, -4.0, 4.0)
    combined = np.concatenate((sequence, velocity), axis=1)
    return combined.reshape(-1).astype(np.float32)


def _point_xy(landmark: object, width: int, height: int) -> tuple[int, int]:
    return int(float(landmark.x) * width), int(float(landmark.y) * height)


def _draw_chain(
    frame: np.ndarray,
    landmarks: Sequence[object],
    connections: Sequence[tuple[int, int]],
    color: tuple[int, int, int],
    point_ids: Sequence[int] | None = None,
) -> None:
    if not landmarks:
        return
    height, width = frame.shape[:2]
    for start, end in connections:
        if start < len(landmarks) and end < len(landmarks):
            cv2.line(
                frame,
                _point_xy(landmarks[start], width, height),
                _point_xy(landmarks[end], width, height),
                color,
                2,
                cv2.LINE_AA,
            )
    indexes = point_ids if point_ids is not None else range(len(landmarks))
    for index in indexes:
        if index < len(landmarks):
            cv2.circle(
                frame,
                _point_xy(landmarks[index], width, height),
                3,
                color,
                -1,
                cv2.LINE_AA,
            )


def draw_tracking_overlay(frame: np.ndarray, result: object) -> np.ndarray:
    output = frame.copy()
    _draw_chain(
        output,
        result.pose_landmarks or [],
        POSE_CONNECTIONS,
        (225, 225, 225),
        POSE_DRAW_IDS,
    )
    _draw_chain(output, result.left_hand_landmarks or [], HAND_CONNECTIONS, (218, 178, 66))
    _draw_chain(output, result.right_hand_landmarks or [], HAND_CONNECTIONS, (97, 207, 184))
    return output


def gesture_result_to_hand_points(result: object) -> tuple[np.ndarray, ...]:
    """Copy Gesture Recognizer landmarks into small, thread-safe arrays."""
    hands: list[np.ndarray] = []
    for landmarks in getattr(result, "hand_landmarks", None) or []:
        if len(landmarks) < 21:
            continue
        hands.append(
            np.asarray(
                [[float(item.x), float(item.y), float(item.z)] for item in landmarks[:21]],
                dtype=np.float32,
            )
        )
    return tuple(hands)


def draw_hand_points_overlay(
    frame: np.ndarray, hands: Sequence[np.ndarray]
) -> np.ndarray:
    """Draw the dedicated hand tracker's stable 21-point skeleton."""
    output = frame.copy()
    height, width = output.shape[:2]
    colors = ((97, 207, 184), (218, 178, 66))
    for hand_index, raw_points in enumerate(hands):
        points = np.asarray(raw_points, dtype=np.float32)
        if points.shape[0] < 21 or points.shape[1] < 2:
            continue
        pixels = [
            (int(float(point[0]) * width), int(float(point[1]) * height))
            for point in points[:21]
        ]
        color = colors[hand_index % len(colors)]
        for start, end in HAND_CONNECTIONS:
            cv2.line(output, pixels[start], pixels[end], color, 2, cv2.LINE_AA)
        for point in pixels:
            cv2.circle(output, point, 3, (72, 102, 255), -1, cv2.LINE_AA)
    return output

