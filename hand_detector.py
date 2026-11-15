import time
import urllib.request

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from config import (
    MAX_HANDS,
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE,
    HAND_MODEL_PATH,
    HAND_MODEL_URL,
    SWAP_HANDEDNESS
)


class HandDetector:

    def __init__(self):

        # Shows which file is running and the active setting
        print(
            "HandDetector loaded from:", __file__,
            "| SWAP_HANDEDNESS =", SWAP_HANDEDNESS
        )

        # Download the model if it is not there yet
        self._ensure_model()

        base_options = python.BaseOptions(
            model_asset_path=str(HAND_MODEL_PATH)
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=DETECTION_CONFIDENCE,
            min_hand_presence_confidence=DETECTION_CONFIDENCE,
            min_tracking_confidence=TRACKING_CONFIDENCE
        )

        self.detector = vision.HandLandmarker.create_from_options(
            options
        )

        self.last_timestamp = 0

        # Pairs of landmark ids that are connected by a line
        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20),
            (0, 17)
        ]

    # ==================================================
    # Download model if missing
    # ==================================================

    def _ensure_model(self):

        if HAND_MODEL_PATH.exists():
            return

        HAND_MODEL_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        urllib.request.urlretrieve(
            HAND_MODEL_URL,
            str(HAND_MODEL_PATH)
        )

    # ==================================================
    # Process Frame
    # ==================================================

    def process(self, frame):

        # OpenCV uses BGR, MediaPipe expects RGB
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        timestamp = int(
            time.monotonic() * 1000
        )

        # VIDEO mode needs strictly increasing timestamps
        if timestamp <= self.last_timestamp:
            timestamp = self.last_timestamp + 1

        self.last_timestamp = timestamp

        return self.detector.detect_for_video(
            mp_image,
            timestamp
        )

    # ==================================================
    # Draw Landmarks
    # ==================================================

    def draw_landmarks(self, frame, results):

        if not results.hand_landmarks:
            return frame

        height, width, _ = frame.shape

        for hand_landmarks in results.hand_landmarks:

            # Lines
            for start, end in self.connections:

                x1 = int(hand_landmarks[start].x * width)
                y1 = int(hand_landmarks[start].y * height)
                x2 = int(hand_landmarks[end].x * width)
                y2 = int(hand_landmarks[end].y * height)

                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 0, 0),
                    2
                )

            # Points + numbers
            for index, landmark in enumerate(hand_landmarks):

                x = int(landmark.x * width)
                y = int(landmark.y * height)

                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 255, 0),
                    -1
                )

                cv2.putText(
                    frame,
                    str(index),
                    (x + 7, y - 7),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2
                )

        return frame

    # ==================================================
    # Get Landmarks
    # ==================================================

    def get_landmarks(self, results):

        all_hands = []

        if not results.hand_landmarks:
            return all_hands

        for hand_landmarks in results.hand_landmarks:

            points = []

            for landmark in hand_landmarks:

                points.append({
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z
                })

            all_hands.append(points)

        return all_hands

    # ==================================================
    # Get Handedness
    # ==================================================

    def get_handedness(self, results):

        hands = []

        if not results.handedness:
            return hands

        for hand in results.handedness:

            if not hand:
                continue

            category = hand[0]

            label = category.category_name

            # The frame is mirrored in camera.py, and the model's
            # label comes out reversed for it. Controlled from config.
            if SWAP_HANDEDNESS:

                if label == "Left":
                    label = "Right"
                elif label == "Right":
                    label = "Left"

            hands.append({
                "label": label,
                "score": category.score
            })

        return hands

    # ==================================================
    # Close
    # ==================================================

    def close(self):

        if self.detector is not None:
            self.detector.close()
