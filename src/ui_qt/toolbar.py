"""Top toolbar."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.ui_qt.theme import app_font
from src.ui_qt.widgets import BrushSelector, ColorPill, StatusPill, ToolPill


class TopToolbar(QWidget):
    help_clicked = Signal()
    fullscreen_clicked = Signal()
    brush_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("TopToolbar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        logo = QLabel("✎")
        logo.setFont(app_font(20, QFont.Weight.DemiBold))
        logo.setStyleSheet("color: #2563EB;")
        name = QLabel("AirBoard")
        name.setFont(app_font(24, QFont.Weight.DemiBold))
        layout.addWidget(logo)
        layout.addWidget(name)
        layout.addSpacing(16)

        self.tool_pill = ToolPill("Freehand")
        self.color_pill = ColorPill()
        self.brush_selector = BrushSelector(compact=True)
        self.left_hand_pill = StatusPill("L: Idle")
        self.right_hand_pill = StatusPill("R: Idle")
        for w in (self.tool_pill, self.color_pill, self.brush_selector,
                  self.left_hand_pill, self.right_hand_pill):
            layout.addWidget(w)
        self.brush_selector.changed.connect(self.brush_changed.emit)
        layout.addStretch()

        help_btn = QPushButton("?  Help")
        help_btn.setObjectName("IconButton")
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.clicked.connect(self.help_clicked.emit)
        fs_btn = QPushButton("⛶  Fullscreen")
        fs_btn.setObjectName("IconButton")
        fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fs_btn.clicked.connect(self.fullscreen_clicked.emit)
        layout.addWidget(help_btn)
        layout.addWidget(fs_btn)
