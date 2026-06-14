import os
import time
from dataclasses import dataclass

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarksConnections

from src.config import settings


class _LandmarkWrapper:
    """Adapt Tasks API landmarks to the landmark[index].x interface."""

    def __init__(self, landmarks):
        self.landmark = landmarks


@dataclass
class TrackedHand:
    """One detected hand with landmarks and pixel coordinates."""

    landmarks: _LandmarkWrapper
    handedness: str
    pixel_coords: list[tuple[int, int]]


class HandTracker:
    """MediaPipe hand detection and landmark access."""

    def __init__(self):
        if not os.path.isfile(settings.HAND_MODEL_PATH):
            raise FileNotFoundError(
                f"Hand landmarker model not found at {settings.HAND_MODEL_PATH}. "
                "Download hand_landmarker.task into the models/ folder."
            )

        options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=settings.HAND_MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=settings.MAX_NUM_HANDS,
            min_hand_detection_confidence=settings.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=settings.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.MIN_TRACKING_CONFIDENCE,
        )
        self._detector = vision.HandLandmarker.create_from_options(options)
        self._connections = HandLandmarksConnections.HAND_CONNECTIONS
        self._start_time = time.time()
        self._frame_index = 0

    def process(self, bgr_frame):
        """
        Run hand tracking on a BGR frame.
        Returns a list of TrackedHand (empty when no hands detected).
        """
        self._frame_index += 1
        h, w = bgr_frame.shape[:2]
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp_ms = int((time.time() - self._start_time) * 1000)
        result = self._detector.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return []

        hands = []
        for i, raw_landmarks in enumerate(result.hand_landmarks):
            handedness = "Right"
            if result.handedness and i < len(result.handedness):
                handedness = result.handedness[i][0].category_name

            wrapper = _LandmarkWrapper(raw_landmarks)
            pixel_coords = [
                self.landmark_to_pixel(lm, w, h) for lm in raw_landmarks
            ]
            hands.append(TrackedHand(
                landmarks=wrapper,
                handedness=handedness,
                pixel_coords=pixel_coords,
            ))

        return hands

    def draw_skeleton(self, frame, hand):
        """Draw hand connections on frame for debug visualization."""
        if hand is None:
            return

        points = hand.pixel_coords
        for connection in self._connections:
            start = points[connection.start]
            end = points[connection.end]
            cv2.line(frame, start, end, (0, 255, 0), 2)

        for point in points:
            cv2.circle(frame, point, 3, (0, 0, 255), -1)

    @staticmethod
    def landmark_to_pixel(landmark, frame_width, frame_height):
        """Convert normalized landmark to pixel coordinates."""
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)
        return x, y

    def close(self):
        """Release MediaPipe resources."""
        self._detector.close()
