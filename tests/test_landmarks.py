from dataclasses import dataclass
import unittest

import numpy as np

from signbridge.config import SEQUENCE_LENGTH
from signbridge.landmarks import (
    FEATURE_DIM,
    draw_hand_points_overlay,
    extract_frame_features,
    gesture_result_to_hand_points,
    resample_sequence,
    sequence_to_model_vector,
)


@dataclass
class FakeLandmark:
    x: float
    y: float
    z: float
    visibility: float = 1.0


@dataclass
class FakeResult:
    pose_landmarks: list[FakeLandmark]
    left_hand_landmarks: list[FakeLandmark]
    right_hand_landmarks: list[FakeLandmark]


class LandmarkTests(unittest.TestCase):
    def test_extract_and_resample_have_fixed_shapes(self) -> None:
        pose = [FakeLandmark(0.3 + index * 0.01, 0.2, 0.0) for index in range(33)]
        hand = [FakeLandmark(0.4 + index * 0.004, 0.4, 0.01) for index in range(21)]
        result = FakeResult(pose, hand, [])

        frame, hand_present = extract_frame_features(result)
        sequence = resample_sequence([frame, frame + 0.01, frame + 0.02])
        vector = sequence_to_model_vector(sequence)

        self.assertTrue(hand_present)
        self.assertEqual(frame.shape, (FEATURE_DIM,))
        self.assertEqual(sequence.shape, (SEQUENCE_LENGTH, FEATURE_DIM))
        self.assertEqual(vector.shape, (SEQUENCE_LENGTH * FEATURE_DIM * 2,))
        self.assertTrue(np.isfinite(vector).all())

    def test_missing_landmarks_are_safe(self) -> None:
        frame, hand_present = extract_frame_features(FakeResult([], [], []))

        self.assertFalse(hand_present)
        self.assertEqual(frame.shape, (FEATURE_DIM,))
        self.assertTrue(np.isfinite(frame).all())

    def test_gesture_hand_points_can_be_copied_and_drawn(self) -> None:
        hand = [FakeLandmark(0.2 + index * 0.01, 0.3, 0.0) for index in range(21)]

        class GestureResult:
            hand_landmarks = [hand]

        points = gesture_result_to_hand_points(GestureResult())
        image = np.zeros((240, 320, 3), dtype=np.uint8)
        drawn = draw_hand_points_overlay(image, points)

        self.assertEqual(len(points), 1)
        self.assertEqual(points[0].shape, (21, 3))
        self.assertGreater(int(drawn.sum()), 0)


if __name__ == "__main__":
    unittest.main()

