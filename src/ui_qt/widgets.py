"""Reusable Qt widgets."""

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
from src.ui_qt.theme import DRAWING_COLORS_BGR, app_font


class SectionHeader(QLabel):
    def __init__(self, text: str):
        super().__init__(text.upper())
        self.setObjectName("SectionHeader")
        self.setFont(app_font(16, QFont.Weight.Medium))


class ToolButton(QPushButton):
    def __init__(self, tool_id: str, label: str, shortcut: str, symbol: str):
        super().__init__(f"  {symbol}  {label}  ({shortcut})")
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
        self.setStyleSheet(f"background-color: rgb({r},{g},{b});")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(14)
        glow.setOffset(0, 0)
        glow.setColor(QColor("#2563EB"))
        glow.setEnabled(False)
        self.setGraphicsEffect(glow)
        self.toggled.connect(glow.setEnabled)


class BrushSelector(QWidget):
    changed = Signal(int)

    def __init__(self, compact: bool = False):
        super().__init__()
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
    def __init__(self):
        super().__init__()
        self.setObjectName("ToolbarCard")
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 10, 4)
        self._swatch = QLabel()
        self._swatch.setFixedSize(14, 14)
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


class ObjectPropertiesCard(QFrame):
    """Read-only selection properties for Iron Man mode."""

    def __init__(self):
        super().__init__()
        self.setObjectName("HandCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)
        title = QLabel("OBJECT PROPERTIES")
        title.setFont(app_font(13, QFont.Weight.Medium))
        layout.addWidget(title)
        self._rows: dict[str, QLabel] = {}
        for key, label in (
            ("type", "Type"),
            ("count", "Selected"),
            ("x", "X"),
            ("y", "Y"),
            ("width", "Width"),
            ("height", "Height"),
            ("rotation", "Rotation"),
            ("scale_x", "Scale X"),
            ("scale_y", "Scale Y"),
            ("thickness", "Stroke"),
            ("z_index", "Layer"),
            ("group_id", "Group"),
        ):
            row = QHBoxLayout()
            cap = QLabel(label)
            cap.setFont(app_font(12))
            cap.setStyleSheet("color: #9CA3AF;")
            cap.setFixedWidth(72)
            val = QLabel("—")
            val.setFont(app_font(12, QFont.Weight.Medium))
            row.addWidget(cap)
            row.addWidget(val)
            layout.addLayout(row)
            self._rows[key] = val
        self._empty = QLabel("Pinch an object to inspect.")
        self._empty.setFont(app_font(12))
        self._empty.setStyleSheet("color: #6B7280;")
        self._empty.setWordWrap(True)
        layout.addWidget(self._empty)

    def update_properties(self, props: dict | None):
        if not props:
            for val in self._rows.values():
                val.setText("—")
            self._empty.show()
            return
        self._empty.hide()
        for key, val in self._rows.items():
            if key not in props:
                val.setText("—")
                continue
            raw = props[key]
            if key == "rotation":
                val.setText(f"{raw}°")
            elif key == "color" and isinstance(raw, tuple):
                val.setText(f"RGB({raw[2]},{raw[1]},{raw[0]})")
            else:
                val.setText(str(raw))


class HandStatusCard(QFrame):
    def __init__(self, hand_label: str):
        super().__init__()
        self.setObjectName("HandCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        title = QLabel(hand_label.upper())
        title.setFont(app_font(13, QFont.Weight.Medium))
        layout.addWidget(title)
        row = QHBoxLayout()
        self._dot = QLabel("●")
        self._status = QLabel("Idle")
        self._status.setFont(app_font(13, QFont.Weight.Medium))
        row.addWidget(self._dot)
        row.addWidget(self._status)
        row.addStretch()
        layout.addLayout(row)
        self._gesture = QLabel("Gesture: —")
        self._gesture.setFont(app_font(14))
        self._gesture.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(self._gesture)
        self._color = QLabel("Color: —")
        self._color.setFont(app_font(14))
        layout.addWidget(self._color)

    @staticmethod
    def _gesture_text(mode: str) -> str:
        m = mode.upper()
        return {"DRAW": "Index finger", "POINTER": "Index + middle", "ERASER": "Erasing", "OPEN_PALM": "Open palm (neutral)", "PINCH": "Thumb + index pinch"}.get(m, "—")

    @staticmethod
    def _status_color(mode: str) -> str:
        m = mode.upper()
        return {"DRAW": "#2563EB", "POINTER": "#F59E0B", "ERASER": "#EF4444", "OPEN_PALM": "#6B7280", "PINCH": "#2563EB"}.get(m, "#22C55E")

    @staticmethod
    def _status_text(mode: str) -> str:
        m = mode.upper()
        return {"DRAW": "Drawing", "POINTER": "Pointing", "ERASER": "Erasing", "OPEN_PALM": "Idle", "PINCH": "Manipulating"}.get(m, "Idle")

    def update_state(self, mode: str, color_name: str):
        self._status.setText(self._status_text(mode))
        self._dot.setStyleSheet(f"color: {self._status_color(mode)};")
        self._gesture.setText(f"Gesture: {self._gesture_text(mode)}")
        self._color.setText(f"Color: {color_name}")


class ShortcutRow(QWidget):
    def __init__(self, key: str, label: str):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        cap = QLabel(key)
        cap.setObjectName("Keycap")
        cap.setFixedWidth(36)
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
    (tools.SELECT, "Pointer", "V", "◻"),
    (tools.FREEHAND, "Freehand", "1", "✏"),
    (tools.LINE, "Line", "2", "╱"),
    (tools.RECTANGLE, "Rectangle", "3", "▭"),
    (tools.CIRCLE, "Circle", "4", "○"),
    (tools.ARROW, "Arrow", "5", "→"),
    (tools.TEXT, "Text", "T", "T"),
    (tools.ERASER, "Eraser", "E", "⌫"),
    (tools.CLEAR, "Clear", "X", "✕"),
]

SHORTCUTS = [
    ("V", "Pointer / manipulate"), ("B", "Pen (freehand)"), ("1", "Freehand"), ("2", "Line"), ("3", "Rectangle"), ("4", "Circle"),
    ("5", "Arrow"), ("T", "Text"), ("E", "Eraser"), ("X", "Clear"),
    ("Del", "Delete selection"), ("Ctrl+D", "Duplicate"), ("Ctrl+G", "Group"),
    ("PgUp/Dn", "Layer forward/back"),
    ("Z", "Undo"), ("Y", "Redo"), ("S", "Save PNG"),
    ("F", "Fullscreen"), ("H", "Help"), ("Q", "Quit"),
]
