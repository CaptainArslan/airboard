"""Qt UI components."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.drawing import tools
from src.ui.qt.theme import COLOR_NAMES, DRAWING_COLORS_BGR, app_font


class SectionHeader(QLabel):
    def __init__(self, text: str):
        super().__init__(text.upper())
        self.setObjectName("SectionHeader")
        self.setFont(app_font(16, QFont.Weight.Medium))


class ToolButton(QPushButton):
    def __init__(self, tool_id: str, label: str):
        super().__init__(f"  {label}")
        self.tool_id = tool_id
        self.setObjectName("ToolButton")
        self.setCheckable(True)
        self.setFont(app_font(14))
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class ColorChip(QPushButton):
    def __init__(self, index: int, bgr: tuple[int, int, int]):
        super().__init__()
        self.index = index
        self.setObjectName("ColorChip")
        self.setCheckable(True)
        r, g, b = bgr[2], bgr[1], bgr[0]
        self._rgb = (r, g, b)
        self.setStyleSheet(f"background-color: rgb({r},{g},{b});")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(14)
        self._glow.setOffset(0, 0)
        self._glow.setColor(QColor("#2563EB"))
        self._glow.setEnabled(False)
        self.setGraphicsEffect(self._glow)
        self.toggled.connect(self._glow.setEnabled)


class BrushSelector(QWidget):
    changed = Signal(int)

    def __init__(self, compact: bool = False):
        super().__init__()
        self._compact = compact
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6 if compact else 8)
        self._minus = QPushButton("−")
        self._minus.setObjectName("BrushButton")
        if compact:
            self._minus.setFixedSize(24, 24)
        self._label = QLabel("6px")
        self._label.setFont(app_font(13 if compact else 14))
        self._plus = QPushButton("+")
        self._plus.setObjectName("BrushButton")
        if compact:
            self._plus.setFixedSize(24, 24)
        layout.addWidget(self._minus)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._plus)
        self._minus.clicked.connect(lambda: self._adjust(-1))
        self._plus.clicked.connect(lambda: self._adjust(1))
        self._size = 6

    def _adjust(self, delta: int):
        self._size = max(1, min(40, self._size + delta))
        self._label.setText(f"{self._size}px")
        self.changed.emit(self._size)

    def set_size(self, size: int):
        self._size = size
        self._label.setText(f"{size}px")


class ColorPill(QFrame):
    """Toolbar color indicator with swatch + label."""

    def __init__(self):
        super().__init__()
        self.setObjectName("ToolbarCard")
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 10, 4)
        row.setSpacing(8)
        self._swatch = QLabel()
        self._swatch.setFixedSize(14, 14)
        self._swatch.setStyleSheet(
            "background-color: #2563EB; border-radius: 7px; border: 1px solid #374151;"
        )
        self._label = QLabel("Blue")
        self._label.setFont(app_font(13, QFont.Weight.Medium))
        row.addWidget(self._swatch)
        row.addWidget(self._label)

    def set_color(self, name: str, bgr: tuple[int, int, int]):
        self._label.setText(name)
        r, g, b = bgr[2], bgr[1], bgr[0]
        self._swatch.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border-radius: 7px; border: 1px solid #374151;"
        )


class ToolPill(QFrame):
    """Toolbar tool indicator."""

    def __init__(self, text: str = "Freehand"):
        super().__init__()
        self.setObjectName("ToolbarCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        self._label = QLabel(text)
        self._label.setFont(app_font(13, QFont.Weight.Medium))
        layout.addWidget(self._label)

    def set_text(self, text: str):
        self._label.setText(text)


class HandStatusCard(QFrame):
    def __init__(self, hand_label: str):
        super().__init__()
        self.setObjectName("HandCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel(hand_label.upper())
        title.setObjectName("HandCardTitle")
        title.setFont(app_font(13, QFont.Weight.Medium))
        layout.addWidget(title)

        self._status_row = QHBoxLayout()
        self._dot = QLabel("●")
        self._status = QLabel("Idle")
        self._status.setFont(app_font(13, QFont.Weight.Medium))
        self._status_row.addWidget(self._dot)
        self._status_row.addWidget(self._status)
        self._status_row.addStretch()
        layout.addLayout(self._status_row)

        self._gesture = QLabel("Gesture: —")
        self._gesture.setObjectName("HandCardValue")
        self._gesture.setFont(app_font(14))
        layout.addWidget(self._gesture)

        self._color = QLabel("Color: —")
        self._color.setObjectName("HandCardValue")
        self._color.setFont(app_font(14))
        self._color_dot = QLabel("●")
        self._color_dot.setFont(app_font(10))
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        color_row.addWidget(self._color)
        color_row.addWidget(self._color_dot)
        color_row.addStretch()
        layout.addLayout(color_row)

    @staticmethod
    def _gesture_text(mode: str) -> str:
        m = mode.upper()
        if m == "DRAW":
            return "Index finger"
        if m == "POINTER":
            return "Index + middle"
        if m == "ERASER":
            return "Open palm"
        return "—"

    @staticmethod
    def _status_color(mode: str) -> str:
        m = mode.upper()
        if m == "DRAW":
            return "#2563EB"
        if m == "POINTER":
            return "#F59E0B"
        if m == "ERASER":
            return "#EF4444"
        return "#22C55E"

    @staticmethod
    def _status_text(mode: str) -> str:
        m = mode.upper()
        if m == "DRAW":
            return "Drawing"
        if m == "POINTER":
            return "Pointing"
        if m == "ERASER":
            return "Erasing"
        return "Idle"

    def update_state(self, mode: str, color_name: str, bgr: tuple[int, int, int] | None = None):
        self._status.setText(self._status_text(mode))
        self._dot.setStyleSheet(f"color: {self._status_color(mode)}; font-size: 14px;")
        self._gesture.setText(f"Gesture: {self._gesture_text(mode)}")
        self._color.setText(f"Color: {color_name}")
        if bgr is not None:
            r, g, b = bgr[2], bgr[1], bgr[0]
            self._color_dot.setStyleSheet(f"color: rgb({r},{g},{b}); font-size: 10px;")
            self._color_dot.show()
        else:
            self._color_dot.hide()


class ShortcutRow(QWidget):
    def __init__(self, key: str, label: str):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        cap = QLabel(key)
        cap.setObjectName("Keycap")
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap.setFixedWidth(32)
        text = QLabel(label)
        text.setFont(app_font(12))
        text.setStyleSheet("color: #9CA3AF;")
        row.addWidget(cap)
        row.addWidget(text)
        row.addStretch()


class StatusPill(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        self.setObjectName("StatusPill")
        self.setFont(app_font(13, QFont.Weight.Medium))


TOOL_ITEMS = [
    (tools.FREEHAND, "Freehand"),
    (tools.LINE, "Line"),
    (tools.RECTANGLE, "Rectangle"),
    (tools.CIRCLE, "Circle"),
    (tools.ARROW, "Arrow"),
    (tools.ERASER, "Eraser"),
    (tools.CLEAR, "Clear All"),
]

SHORTCUTS = [
    ("1", "Freehand"), ("2", "Line"), ("3", "Rectangle"),
    ("4", "Circle"), ("5", "Arrow"), ("E", "Eraser"),
    ("X", "Clear"), ("F", "Fullscreen"), ("H", "Help"), ("Q", "Quit"),
]
