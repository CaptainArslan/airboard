"""PySide6 application entry and main loop."""

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel

from src.app.frame_processor import FrameProcessor
from src.config import settings
from src.drawing import tools
from src.ui.qt.main_window import MainWindow
from src.ui.qt.theme import load_poppins, load_stylesheet, app_font


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AirBoard Help")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        text = QLabel(
            "Window\n"
            "  Q / Esc — Quit\n"
            "  F — Toggle fullscreen\n"
            "  H — Toggle this help\n\n"
            "Tools\n"
            "  1 Freehand   2 Line   3 Rectangle\n"
            "  4 Circle     5 Arrow  E Eraser\n"
            "  X Clear canvas\n\n"
            "Brush:  + / - \n\n"
            "Gestures\n"
            "  Index finger — Draw\n"
            "  Index + middle — Pointer\n"
            "  Open palm — Eraser"
        )
        text.setFont(app_font(12))
        text.setWordWrap(True)
        layout.addWidget(text)


class QtApplication:
    def __init__(self):
        self._app = QApplication(sys.argv)
        load_poppins()
        self._app.setStyleSheet(load_stylesheet())
        self._app.setFont(app_font(14))
        self._window = MainWindow()
        self._processor = FrameProcessor()
        self._help = HelpDialog(self._window)
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._bind_shortcuts()
        self._bind_signals()

    def _bind_signals(self):
        w = self._window
        w.tool_selected.connect(self._on_tool)
        w.color_selected.connect(self._on_color)
        w.brush_changed.connect(self._on_brush)
        w.clear_requested.connect(self._on_clear)
        w.help_toggled.connect(self._toggle_help)
        w.fullscreen_toggled.connect(self._toggle_fullscreen)

    def _bind_shortcuts(self):
        w = self._window
        QShortcut(QKeySequence("Q"), w, self._app.quit)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), w, self._app.quit)
        QShortcut(QKeySequence("F"), w, self._toggle_fullscreen)
        QShortcut(QKeySequence("H"), w, self._toggle_help)
        QShortcut(QKeySequence("X"), w, self._on_clear)
        QShortcut(QKeySequence("+"), w, lambda: self._on_brush_delta(1))
        QShortcut(QKeySequence("-"), w, lambda: self._on_brush_delta(-1))
        QShortcut(QKeySequence("E"), w, lambda: self._on_tool(tools.ERASER))
        for key, tool in tools.KEY_MAP.items():
            QShortcut(QKeySequence(chr(key)), w, lambda t=tool: self._on_tool(t))

    def _on_tool(self, tool_id: str):
        if tool_id == tools.CLEAR:
            self._on_clear()
            return
        self._processor.hand_manager.set_tool(tool_id)
        self._window.set_tool_checked(tool_id)

    def _on_color(self, index: int):
        self._processor.hand_manager.set_color_index(index)

    def _on_brush(self, size: int):
        hm = self._processor.hand_manager
        hm.brush_size = size
        for hand in hm._hands.values():
            hand.brush_size = size

    def _on_brush_delta(self, delta: int):
        hm = self._processor.hand_manager
        hm.adjust_brush(delta)
        self._window._sync_brush_ui(hm.brush_size)

    def _on_clear(self):
        self._processor.hand_manager.clear_canvas()

    def _toggle_help(self):
        if self._help.isVisible():
            self._help.hide()
        else:
            self._help.show()

    def _toggle_fullscreen(self):
        if self._window.isFullScreen():
            self._window.showNormal()
            self._window.resize(settings.DEFAULT_WINDOW_WIDTH, settings.DEFAULT_WINDOW_HEIGHT)
        else:
            self._window.showFullScreen()

    def _tick(self):
        avail_w, avail_h = self._window._webcam.available_size()
        result = self._processor.process(avail_w, avail_h)
        if result is None:
            return
        self._window.bind_state(
            result.current_tool,
            result.color_index,
            result.brush_size,
            result.left_mode,
            result.right_mode,
            result.frame,
        )

    def run(self) -> int:
        self._window.show()
        self._timer.start(33)
        try:
            return self._app.exec()
        finally:
            self._processor.close()


def main() -> int:
    return QtApplication().run()
