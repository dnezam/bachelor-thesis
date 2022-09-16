from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QInputDialog
)

# References for PyQt
# https://www.pythonguis.com/tutorials/pyqt-signals-slots-events/
# https://www.pythonguis.com/tutorials/pyqt-basic-widgets/
# https://www.pythonguis.com/tutorials/pyqt-layouts/
# https://www.pythonguis.com/tutorials/creating-your-own-custom-widgets/
# https://zetcode.com/gui/pyqt5/customwidgets/
from gui import singletons
from gui.helper_functions import str_to_pvalue
from gui.helper_widgets import WidgetCollection, CellWidget
from backend.helper_type import PValue


class RegisterCollection(WidgetCollection):
    """Collection of register widgets"""
    def __init__(self):
        super().__init__("Registers")

    def create_was_clicked(self):
        # TODO: Maybe we should destroy this object after use or create it once and keep it around
        text, ok = QInputDialog().getText(self, "New register", "Enter the value for the new register")
        if ok and text:
            register_name = singletons.state.create_register(str_to_pvalue(text))
            self.create_register_widget(register_name)
        singletons.app_snapper.create_snapshot()

    def create_register_widget(self, register_name: str):
        register_widget = RegisterWidget(register_name)
        self._widget_collection.addWidget(register_widget)
        singletons.selected_manager.watch_widget(register_widget)

    def rebuild(self):
        self.clear_widget_collection()
        for register in singletons.state.get_register_names():
            self.create_register_widget(register)


class RegisterWidget(CellWidget):
    """Widget representing the value of a register in the state"""

    leftClicked = pyqtSignal(str)
    rightClicked = pyqtSignal(str)
    modified = pyqtSignal(str)
    deleted = pyqtSignal(str)

    def __init__(self, register_name: str):
        # NOTE: Should we add a check whether register_name is valid?
        self._register_name = register_name

        super().__init__(register_name)

    def get_value(self) -> PValue:
        return singletons.state.get_register(self._register_name)

    def value_was_edited(self):
        value: PValue = str_to_pvalue(self._valueEdit.text())
        singletons.state.update_register(self._register_name, value)
        self.modified.emit(self._register_name)
        singletons.app_snapper.create_snapshot()

    def delete_was_clicked(self):
        singletons.state.delete_register(self._register_name)
        self.deleted.emit(self._register_name)
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        self.deleteLater()
        singletons.app_snapper.create_snapshot()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.leftClicked.emit(self._register_name)
        elif ev.button() == Qt.RightButton:
            self.rightClicked.emit(self._register_name)
