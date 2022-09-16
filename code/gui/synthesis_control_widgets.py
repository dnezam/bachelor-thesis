from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout

from gui import singletons


def recurse_was_clicked():
    temp_name = singletons.state.recurse()
    singletons.selected_manager.clear_all()
    singletons.selected_manager.set_applying(False)
    singletons.temporary_collection.create_temp_widget(temp_name)
    singletons.app_snapper.create_snapshot()


def branch_was_clicked():
    singletons.state.branch()
    singletons.selected_manager.clear_all()
    singletons.selected_manager.set_applying(False)
    singletons.app_snapper.create_snapshot()


def return_was_clicked():
    paths, function_name = singletons.state.ret()
    singletons.selected_manager.clear_all()
    singletons.selected_manager.set_applying(False)
    singletons.temporary_collection.clear_all()

    if not paths:
        singletons.custom_function_collection.add_function_widget(function_name)
        singletons.prompt.setText(singletons.state.current_mode())
    else:
        singletons.prompt.setText(f"{singletons.state.current_mode()}: Prepare state for a path from {paths} and "
                                  f"press continue.")

    singletons.app_snapper.create_snapshot()


def continue_was_clicked():
    singletons.state.cont()
    singletons.selected_manager.set_applying(False)
    singletons.app_snapper.create_snapshot()


class SynthesisControlWidget(QWidget):
    """Collection of buttons for recursion, branching, returning and continuing"""

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()

        recurse_button = QPushButton("Recurse")
        recurse_button.clicked.connect(recurse_was_clicked)
        layout.addWidget(recurse_button)

        branch_button = QPushButton("Branch")
        branch_button.clicked.connect(branch_was_clicked)
        layout.addWidget(branch_button)

        return_button = QPushButton("Return")
        return_button.clicked.connect(return_was_clicked)
        layout.addWidget(return_button)

        continue_button = QPushButton("Continue")
        continue_button.clicked.connect(continue_was_clicked)
        layout.addWidget(continue_button)

        self.setLayout(layout)
