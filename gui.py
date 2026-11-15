import sys
import cv2

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
    QCheckBox,
)

from camera import Camera
from hand_detector import HandDetector
from gesture_recognizer import GestureRecognizer
from gesture_controller import GestureController
from overlay import Overlay


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Hand Gesture Recognition")
        self.setMinimumSize(1100, 700)

        # ==================================================
        # Components
        # ==================================================
        self.camera = Camera()
        self.detector = HandDetector()
        self.recognizer = GestureRecognizer()
        self.controller = GestureController()

        # Floating notification overlay
        self.overlay = Overlay()

        self.camera_running = False
        self.closing = False

        # ==================================================
        # Timer
        # ==================================================
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        # ==================================================
        # Build interface
        # ==================================================
        self.setup_ui()

    # ======================================================
    # GUI
    # ======================================================
    def setup_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ==================================================
        # Camera Section
        # ==================================================
        camera_frame = QFrame()
        camera_layout = QVBoxLayout(camera_frame)

        title = QLabel("LIVE CAMERA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        camera_layout.addWidget(title)

        self.camera_label = QLabel("Camera is stopped")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(700, 500)

        camera_layout.addWidget(self.camera_label)

        # ==================================================
        # Camera Buttons
        # ==================================================
        buttons = QHBoxLayout()

        self.start_button = QPushButton("▶ Start Camera")
        self.stop_button = QPushButton("■ Stop Camera")

        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)

        self.stop_button.setEnabled(False)

        # Prevent gesture-generated keyboard input from
        # accidentally activating these buttons.
        self.start_button.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.stop_button.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)

        camera_layout.addLayout(buttons)

        # ==================================================
        # Information Section
        # ==================================================
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("HAND ANALYSIS")
        info_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))

        info_layout.addWidget(info_title)

        # ==================================================
        # Gesture
        # ==================================================
        info_layout.addWidget(QLabel("Detected Gesture"))

        self.gesture_label = QLabel("NONE")
        self.gesture_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.gesture_label.setFont(
            QFont("Arial", 24, QFont.Weight.Bold)
        )

        info_layout.addWidget(self.gesture_label)

        # ==================================================
        # Hand
        # ==================================================
        info_layout.addWidget(QLabel("Hand"))

        self.hand_label = QLabel("Unknown")
        self.hand_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.hand_label.setFont(QFont("Arial", 20))

        info_layout.addWidget(self.hand_label)

        # ==================================================
        # Extended Fingers
        # ==================================================
        info_layout.addWidget(QLabel("Extended Fingers"))

        self.fingers_label = QLabel("0")
        self.fingers_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.fingers_label.setFont(QFont("Arial", 20))

        info_layout.addWidget(self.fingers_label)

        # ==================================================
        # Confidence
        # ==================================================
        info_layout.addWidget(
            QLabel("Detection Confidence")
        )

        self.confidence_label = QLabel("0.00")
        self.confidence_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.confidence_label.setFont(
            QFont("Arial", 20)
        )

        info_layout.addWidget(self.confidence_label)

        # ==================================================
        # System Status
        # ==================================================
        info_layout.addWidget(QLabel("System Status"))

        self.status_label = QLabel("● Camera Stopped")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        info_layout.addWidget(self.status_label)

        # ==================================================
        # Gesture Control
        # ==================================================
        self.control_checkbox = QCheckBox(
            "Enable Gesture Control"
        )
        self.control_checkbox.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.control_checkbox.toggled.connect(
            self.toggle_control
        )

        info_layout.addWidget(self.control_checkbox)

        # ==================================================
        # Last Action
        # ==================================================
        info_layout.addWidget(QLabel("Last Action"))

        self.action_label = QLabel("-")
        self.action_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.action_label.setWordWrap(True)

        info_layout.addWidget(self.action_label)
        info_layout.addStretch()

        # ==================================================
        # Exit
        # ==================================================
        exit_button = QPushButton("✕ Exit")
        exit_button.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        exit_button.clicked.connect(self.close)

        info_layout.addWidget(exit_button)

        # ==================================================
        # Add Sections
        # ==================================================
        main_layout.addWidget(camera_frame, 3)
        main_layout.addWidget(info_frame, 1)

    # ======================================================
    # Start Camera
    # ======================================================
    def start_camera(self):

        if self.camera_running:
            return

        try:
            camera_started = self.camera.start()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Camera Error",
                f"Could not start the camera:\n{error}"
            )
            return

        if camera_started:
            self.camera_running = True

            self.controller.reset()

            self.timer.start(30)

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            self.status_label.setText(
                "● Camera Running"
            )

            self.camera_label.clear()
            self.camera_label.setText("Starting camera...")

        else:
            QMessageBox.critical(
                self,
                "Camera Error",
                "Cannot open camera. Check that it is connected "
                "and not being used by another application."
            )

    # ======================================================
    # Stop Camera
    # ======================================================
    def stop_camera(self):

        self.timer.stop()

        try:
            self.camera.stop()
        except Exception as error:
            print(f"Camera stop warning: {error}")

        self.camera_running = False

        self.controller.reset()

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.camera_label.clear()
        self.camera_label.setText("Camera is stopped")

        self.gesture_label.setText("NONE")
        self.hand_label.setText("Unknown")
        self.fingers_label.setText("0")
        self.confidence_label.setText("0.00")
        self.status_label.setText("● Camera Stopped")

        self.overlay.hide()

    # ======================================================
    # Toggle Gesture Control
    # ======================================================
    def toggle_control(self, checked):

        self.controller.enabled = bool(checked)

        # Reset gesture history when switching modes.
        self.controller.reset()

        if checked:
            self.action_label.setText(
                "Gesture control enabled"
            )

            if self.camera_running:
                self.overlay.show_message(
                    "Gesture Control Enabled"
                )

        else:
            self.action_label.setText(
                "Gesture control disabled"
            )

            self.overlay.show_message(
                "Gesture Control Disabled"
            )

    # ======================================================
    # Update Frame
    # ======================================================
    def update_frame(self):

        if not self.camera_running:
            return

        try:
            frame = self.camera.read()

            if frame is None:
                self.stop_camera()

                QMessageBox.warning(
                    self,
                    "Camera Warning",
                    "The camera stopped sending frames."
                )
                return

            # ==============================================
            # Detect Hands
            # ==============================================
            results = self.detector.process(frame)

            # ==============================================
            # Draw Landmarks
            # ==============================================
            self.detector.draw_landmarks(
                frame,
                results
            )

            # ==============================================
            # Get Landmarks
            # ==============================================
            landmarks_list = (
                self.detector.get_landmarks(results)
            )

            # ==============================================
            # Get Handedness
            # ==============================================
            handedness_list = (
                self.detector.get_handedness(results)
            )

            # ==============================================
            # No Hand Detected
            # ==============================================
            if not landmarks_list:

                self.gesture_label.setText("NONE")
                self.hand_label.setText("No Hand")
                self.fingers_label.setText("0")
                self.confidence_label.setText("0.00")

                self.controller.reset()

            # ==============================================
            # Hand Detected
            # ==============================================
            else:

                hands_info = []

                for index, hand_landmarks in enumerate(
                    landmarks_list
                ):

                    hand_gesture, hand_fingers = (
                        self.recognizer.recognize(
                            hand_landmarks
                        )
                    )

                    if index < len(handedness_list):
                        side = handedness_list[index]["label"]
                    else:
                        side = "Unknown"

                    hands_info.append({
                        "label": side,
                        "landmarks": hand_landmarks,
                        "gesture": hand_gesture,
                        "fingers": hand_fingers,
                    })

                # ==========================================
                # Gestures -> Actions
                # ==========================================
                result = self.controller.update(hands_info)

                if result:

                    # Support both return formats:
                    # 1. "FIST PLAYPAUSE"
                    # 2. ("VOLUME 50%", 0.5)
                    if isinstance(result, tuple):
                        action, level = result

                    else:
                        action = result
                        level = None

                    if action:

                        action_text = str(action)

                        self.action_label.setText(
                            action_text
                        )

                        # Display the action and optional
                        # volume level in the floating overlay.
                        self.overlay.show_message(
                            action_text,
                            level
                        )

                # ==========================================
                # Update Information Panel
                # ==========================================
                first_hand = hands_info[0]

                gesture = first_hand["gesture"]
                fingers = first_hand["fingers"]

                if handedness_list:
                    hand_label = (
                        handedness_list[0]["label"]
                    )
                    confidence = (
                        handedness_list[0]["score"]
                    )
                else:
                    hand_label = "Unknown"
                    confidence = 0.0

                self.gesture_label.setText(
                    str(gesture)
                )

                self.hand_label.setText(
                    str(hand_label)
                )

                self.fingers_label.setText(
                    str(sum(fingers))
                )

                self.confidence_label.setText(
                    f"{confidence:.2f}"
                )

            # ==============================================
            # Convert Frame to RGB
            # ==============================================
            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            height, width, channels = rgb.shape
            bytes_per_line = channels * width

            image = QImage(
                rgb.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            pixmap = QPixmap.fromImage(image)

            self.camera_label.setPixmap(
                pixmap.scaled(
                    self.camera_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

        except Exception as error:
            # Avoid repeatedly showing a message box on every
            # timer tick if an unexpected frame-processing error occurs.
            print(f"Frame processing error: {error}")

            self.timer.stop()
            self.camera_running = False

            try:
                self.camera.stop()
            except Exception:
                pass

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.status_label.setText(
                "● Camera Error"
            )

            QMessageBox.critical(
                self,
                "Processing Error",
                f"An error occurred while processing the camera frame:\n"
                f"{error}"
            )

    # ======================================================
    # Close
    # ======================================================
    def closeEvent(self, event):

        self.timer.stop()
        self.camera_running = False

        try:
            self.camera.stop()
        except Exception as error:
            print(f"Camera cleanup warning: {error}")

        try:
            self.overlay.hide()
        except Exception:
            pass

        try:
            self.detector.close()
        except Exception as error:
            print(f"Detector cleanup warning: {error}")

        cv2.destroyAllWindows()

        event.accept()


# ==========================================================
# MAIN
# ==========================================================

def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


# ==========================================================
# Run
# ==========================================================

if __name__ == "__main__":
    main()
