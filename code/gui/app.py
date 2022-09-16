# https://www.pythonguis.com/tutorials/creating-your-first-pyqt-window/
import sys
import traceback

from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
)

from gui import singletons
from gui.apply_widget import ApplyWidget
from gui.function_widget import BuiltinCollection
from gui.snapper_widgets import UndoWidget, RedoWidget
from gui.synthesis_control_widgets import SynthesisControlWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PROTOTYPE - Function synthesis in Algot")

        # https://stackoverflow.com/questions/37304684/qwidgetsetlayout-attempting-to-set-qlayout-on-mainwindow-which-already/63268752#63268752
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # https://www.qtcentre.org/threads/61483-How-to-fix-error-Must-construct-a-QApplication-before-a-QWidget
        singletons.initialize()

        # Initialize first row
        first_row = QHBoxLayout()
        main_layout.addLayout(first_row)
        first_row.addWidget(UndoWidget())
        first_row.addWidget(RedoWidget())

        # For debugging
        print_button = QPushButton("DEBUGGING: Print state")
        print_button.clicked.connect(lambda: print(f"State:\n{singletons.state}\n"))
        first_row.addWidget(print_button)

        # Initialize second row
        second_row = QHBoxLayout()
        main_layout.addLayout(second_row)

        # TODO: Update text accordingly in the rest of the program
        second_row.addWidget(singletons.prompt)
        singletons.prompt.setText(singletons.state.current_mode())

        second_row.addWidget(ApplyWidget())

        # Register collection
        main_layout.addWidget(singletons.register_collection)
        singletons.selected_manager.register_register_collection(singletons.register_collection)

        # List collection
        main_layout.addWidget(singletons.list_collection)
        singletons.selected_manager.register_list_collection(singletons.list_collection)

        # Built-in collection
        builtin_collection = BuiltinCollection()
        main_layout.addWidget(builtin_collection)

        # Custom function collection
        main_layout.addWidget(singletons.custom_function_collection)  # TODO: Test this

        # Selected collection
        selected_collection = singletons.selected_manager.selected_collection
        main_layout.addWidget(selected_collection)

        # Synthesis control widget
        synthesis_control_widget = SynthesisControlWidget()
        main_layout.addWidget(synthesis_control_widget)

        # Temporary collection
        temporary_collection = singletons.temporary_collection
        main_layout.addWidget(temporary_collection)
        singletons.selected_manager.register_temporary_collection(temporary_collection)


# Catching exceptions raised in QApplication: https://stackoverflow.com/a/55819545
def excepthook(exc_type, exc_value, exc_tb):
    # NOTE: Using the tb = ... approach from SO, because with traceback.print_exception things got printed in the wrong
    #  order - EXPLANATION: We printed to stderr AND stdout, leading to problems (https://stackoverflow.com/a/34046924)
    tb = " ".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"The following error has occurred:\n{tb}")
    print("Attempting to restore snapshot...")
    singletons.state, singletons.selected_manager.applying = singletons.app_snapper.restore()
    singletons.rebuild_gui()
    print("Restored snapshot.")


def run_gui():
    sys.excepthook = excepthook
    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec()
