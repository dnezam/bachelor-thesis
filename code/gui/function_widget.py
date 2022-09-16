from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QPushButton, QWidget
)

from gui import singletons
from gui.helper_widgets import ClickableLabel


class BuiltinCollection(QGroupBox):
    """Displays all built-in functions"""

    def __init__(self):
        super().__init__("Built-in functions")
        builtin_collection = QHBoxLayout()
        builtin_names = list(singletons.state.get_builtins().keys())

        for name in builtin_names:
            label = ClickableLabel(name, name)
            label.setMinimumWidth(30)
            label.setAlignment(Qt.AlignCenter)
            builtin_collection.addWidget(label)
            singletons.selected_manager.watch_widget(label)

        self.setLayout(builtin_collection)


def create_new_function():
    """Call functions required to create a new function"""
    singletons.state.create_function()
    singletons.prompt.setText(singletons.state.current_mode())
    singletons.app_snapper.create_snapshot()


class CustomFunctionCollection(QGroupBox):
    """Displays all user-defined functions"""

    def __init__(self):
        super().__init__("User-defined functions")
        outer_layout = QHBoxLayout()

        self._custom_function_collection = QHBoxLayout()
        outer_layout.addLayout(self._custom_function_collection)

        new_button = QPushButton("+")
        new_button.setFixedWidth(30)
        new_button.clicked.connect(create_new_function)
        outer_layout.addWidget(new_button)

        self.setLayout(outer_layout)

    def add_function_widget(self, function_name: str):
        """Add a widget to CustomFunctionCollection"""
        function_widget = CustomFunctionWidget(function_name)
        self._custom_function_collection.addWidget(function_widget)
        singletons.selected_manager.watch_widget(function_widget.label)

    def clear(self):
        """Remove all widgets (i.e. widgets of user-defined functions) within CustomFunctionCollection"""
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self._custom_function_collection.count())):
            self._custom_function_collection.itemAt(i).widget().deleteLater()

    def rebuild(self):
        """Remove all widgets within CustomFunctionCollection and add widgets for all custom functions in the State"""
        self.clear()
        for f_name in singletons.state.get_custom_function_names():
            self.add_function_widget(f_name)


class CustomFunctionWidget(QWidget):
    """Widget representing a single user-defined function"""

    def __init__(self, function_name: str):
        self._function_name = function_name
        super().__init__()
        outer_layout = QHBoxLayout()

        self.label = ClickableLabel(function_name, function_name)
        self.label.setMinimumWidth(30)
        self.label.setAlignment(Qt.AlignCenter)
        outer_layout.addWidget(self.label)

        delete_button = QPushButton("Del")
        delete_button.setFixedWidth(30)
        delete_button.clicked.connect(self.delete_was_clicked)
        outer_layout.addWidget(delete_button)

        self.setLayout(outer_layout)

    def delete_was_clicked(self):
        """Call functions required to delete a function from the state and GUI"""
        singletons.state.delete_function(self._function_name)
        self.label.deleted.emit(self._function_name)
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        self.deleteLater()
        singletons.app_snapper.create_snapshot()
