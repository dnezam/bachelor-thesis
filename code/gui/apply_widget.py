from PyQt5.QtWidgets import QPushButton

from gui import singletons


class ApplyWidget(QPushButton):
    """Apply button"""

    def __init__(self):
        super().__init__("Apply")
        self.setFixedWidth(50)
        self.clicked.connect(singletons.selected_manager.apply_was_clicked)
