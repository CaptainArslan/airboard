"""Right status sidebar."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from src.ui_qt.widgets import HandStatusCard, ObjectPropertiesCard, SectionHeader, ShortcutRow, SHORTCUTS


class RightPanel(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setObjectName("RightSidebar")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel = QWidget()
        panel.setObjectName("SidebarPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        layout.addWidget(SectionHeader("Hand Status"))
        layout.addSpacing(8)
        self.left_card = HandStatusCard("Left Hand")
        self.right_card = HandStatusCard("Right Hand")
        layout.addWidget(self.left_card)
        layout.addWidget(self.right_card)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line2)

        layout.addWidget(SectionHeader("Object Properties"))
        layout.addSpacing(8)
        self.properties_card = ObjectPropertiesCard()
        layout.addWidget(self.properties_card)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        layout.addWidget(SectionHeader("Shortcuts"))
        layout.addSpacing(12)
        for key, label in SHORTCUTS:
            layout.addWidget(ShortcutRow(key, label))
            layout.addSpacing(8)
        layout.addStretch()
        self.setWidget(panel)
