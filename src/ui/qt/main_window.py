"""Main application window — responsive 4-zone layout."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import cv2
import numpy as np

from src.drawing import tools
from src.ui.qt.components.widgets import (
    SHORTCUTS,
    TOOL_ITEMS,
    BrushSelector,
    ColorChip,
    ColorPill,
    HandStatusCard,
    SectionHeader,
    ShortcutRow,
    StatusPill,
    ToolButton,
    ToolPill,
)
from src.ui.qt.layout_metrics import LayoutMetrics
from src.ui.qt.theme import COLOR_NAMES, DRAWING_COLORS_BGR, app_font


class WebcamPanel(QFrame):
    """Rounded panel with contain-mode video display."""

    def __init__(self):
        super().__init__()
        self.setObjectName("WebcamPanel")
        self._padding = 16
        layout = QVBoxLayout(self)
        layout.setContentsMargins(self._padding, self._padding, self._padding, self._padding)
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background-color: #0B1220;")
        self._label.setMinimumSize(320, 240)
        layout.addWidget(self._label, stretch=1)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(shadow)

    @property
    def padding(self) -> int:
        return self._padding

    def available_size(self) -> tuple[int, int]:
        w = max(1, self._label.width())
        h = max(1, self._label.height())
        return w, h

    def set_frame(self, bgr: np.ndarray):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg.copy())
        scaled = pixmap.scaled(
            self._label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)


class MainWindow(QMainWindow):
    tool_selected = Signal(str)
    color_selected = Signal(int)
    brush_changed = Signal(int)
    clear_requested = Signal()
    help_toggled = Signal()
    fullscreen_toggled = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AirBoard")
        self.setMinimumSize(1024, 640)
        self.resize(1280, 720)

        root = QWidget()
        root.setObjectName("CentralRoot")
        self.setCentralWidget(root)
        self._root_layout = QVBoxLayout(root)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self._toolbar = self._build_toolbar()
        self._root_layout.addWidget(self._toolbar)

        mid = QWidget()
        self._mid_layout = QHBoxLayout(mid)
        self._mid_layout.setContentsMargins(12, 12, 12, 12)
        self._mid_layout.setSpacing(12)

        self._left_scroll = QScrollArea()
        self._left_scroll.setObjectName("LeftSidebar")
        self._left_scroll.setWidgetResizable(True)
        self._left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._left_panel = self._build_left_panel()
        self._left_scroll.setWidget(self._left_panel)

        self._webcam = WebcamPanel()

        self._right_scroll = QScrollArea()
        self._right_scroll.setObjectName("RightSidebar")
        self._right_scroll.setWidgetResizable(True)
        self._right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._right_panel = self._build_right_panel()
        self._right_scroll.setWidget(self._right_panel)

        self._mid_layout.addWidget(self._left_scroll)
        self._mid_layout.addWidget(self._webcam, stretch=1)
        self._mid_layout.addWidget(self._right_scroll)
        self._root_layout.addWidget(mid, stretch=1)

        self._bottom = self._build_bottom_bar()
        self._root_layout.addWidget(self._bottom)

        self._apply_layout_metrics()

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("TopToolbar")
        layout = QHBoxLayout(bar)
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

        self._tool_pill = ToolPill("Freehand")
        self._color_pill = ColorPill()
        self._brush_selector_toolbar = BrushSelector(compact=True)
        self._left_hand_pill = StatusPill("L: Idle")
        self._right_hand_pill = StatusPill("R: Idle")

        for widget in (
            self._tool_pill,
            self._color_pill,
            self._brush_selector_toolbar,
            self._left_hand_pill,
            self._right_hand_pill,
        ):
            layout.addWidget(widget)

        self._brush_selector_toolbar.changed.connect(self._on_brush_toolbar)

        layout.addStretch()

        help_btn = QPushButton("?  Help")
        help_btn.setObjectName("IconButton")
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.clicked.connect(self.help_toggled.emit)
        fs_btn = QPushButton("⛶  Fullscreen")
        fs_btn.setObjectName("IconButton")
        fs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fs_btn.clicked.connect(self.fullscreen_toggled.emit)
        layout.addWidget(help_btn)
        layout.addWidget(fs_btn)
        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("SidebarPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        layout.addWidget(SectionHeader("Tools"))
        layout.addSpacing(24)

        self._tool_group = QButtonGroup(self)
        self._tool_group.setExclusive(True)
        self._tool_buttons: dict[str, ToolButton] = {}

        for i, (tool_id, label) in enumerate(TOOL_ITEMS):
            btn = ToolButton(tool_id, label)
            self._tool_group.addButton(btn, i)
            self._tool_buttons[tool_id] = btn
            layout.addWidget(btn)
            if i < len(TOOL_ITEMS) - 1:
                layout.addSpacing(12)
            btn.clicked.connect(lambda checked, t=tool_id: self._on_tool(t))

        self._tool_buttons[tools.FREEHAND].setChecked(True)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1F2937;")
        layout.addSpacing(16)
        layout.addWidget(line)
        layout.addSpacing(16)

        layout.addWidget(SectionHeader("Colors"))
        layout.addSpacing(24)

        color_grid = QWidget()
        grid = QHBoxLayout(color_grid)
        grid.setSpacing(12)
        self._color_group = QButtonGroup(self)
        self._color_chips: list[ColorChip] = []
        for i, bgr in enumerate(DRAWING_COLORS_BGR):
            chip = ColorChip(i, bgr)
            self._color_group.addButton(chip, i)
            self._color_chips.append(chip)
            grid.addWidget(chip)
            chip.clicked.connect(lambda checked, idx=i: self.color_selected.emit(idx))
        grid.addStretch()
        layout.addWidget(color_grid)
        if self._color_chips:
            self._color_chips[0].setChecked(True)

        layout.addSpacing(24)
        layout.addWidget(SectionHeader("Brush"))
        layout.addSpacing(24)
        self._brush_selector = BrushSelector()
        self._brush_selector.changed.connect(self._on_brush_sidebar)
        layout.addWidget(self._brush_selector)

        layout.addStretch()
        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("SidebarPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        layout.addWidget(SectionHeader("Hand Status"))
        layout.addSpacing(8)
        self._left_card = HandStatusCard("Left Hand")
        self._right_card = HandStatusCard("Right Hand")
        layout.addWidget(self._left_card)
        layout.addWidget(self._right_card)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #1F2937;")
        layout.addWidget(line)

        layout.addWidget(SectionHeader("Shortcuts"))
        layout.addSpacing(12)
        for key, label in SHORTCUTS:
            layout.addWidget(ShortcutRow(key, label))
            layout.addSpacing(8)

        layout.addStretch()
        return panel

    def _build_bottom_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("BottomStatusBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        left = QLabel("Draw with index finger  |  Open palm to erase  |  Two fingers for pointer")
        left.setObjectName("BottomBar")
        right = QLabel("q / Esc = Quit  |  f = Fullscreen  |  h = Help")
        right.setObjectName("BottomBar")
        layout.addWidget(left)
        layout.addStretch()
        layout.addWidget(right)
        return bar

    def _on_brush_sidebar(self, size: int):
        self._brush_selector_toolbar.set_size(size)
        self.brush_changed.emit(size)

    def _on_brush_toolbar(self, size: int):
        self._brush_selector.set_size(size)
        self.brush_changed.emit(size)

    def _sync_brush_ui(self, brush_size: int):
        self._brush_selector.set_size(brush_size)
        self._brush_selector_toolbar.set_size(brush_size)

    def _on_tool(self, tool_id: str):
        if tool_id == tools.CLEAR:
            self.clear_requested.emit()
            prev = self._current_tool_id()
            if prev in self._tool_buttons:
                self._tool_buttons[prev].setChecked(True)
            return
        self.tool_selected.emit(tool_id)

    def _current_tool_id(self) -> str:
        for tid, btn in self._tool_buttons.items():
            if btn.isChecked() and tid != tools.CLEAR:
                return tid
        return tools.FREEHAND

    def _apply_layout_metrics(self):
        m = LayoutMetrics.from_window(self.width(), self.height())
        self._toolbar.setFixedHeight(m.toolbar_h)
        self._bottom.setFixedHeight(m.status_h)
        self._left_scroll.setFixedWidth(m.left_w)
        self._right_scroll.setFixedWidth(m.right_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_layout_metrics()

    def bind_state(
        self,
        current_tool: str,
        color_index: int,
        brush_size: int,
        left_mode: str,
        right_mode: str,
        frame_bgr: np.ndarray,
    ):
        tool_label = tools.LABELS.get(current_tool, current_tool)
        self._tool_pill.set_text(tool_label)
        color_name = COLOR_NAMES[color_index] if color_index < len(COLOR_NAMES) else "?"
        bgr = DRAWING_COLORS_BGR[color_index] if color_index < len(DRAWING_COLORS_BGR) else (255, 0, 0)
        self._color_pill.set_color(color_name, bgr)

        self._left_hand_pill.setText(f"L: {HandStatusCard._status_text(left_mode)}")
        self._right_hand_pill.setText(f"R: {HandStatusCard._status_text(right_mode)}")

        if current_tool in self._tool_buttons and not self._tool_buttons[current_tool].isChecked():
            self._tool_buttons[current_tool].setChecked(True)
        if color_index < len(self._color_chips) and not self._color_chips[color_index].isChecked():
            self._color_chips[color_index].setChecked(True)

        self._sync_brush_ui(brush_size)
        self._left_card.update_state(left_mode, color_name, bgr)
        self._right_card.update_state(right_mode, color_name, bgr)
        self._webcam.set_frame(frame_bgr)

    def set_tool_checked(self, tool_id: str):
        if tool_id in self._tool_buttons:
            self._tool_buttons[tool_id].setChecked(True)
