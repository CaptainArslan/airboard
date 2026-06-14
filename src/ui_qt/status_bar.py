"""Bottom status bar."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.drawing import tools


class BottomStatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("BottomStatusBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)

        self._hints = QLabel(
            "Draw: index finger  |  Pointer: two fingers  |  "
            "Erase: open palm  |  [ ] eraser size  |  Q/Esc: quit  |  F: fullscreen"
        )
        self._hints.setObjectName("BottomBar")
        layout.addWidget(self._hints)

        layout.addStretch()

        self._tool_label = QLabel("Tool: Freehand")
        self._tool_label.setObjectName("BottomBar")
        self._size_label = QLabel("")
        self._size_label.setObjectName("BottomBar")
        layout.addWidget(self._tool_label)
        layout.addSpacing(16)
        layout.addWidget(self._size_label)

    def update_tool_info(self, current_tool: str, brush_size: int, eraser_size: int):
        label = tools.LABELS.get(current_tool, current_tool)
        self._tool_label.setText(f"Tool: {label}")
        if current_tool == tools.ERASER:
            self._size_label.setText(f"Size: {eraser_size}px")
        else:
            self._size_label.setText(f"Brush: {brush_size}px")
