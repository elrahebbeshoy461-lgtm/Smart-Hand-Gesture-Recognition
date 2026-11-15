from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QGuiApplication
from PyQt6.QtWidgets import QWidget

from config import OVERLAY_SECONDS


class Overlay(QWidget):
    """
    Small message box on top of every window.

    It never takes the keyboard focus and ignores the mouse,
    so it cannot break the keys we send to other apps.
    """

    def __init__(self):

        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )

        # Transparent background + do not activate when shown
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )

        self.resize(380, 96)

        self.text = ""

        # None = no bar, otherwise 0.0 to 1.0
        self.level = None

        # Hides the overlay after OVERLAY_SECONDS
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    # ==================================================
    # Bottom center of the main screen
    # ==================================================

    def place(self):

        screen = QGuiApplication.primaryScreen()

        if screen is None:
            return

        area = screen.geometry()

        x = area.center().x() - self.width() // 2
        y = area.bottom() - self.height() - 80

        self.move(x, y)

    # ==================================================
    # Show a message (and optionally a volume bar)
    # ==================================================

    def show_message(self, text, level=None):

        self.text = text
        self.level = level

        self.place()

        self.show()
        self.raise_()
        self.update()

        self.timer.start(int(OVERLAY_SECONDS * 1000))

    # ==================================================
    # Drawing
    # ==================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        # Rounded dark background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 20, 20, 210))
        painter.drawRoundedRect(
            QRectF(self.rect()),
            18,
            18
        )

        # Text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(
            QFont("Arial", 18, QFont.Weight.Bold)
        )

        if self.level is None:

            text_rect = QRectF(
                0,
                0,
                self.width(),
                self.height()
            )

        else:

            text_rect = QRectF(
                0,
                8,
                self.width(),
                50
            )

        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter,
            self.text
        )

        # Volume bar
        if self.level is not None:

            bar_x = 30
            bar_y = 62
            bar_w = self.width() - 60
            bar_h = 14

            painter.setPen(Qt.PenStyle.NoPen)

            # Empty part
            painter.setBrush(QColor(255, 255, 255, 70))
            painter.drawRoundedRect(
                QRectF(bar_x, bar_y, bar_w, bar_h),
                7,
                7
            )

            # Filled part
            painter.setBrush(QColor(80, 200, 120))
            painter.drawRoundedRect(
                QRectF(
                    bar_x,
                    bar_y,
                    bar_w * max(0.0, min(1.0, self.level)),
                    bar_h
                ),
                7,
                7
            )
