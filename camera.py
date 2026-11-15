import cv2

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT
)


class Camera:

    def __init__(self):

        self.cap = None

    def start(self):

        self.cap = cv2.VideoCapture(CAMERA_INDEX)

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            FRAME_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            FRAME_HEIGHT
        )

        if not self.cap.isOpened():

            self.cap.release()
            self.cap = None
            return False

        return True

    def read(self):

        if self.cap is None:
            return None

        ok, frame = self.cap.read()

        if not ok:
            return None

        return cv2.flip(frame, 1)

    def stop(self):

        if self.cap is not None:

            self.cap.release()
            self.cap = None
