"""AirBoard application — PySide6 shell + drawing engine."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QVBoxLayout

from src.app.app_state import AppState, ToolMode
from src.app.frame_processor import FrameProcessor
from src.config import settings
from src.drawing import tools
from src.ui_qt.main_window import MainWindow
from src.ui_qt.theme import app_font, load_poppins, load_stylesheet

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPORTS_DIR = PROJECT_ROOT / "exports"

_TOOL_MAP = {
    tools.FREEHAND: ToolMode.FREEHAND,
    tools.LINE: ToolMode.LINE,
    tools.RECTANGLE: ToolMode.RECTANGLE,
    tools.CIRCLE: ToolMode.CIRCLE,
    tools.ARROW: ToolMode.ARROW,
    tools.TEXT: ToolMode.TEXT,
    tools.ERASER: ToolMode.ERASER,
    tools.SELECT: ToolMode.SELECT,
}


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AirBoard Help")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        text = QLabel(
            "AirBoard in one line:\n"
            "  Draw with one finger · Select with pinch · Control with two hands · Delete via trash\n\n"
            "Drawing Mode (B / 1–5)\n"
            "  Index finger up — draw on canvas\n\n"
            "Selection Mode (V)\n"
            "  Pinch once — select object (Point → Pinch → Release)\n"
            "  Pinch + hold — move object (Pinch → Hold → Move → Release)\n"
            "  Two-hand pinch — scale, stretch, rotate (both hands must pinching)\n"
            "  Drag to trash + release — delete (not on hover alone)\n\n"
            "Eraser Mode (E only)\n"
            "  Open palm or index finger — erase\n"
            "  Open palm alone never erases outside Eraser tool\n\n"
            "Tools: V Pointer  B/1 Pen  2–5 Shapes  T Text  E Eraser  X Clear\n\n"
            "Objects: Delete  Ctrl+D Duplicate  Ctrl+G Group  Ctrl+Shift+G Ungroup  PgUp/PgDn Layer\n"
            "Edit: Z / Ctrl+Z Undo   Y / Ctrl+Y Redo   S Save PNG\n"
            "Brush: + / -   Eraser size: [ / ]   (also +/- when eraser tool active)\n\n"
            "Window: F Fullscreen  H Help  Q / Esc Quit\n\n"
            "Text tool: select T, type text, Enter to commit, Esc to cancel."
        )
        text.setFont(app_font(12))
        text.setWordWrap(True)
        layout.addWidget(text)


class AirBoardApplication:
    def __init__(self):
        self._state = AppState(eraser_size=settings.DEFAULT_ERASER_SIZE)
        self._app = QApplication(sys.argv)
        load_poppins()
        self._app.setStyleSheet(load_stylesheet())
        self._app.setFont(app_font(14))
        self._window = MainWindow()
        self._processor = FrameProcessor(self._state)
        self._help = HelpDialog(self._window)
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self._bind_signals()
        self._bind_shortcuts()

    def _bind_signals(self):
        w = self._window
        w.tool_selected.connect(self._on_tool)
        w.color_selected.connect(self._on_color)
        w.brush_changed.connect(self._on_brush)
        w.clear_requested.connect(self._on_clear)
        w.undo_requested.connect(self._on_undo)
        w.redo_requested.connect(self._on_redo)
        w.save_requested.connect(self._on_save)
        w.text_committed.connect(self._on_text_committed)
        w.text_cancelled.connect(self._on_text_cancelled)
        w.help_toggled.connect(self._toggle_help)
        w.fullscreen_toggled.connect(self._toggle_fullscreen)

    def _bind_shortcuts(self):
        w = self._window
        QShortcut(QKeySequence("Q"), w, self._app.quit)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), w, self._escape)
        QShortcut(QKeySequence("F"), w, self._toggle_fullscreen)
        QShortcut(QKeySequence("H"), w, self._toggle_help)
        QShortcut(QKeySequence("X"), w, self._on_clear)
        QShortcut(QKeySequence("S"), w, self._on_save)
        QShortcut(QKeySequence("Z"), w, self._on_undo)
        QShortcut(QKeySequence("Y"), w, self._on_redo)
        QShortcut(QKeySequence("Ctrl+Z"), w, self._on_undo)
        QShortcut(QKeySequence("Ctrl+Y"), w, self._on_redo)
        QShortcut(QKeySequence("+"), w, lambda: self._on_size_delta(1))
        QShortcut(QKeySequence("-"), w, lambda: self._on_size_delta(-1))
        QShortcut(QKeySequence("["), w, lambda: self._on_eraser_delta(-5))
        QShortcut(QKeySequence("]"), w, lambda: self._on_eraser_delta(5))
        QShortcut(QKeySequence("E"), w, lambda: self._on_tool(tools.ERASER))
        QShortcut(QKeySequence("V"), w, lambda: self._on_tool(tools.SELECT))
        QShortcut(QKeySequence("B"), w, lambda: self._on_tool(tools.FREEHAND))
        QShortcut(QKeySequence("T"), w, lambda: self._on_tool(tools.TEXT))
        QShortcut(QKeySequence(Qt.Key.Key_Delete), w, self._on_delete_selected)
        QShortcut(QKeySequence("Ctrl+D"), w, self._on_duplicate_selected)
        QShortcut(QKeySequence("Ctrl+G"), w, self._on_group_selected)
        QShortcut(QKeySequence("Ctrl+Shift+G"), w, self._on_ungroup_selected)
        QShortcut(QKeySequence(Qt.Key.Key_PageUp), w, lambda: self._on_layer(1))
        QShortcut(QKeySequence(Qt.Key.Key_PageDown), w, lambda: self._on_layer(-1))
        for key, tool in tools.KEY_MAP.items():
            QShortcut(QKeySequence(chr(key)), w, lambda t=tool: self._on_tool(t))

    def _escape(self):
        if self._state.text_input_active:
            self._window.cancel_text_input()
            return
        self._app.quit()

    def _on_tool(self, tool_id: str):
        if tool_id == tools.CLEAR:
            self._on_clear()
            return
        hm = self._processor.hand_manager
        hm.set_tool(tool_id)
        self._processor.manipulation.set_tool(tool_id)
        if tool_id in _TOOL_MAP:
            self._state.current_tool = _TOOL_MAP[tool_id]
        self._window.set_tool_checked(tool_id)
        if tool_id == tools.TEXT:
            self._window.start_text_input()
            self._state.text_input_active = True
            self._state.text_draft = ""
        if tool_id == tools.ERASER:
            self._window.show_eraser_hud(self._state.eraser_size)

    def _on_color(self, index: int):
        self._state.selected_color_index = index
        self._processor.hand_manager.set_color_index(index)

    def _on_brush(self, size: int):
        hm = self._processor.hand_manager
        hm.brush_size = size
        self._state.brush_size = size

    def _on_size_delta(self, delta: int):
        if self._state.current_tool == ToolMode.ERASER:
            self._on_eraser_delta(delta)
        else:
            self._on_brush_delta(delta)

    def _on_eraser_delta(self, delta: int):
        hm = self._processor.hand_manager
        size = hm.adjust_eraser(delta)
        self._state.eraser_size = size
        self._window.show_eraser_hud(size)

    def _on_brush_delta(self, delta: int):
        hm = self._processor.hand_manager
        hm.adjust_brush(delta)
        self._state.brush_size = hm.brush_size
        self._window.sync_brush(hm.brush_size)

    def _on_clear(self):
        self._processor.hand_manager.clear_canvas()

    def _on_undo(self):
        self._processor.hand_manager.undo()

    def _on_redo(self):
        self._processor.hand_manager.redo()

    def _on_delete_selected(self):
        self._processor.manipulation.delete_selected()

    def _on_duplicate_selected(self):
        self._processor.manipulation.duplicate_selected()

    def _on_group_selected(self):
        self._processor.manipulation.group_selected()

    def _on_ungroup_selected(self):
        self._processor.manipulation.ungroup_selected()

    def _on_layer(self, delta: int):
        mc = self._processor.manipulation
        if delta > 0:
            mc.layer_forward()
        else:
            mc.layer_backward()

    def _on_save(self):
        path = self._processor.export_png(str(EXPORTS_DIR))
        if path:
            self._window.setWindowTitle(f"AirBoard — Saved {Path(path).name}")

    def _on_text_committed(self, text: str):
        pos = self._processor.hand_manager.pointer_position(self._processor.last_hand_states)
        if pos is None:
            w, h = self._state.current_frame_size
            pos = (w // 4, h // 2)
        self._processor.hand_manager.add_text(text, pos)
        self._state.text_input_active = False
        self._state.text_draft = ""
        self._window.setWindowTitle("AirBoard")

    def _on_text_cancelled(self):
        self._state.text_input_active = False
        self._state.text_draft = ""

    def _toggle_help(self):
        self._state.show_help = not self._state.show_help
        if self._state.show_help:
            self._help.show()
        else:
            self._help.hide()

    def _toggle_fullscreen(self):
        if self._window.isFullScreen():
            self._window.showNormal()
            self._window.resize(settings.DEFAULT_WINDOW_WIDTH, settings.DEFAULT_WINDOW_HEIGHT)
            self._state.is_fullscreen = False
        else:
            self._window.showFullScreen()
            self._state.is_fullscreen = True

    def _tick(self):
        avail_w, avail_h = self._window.camera_view.available_size()
        result = self._processor.process(avail_w, avail_h)
        if result is None:
            return
        self._window.bind_state(
            result.current_tool,
            result.color_index,
            result.brush_size,
            result.eraser_size,
            result.left_mode,
            result.right_mode,
            result.frame,
            self._state.text_draft,
            self._state.text_input_active,
            result.selection_props,
        )

    def run(self) -> int:
        self._window.show()
        self._timer.start(33)
        try:
            return self._app.exec()
        finally:
            self._processor.close()
