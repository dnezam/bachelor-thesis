# https://www.stefaanlippens.net/circular-imports-type-hints-python.html
from __future__ import annotations
from typing import TYPE_CHECKING

from gui.temp_widget import TemporaryCollection

if TYPE_CHECKING:
    from gui.list_widget import ListCollection
    from gui.register_widget import RegisterCollection

from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout, QWidget, QLabel, QPushButton
)

from gui import singletons


class SelectedManager:
    """Keeps tracks of all operations related to selecting/selected values.

    Notes
    -----
    Since many different components can be selected, we set up the SelectedManager, which knows which components are
    selected and can thus orchestrate the GUI appropriately. For example, if Apply is clicked, the next selected element
    is the function to be applied. By having the SelectedManager keep track of this, the implementation of Apply
    becomes easier.
    """
    APPLY_PROMPT = "Select a function to be applied."

    def __init__(self):
        self.register_collection: RegisterCollection | None = None
        self.list_collection: ListCollection | None = None
        self.selected_collection: SelectedCollection = SelectedCollection()
        self.temporary_collection: TemporaryCollection | None = None
        self.applying: bool = False

    def register_register_collection(self, register_collection: RegisterCollection):
        self.register_collection = register_collection

    def register_list_collection(self, list_collection: ListCollection):
        self.list_collection = list_collection

    def register_temporary_collection(self, temporary_collection: TemporaryCollection):
        self.temporary_collection = temporary_collection

    def create_widget(self, identifier: str):
        if singletons.state.is_valid_register(identifier):
            self.register_collection.create_register_widget(identifier)
        elif singletons.state.is_valid_list(identifier):
            self.list_collection.create_list_widget(identifier)
        elif singletons.state.is_valid_temporary(identifier):
            self.temporary_collection.create_temp_widget(identifier)
        else:
            assert False, f"Unknown identifier {identifier}"

    def clear_all(self):
        self.selected_collection.clear_all()

    def apply_was_clicked(self):
        if not self.applying:  # We don't want to create multiple snapshots if applying is already True
            self.set_applying(True)
            singletons.app_snapper.create_snapshot()

    def watch_widget(self, widget):
        # widget needs to have signals leftClicked, rightClicked, modified and deleted
        widget.leftClicked.connect(self.widget_was_left_clicked)
        widget.rightClicked.connect(self.widget_was_right_clicked)
        widget.modified.connect(self.value_was_modified)
        widget.deleted.connect(self.identifier_was_deleted)

    def widget_was_left_clicked(self, identifier: str):
        if self.applying:
            result_identifier = singletons.state.apply(identifier, True)
            self.create_widget(result_identifier)
            self.selected_collection.clear_all()
            self.set_applying(False)
        else:
            selected_index = singletons.state.select(identifier, True)
            self.selected_collection.add(selected_index)

        singletons.app_snapper.create_snapshot()

    def widget_was_right_clicked(self, identifier: str):
        if self.applying:
            result_identifier = singletons.state.apply(identifier, False)
            self.create_widget(result_identifier)
            self.selected_collection.clear_all()
            self.set_applying(False)
        else:
            selected_index = singletons.state.select(identifier, False)
            self.selected_collection.add(selected_index)

        singletons.app_snapper.create_snapshot()

    def value_was_modified(self):
        self.selected_collection.update_all_labels()

    def rebuild_collection(self):
        self.selected_collection.rebuild()

    def identifier_was_deleted(self):
        self.rebuild_collection()

    def set_applying(self, b: bool):
        self.applying = b
        singletons.rebuild_prompt()


class SelectedCollection(QGroupBox):
    """Displays all selected values"""

    def __init__(self):
        super().__init__("Selected")
        outer_layout = QHBoxLayout()

        self._widget_collection = QHBoxLayout()
        outer_layout.addLayout(self._widget_collection)

        unselect_all_button = QPushButton("Unselect All")
        unselect_all_button.setFixedWidth(80)
        unselect_all_button.clicked.connect(self.unselect_all)
        outer_layout.addWidget(unselect_all_button)

        self.setLayout(outer_layout)

    def add(self, selected_index: int):
        selected_element_widget = SelectedElementWidget(selected_index)
        self._widget_collection.addWidget(selected_element_widget)

    def unselect(self, selected_index: int):
        singletons.state.unselect(selected_index)

        # https://stackoverflow.com/questions/70893947/how-to-get-list-of-widgets-in-pyqt
        for i in range(self._widget_collection.count()):
            widget = self._widget_collection.itemAt(i).widget()

            # Without this guard we might access the deleted selected item in update_label()
            if widget.selected_index == selected_index:
                continue

            new_index = (widget.selected_index - 1) if widget.selected_index > selected_index else widget.selected_index
            widget.selected_index = new_index

        singletons.app_snapper.create_snapshot()

    def clear_all(self):
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self._widget_collection.count())):
            self._widget_collection.itemAt(i).widget().deleteLater()

    def unselect_all(self):
        self.clear_all()
        singletons.state.unselect_all()
        singletons.app_snapper.create_snapshot()

    def update_all_labels(self):
        for i in range(self._widget_collection.count()):
            widget = self._widget_collection.itemAt(i).widget()
            widget.update_label()

    def rebuild(self):
        self.clear_all()

        selected = singletons.state.get_selected()
        for i in range(len(selected)):
            self.add(i)


class SelectedElementWidget(QWidget):
    """Widget representing a selected element together with an unselect button"""
    def __init__(self, selected_index: int):
        self.selected_index = selected_index
        super().__init__()

        layout = QHBoxLayout()
        self._label = QLabel()
        self.update_label()
        layout.addWidget(self._label)

        unselect_button = QPushButton("Unselect")
        unselect_button.clicked.connect(self.unselect_was_clicked)
        layout.addWidget(unselect_button)

        self.setLayout(layout)

    def update_label(self):
        name, is_variable = singletons.state.get_selected()[self.selected_index]
        value = singletons.state.get_value(name)
        self._label.setText(f"{[name]}: {value} ({'variable' if is_variable else 'constant'})")

    def unselect_was_clicked(self):
        # Remove from singletons.state, update other indices accordingly and remove widget
        self.parent().unselect(self.selected_index)
        self.deleteLater()
