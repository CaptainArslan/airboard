"""Floating HUD for eraser size feedback."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel

from src.ui_qt.theme import app_font


class EraserHud(QLabel):
    """Temporary floating label showing eraser size (1s visibility)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EraserHud")
        self.setFont(app_font(14))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "background-color: rgba(17, 24, 39, 230);"
            "color: #F9FAFB;"
            "padding: 8px 14px;"
            "border-radius: 8px;"
            "border: 1px solid #2563EB;"
        )
        self.hide()
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self.hide)

    def show_size(self, size: int, anchor_x: int | None = None, anchor_y: int | None = None):
        self.setText(f"◯ {size}px")
        self.adjustSize()
        if anchor_x is not None and anchor_y is not None:
            x = anchor_x - self.width() // 2
            y = anchor_y - self.height() - 24
            self.move(max(8, x), max(8, y))
        else:
            parent = self.parentWidget()
            if parent:
                self.move(
                    (parent.width() - self.width()) // 2,
                    parent.height() // 3,
                )
        self.show()
        self.raise_()
        self._fade_timer.start(1000)
