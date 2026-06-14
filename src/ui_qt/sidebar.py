"""Left tools sidebar."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.drawing import tools
from src.ui_qt.theme import DRAWING_COLORS_BGR
from src.ui_qt.widgets import BrushSelector, ColorChip, SectionHeader, ToolButton, TOOL_ITEMS


class LeftSidebar(QScrollArea):
    tool_selected = Signal(str)
    color_selected = Signal(int)
    brush_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("LeftSidebar")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QWidget()
        panel.setObjectName("SidebarPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        layout.addWidget(SectionHeader("Tools"))
        layout.addSpacing(24)
        self._tool_group = QButtonGroup(self)
        self.tool_buttons: dict[str, ToolButton] = {}
        for i, (tool_id, label, shortcut, symbol) in enumerate(TOOL_ITEMS):
            btn = ToolButton(tool_id, label, shortcut, symbol)
            self._tool_group.addButton(btn, i)
            self.tool_buttons[tool_id] = btn
            layout.addWidget(btn)
            if i < len(TOOL_ITEMS) - 1:
                layout.addSpacing(12)
            btn.clicked.connect(lambda checked, t=tool_id: self._on_tool(t))
        self.tool_buttons[tools.FREEHAND].setChecked(True)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addSpacing(16)
        layout.addWidget(line)
        layout.addSpacing(16)

        layout.addWidget(SectionHeader("Colors"))
        layout.addSpacing(24)
        color_row = QWidget()
        grid = QHBoxLayout(color_row)
        grid.setSpacing(12)
        self.color_chips: list[ColorChip] = []
        for i, bgr in enumerate(DRAWING_COLORS_BGR):
            chip = ColorChip(i, bgr)
            self.color_chips.append(chip)
            grid.addWidget(chip)
            chip.clicked.connect(lambda checked, idx=i: self.color_selected.emit(idx))
        grid.addStretch()
        layout.addWidget(color_row)
        if self.color_chips:
            self.color_chips[0].setChecked(True)

        layout.addSpacing(24)
        layout.addWidget(SectionHeader("Brush"))
        layout.addSpacing(24)
        self.brush_selector = BrushSelector()
        self.brush_selector.changed.connect(self._on_brush_sidebar)
        layout.addWidget(self.brush_selector)
        layout.addStretch()
        self.setWidget(panel)

    def _on_tool(self, tool_id: str):
        if tool_id == tools.CLEAR:
            self.tool_selected.emit(tool_id)
            prev = self._current_tool()
            if prev in self.tool_buttons:
                self.tool_buttons[prev].setChecked(True)
            return
        self.tool_selected.emit(tool_id)

    def _current_tool(self) -> str:
        for tid, btn in self.tool_buttons.items():
            if btn.isChecked() and tid != tools.CLEAR:
                return tid
        return tools.FREEHAND

    def _on_brush_sidebar(self, size: int):
        self.brush_changed.emit(size)

    def sync_brush(self, size: int):
        self.brush_selector.set_size(size)

    def set_tool_checked(self, tool_id: str):
        if tool_id in self.tool_buttons:
            self.tool_buttons[tool_id].setChecked(True)
