class GestureRecognizer:

    # MediaPipe landmark indices
    WRIST = 0
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_PIP = 6
    INDEX_TIP = 8
    MIDDLE_PIP = 10
    MIDDLE_TIP = 12
    RING_PIP = 14
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_TIP = 20

    GESTURES = {
        0: "FIST",
        1: "ONE",
        2: "TWO",
        3: "THREE",
        4: "FOUR",
        5: "OPEN PALM"
    }

    def recognize(self, landmarks):

        fingers = self._fingers_up(landmarks)
        count = sum(fingers)
        gesture = self.GESTURES.get(count, "UNKNOWN")

        return gesture, fingers

    def _fingers_up(self, landmarks):

        fingers = []

        # Thumb: tip is farther from the pinky than the IP joint
        if (
            abs(
                landmarks[self.THUMB_TIP]["x"]
                - landmarks[self.PINKY_MCP]["x"]
            )
            > abs(
                landmarks[self.THUMB_IP]["x"]
                - landmarks[self.PINKY_MCP]["x"]
            )
        ):
            fingers.append(1)
        else:
            fingers.append(0)

        # Other fingers: tip is above the PIP joint
        for tip, pip in (
            (self.INDEX_TIP, self.INDEX_PIP),
            (self.MIDDLE_TIP, self.MIDDLE_PIP),
            (self.RING_TIP, self.RING_PIP),
            (self.PINKY_TIP, self.PINKY_PIP)
        ):

            if landmarks[tip]["y"] < landmarks[pip]["y"]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers
