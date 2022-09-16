from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QInputDialog, QHBoxLayout, QPushButton

from gui import singletons
from gui.helper_functions import str_to_pvalue
from gui.helper_widgets import CellWidget, WidgetCollection
from backend.helper_type import PValue


class ListCollection(WidgetCollection):
    """Implements a collection of list widgets"""
    def __init__(self):
        super().__init__("Lists")

    def create_was_clicked(self):
        list_name = singletons.state.create_list()
        self.create_list_widget(list_name)
        singletons.app_snapper.create_snapshot()

    def create_list_widget(self, list_name: str):
        list_widget = ListWidgetWithDelete(list_name)
        self._widget_collection.addWidget(list_widget)
        singletons.selected_manager.watch_widget(list_widget)

    def rebuild(self):
        self.clear_widget_collection()
        for list_name in singletons.state.get_list_names():
            self.create_list_widget(list_name)


class ListWidgetWithDelete(QWidget):
    """List widget with a delete button (to delete this list)"""

    leftClicked = pyqtSignal(str)
    rightClicked = pyqtSignal(str)
    modified = pyqtSignal(str)
    deleted = pyqtSignal(str)

    def __init__(self, list_name: str):
        self._list_name = list_name
        super().__init__()

        layout = QHBoxLayout()

        delete_button = QPushButton()
        delete_button.setText("Del")
        delete_button.setFixedWidth(30)
        delete_button.clicked.connect(self.delete_was_clicked)
        layout.addWidget(delete_button)

        list_widget = ListWidget(list_name)
        layout.addWidget(list_widget)

        self.setLayout(layout)

    def delete_was_clicked(self):
        singletons.state.delete_list(self._list_name)
        # Why emit -> deleteLater is (probably) fine:
        # https://www.qtforum.de/viewtopic.php?t=15897
        # https://stackoverflow.com/questions/19863629/does-deletelater-wait-for-all-pending-signals-to-be-delivered
        self.deleted.emit(self._list_name)
        self.deleteLater()
        singletons.app_snapper.create_snapshot()

    def was_modified(self):
        self.modified.emit(self._list_name)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.leftClicked.emit(self._list_name)
        elif ev.button() == Qt.RightButton:
            self.rightClicked.emit(self._list_name)


class ListWidget(WidgetCollection):
    """A list widget is a collection of list element widgets"""
    def __init__(self, list_name: str):
        self._list_name = list_name

        super().__init__(list_name)

        # create elements based on state
        list_value = singletons.state.get_list(list_name)
        for i in range(len(list_value)):
            list_element_widget = ListElementWithInsertWidget(self._list_name, i)
            self._widget_collection.addWidget(list_element_widget)

    def create_was_clicked(self):  # Append
        self.create_list_element(len(self._widget_collection))

    def list_element_was_deleted(self, index: int):
        # https://stackoverflow.com/questions/70893947/how-to-get-list-of-widgets-in-pyqt
        # Update indices of subsequent elements
        for i in range(self._widget_collection.count()):
            widget = self._widget_collection.itemAt(i).widget()
            new_index = (widget.list_index - 1) if widget.list_index > index else widget.list_index
            widget.update_index(new_index)

    def create_list_element(self, index: int):
        # TODO: Maybe we should destroy this object after use
        # https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QInputDialog.html#more
        text, ok = QInputDialog().getText(self, "New list element", "Enter the value for the new list element")
        if ok and text:
            # Update indices of subsequent elements
            for i in range(self._widget_collection.count()):
                widget = self._widget_collection.itemAt(i).widget()
                new_index = (widget.list_index + 1) if widget.list_index >= index else widget.list_index
                widget.update_index(new_index)

            singletons.state.insert_list_element(self._list_name, str_to_pvalue(text), index)
            list_element_widget = ListElementWithInsertWidget(self._list_name, index)
            self._widget_collection.insertWidget(index, list_element_widget)
            singletons.app_snapper.create_snapshot()


class ListElementWithInsertWidget(QWidget):
    """+ button (for insertion) together with a list element"""
    def __init__(self, list_name: str, list_index: int):
        self.list_index = list_index
        super().__init__()

        layout = QHBoxLayout()

        insert_button = QPushButton("+")
        insert_button.setFixedWidth(30)
        insert_button.clicked.connect(self.insert_was_clicked)
        self._list_element = ListElementWidget(list_name, list_index)

        layout.addWidget(insert_button)
        layout.addWidget(self._list_element)
        self.setLayout(layout)

    def insert_was_clicked(self):
        self.parent().create_list_element(self.list_index)

    def update_index(self, new_index: str):
        self.list_index = new_index
        self._list_element.update_index(new_index)


class ListElementWidget(CellWidget):
    """Widget representing the value of a list element"""
    def __init__(self, list_name: str, list_index: int):
        # NOTE: Check for valid inputs?
        self._list_name = list_name
        self._list_index = list_index

        super().__init__(f"{self._list_name}[{self._list_index}]")

    def get_value(self):
        return singletons.state.get_list_element(self._list_name, self._list_index)

    def value_was_edited(self):
        value: PValue = str_to_pvalue(self._valueEdit.text())
        singletons.state.update_list_element(self._list_name, value, self._list_index)
        self.parent().parent().parent().was_modified()
        singletons.app_snapper.create_snapshot()

    # NOTE: Order of operations in delete could become problematic/cause bugs
    def delete_was_clicked(self):
        singletons.state.delete_list_element(self._list_name, self._list_index)
        self.parent().parent().list_element_was_deleted(self._list_index)
        self.parent().parent().parent().was_modified()
        self.parent().deleteLater()
        singletons.app_snapper.create_snapshot()

    def update_index(self, new_index: str):
        self._list_index = new_index
        self._update_title()

    def _update_title(self):
        self.setTitle(f"{self._list_name}[{self._list_index}]")
