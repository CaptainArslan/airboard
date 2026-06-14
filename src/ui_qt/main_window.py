"""Main application window."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QMainWindow, QVBoxLayout, QWidget

import numpy as np

from src.drawing import tools
from src.ui_qt.camera_view import CameraView
from src.ui_qt.eraser_hud import EraserHud
from src.ui_qt.layout_metrics import LayoutMetrics
from src.ui_qt.right_panel import RightPanel
from src.ui_qt.sidebar import LeftSidebar
from src.ui_qt.status_bar import BottomStatusBar
from src.ui_qt.theme import COLOR_NAMES, DRAWING_COLORS_BGR
from src.ui_qt.toolbar import TopToolbar
from src.ui_qt.widgets import HandStatusCard


class MainWindow(QMainWindow):
    tool_selected = Signal(str)
    color_selected = Signal(int)
    brush_changed = Signal(int)
    clear_requested = Signal()
    undo_requested = Signal()
    redo_requested = Signal()
    save_requested = Signal()
    text_committed = Signal(str)
    text_cancelled = Signal()
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
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.toolbar = TopToolbar()
        self.toolbar.help_clicked.connect(self.help_toggled.emit)
        self.toolbar.fullscreen_clicked.connect(self.fullscreen_toggled.emit)
        root_layout.addWidget(self.toolbar)

        mid = QWidget()
        mid_layout = QHBoxLayout(mid)
        mid_layout.setContentsMargins(12, 12, 12, 12)
        mid_layout.setSpacing(12)

        self.left_sidebar = LeftSidebar()
        self.left_sidebar.tool_selected.connect(self._on_tool)
        self.left_sidebar.color_selected.connect(self.color_selected.emit)
        self.left_sidebar.brush_changed.connect(self._on_brush)
        self.toolbar.brush_changed.connect(self._on_brush)

        self.camera_view = CameraView()
        self._eraser_hud = EraserHud(self.camera_view)
        self.right_panel = RightPanel()

        mid_layout.addWidget(self.left_sidebar)
        mid_layout.addWidget(self.camera_view, stretch=1)
        mid_layout.addWidget(self.right_panel)
        root_layout.addWidget(mid, stretch=1)

        self.bottom_bar = BottomStatusBar()
        root_layout.addWidget(self.bottom_bar)

        self._text_input = QLineEdit(self)
        self._text_input.setPlaceholderText("Type text, Enter to place, Esc to cancel")
        self._text_input.hide()
        self._text_input.returnPressed.connect(self._commit_text)
        self._apply_layout_metrics()

    def _on_tool(self, tool_id: str):
        if tool_id == tools.CLEAR:
            self.clear_requested.emit()
            return
        self.tool_selected.emit(tool_id)

    def _on_brush(self, size: int):
        self.toolbar.brush_selector.set_size(size)
        self.brush_changed.emit(size)

    def sync_brush(self, size: int):
        self.left_sidebar.sync_brush(size)
        self.toolbar.brush_selector.set_size(size)

    def _commit_text(self):
        text = self._text_input.text()
        self._text_input.hide()
        self._text_input.clear()
        if text.strip():
            self.text_committed.emit(text)

    def cancel_text_input(self):
        self._text_input.hide()
        self._text_input.clear()
        self.text_cancelled.emit()

    def start_text_input(self):
        self._text_input.show()
        self._text_input.setFocus()

    def keyPressEvent(self, event):
        if self._text_input.isVisible() and event.key() == Qt.Key.Key_Escape:
            self.cancel_text_input()
            return
        if event.text() and len(event.text()) == 1 and event.text().isprintable():
            if self.left_sidebar._current_tool() == tools.TEXT and not self._text_input.isVisible():
                self.start_text_input()
                self._text_input.setText(event.text())
                return
        super().keyPressEvent(event)

    def _apply_layout_metrics(self):
        m = LayoutMetrics.from_window(self.width(), self.height())
        self.toolbar.setFixedHeight(m.toolbar_h)
        self.bottom_bar.setFixedHeight(m.status_h)
        self.left_sidebar.setFixedWidth(m.left_w)
        self.right_panel.setFixedWidth(m.right_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_layout_metrics()

    def show_eraser_hud(self, size: int, x: int | None = None, y: int | None = None):
        self._eraser_hud.show_size(size, x, y)

    def bind_state(
        self,
        current_tool: str,
        color_index: int,
        brush_size: int,
        eraser_size: int,
        left_mode: str,
        right_mode: str,
        frame_bgr: np.ndarray,
        text_draft: str = "",
        text_input_active: bool = False,
        selection_props: dict | None = None,
    ):
        from src.drawing import tools as T
        tool_label = T.LABELS.get(current_tool, current_tool)
        self.toolbar.tool_pill.set_text(tool_label)
        color_name = COLOR_NAMES[color_index] if color_index < len(COLOR_NAMES) else "?"
        bgr = DRAWING_COLORS_BGR[color_index] if color_index < len(DRAWING_COLORS_BGR) else (255, 0, 0)
        self.toolbar.color_pill.set_color(color_name, bgr)
        self.toolbar.left_hand_pill.setText(f"L: {HandStatusCard._status_text(left_mode)}")
        self.toolbar.right_hand_pill.setText(f"R: {HandStatusCard._status_text(right_mode)}")

        if current_tool in self.left_sidebar.tool_buttons:
            btn = self.left_sidebar.tool_buttons[current_tool]
            if not btn.isChecked():
                btn.setChecked(True)
        if color_index < len(self.left_sidebar.color_chips):
            chip = self.left_sidebar.color_chips[color_index]
            if not chip.isChecked():
                chip.setChecked(True)

        self.sync_brush(brush_size)
        self.bottom_bar.update_tool_info(current_tool, brush_size, eraser_size)
        self.right_panel.left_card.update_state(left_mode, color_name)
        self.right_panel.right_card.update_state(right_mode, color_name)
        self.right_panel.properties_card.update_properties(selection_props)
        self.camera_view.set_frame(frame_bgr)

        if text_input_active and text_draft and self._text_input.isVisible():
            self._text_input.setText(text_draft)

    def set_tool_checked(self, tool_id: str):
        self.left_sidebar.set_tool_checked(tool_id)
