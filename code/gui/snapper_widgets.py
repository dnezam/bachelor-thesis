from PyQt5.QtWidgets import QPushButton

from gui import singletons

"""
In general, a snapshot is created at the end of a method that causes a change to State or applying in SelectedManager.
If undo/redo is not possible, nothing happens.

rebuild_gui() is used to make sure that the internal state and GUI are consistent with each other
"""


def undo_was_clicked():
    try:
        singletons.state, singletons.selected_manager.applying = singletons.app_snapper.undo()
        singletons.rebuild_gui()
    except ValueError:
        pass


def redo_was_clicked():
    try:
        singletons.state, singletons.selected_manager.applying = singletons.app_snapper.redo()
        singletons.rebuild_gui()
    except ValueError:
        pass


class UndoWidget(QPushButton):
    """Undo button"""
    def __init__(self):
        super().__init__("Undo")
        self.setFixedWidth(50)
        self.clicked.connect(undo_was_clicked)


class RedoWidget(QPushButton):
    """Redo button"""
    def __init__(self):
        super().__init__("Redo")
        self.setFixedWidth(50)
        self.clicked.connect(redo_was_clicked)
