from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout, QPushButton, QGroupBox, QLineEdit, QLabel
)


class WidgetCollection(QGroupBox):
    """Collection of widgets together with a + button (to add new widgets)"""
    def __init__(self, group_name: str, parent=None):
        super().__init__(group_name, parent)

        # Setup layout: Widget Collection | + button
        outer_layout = QHBoxLayout()

        self._widget_collection = QHBoxLayout()
        outer_layout.addLayout(self._widget_collection)

        new_button = QPushButton("+")
        new_button.setFixedWidth(30)
        outer_layout.addWidget(new_button)

        self.setLayout(outer_layout)

        # Setup widgets
        new_button.clicked.connect(self.create_was_clicked)

    # Child classes should override this
    def create_was_clicked(self):
        pass

    def clear_widget_collection(self):
        """Remove all widgets from the widget collection"""
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self._widget_collection.count())):
            self._widget_collection.itemAt(i).widget().deleteLater()


class CellWidget(QGroupBox):
    """Widget representing a cell (value that can be edited)"""

    def __init__(self, group_name: str, parent=None):
        super().__init__(group_name, parent)
        # https://stackoverflow.com/questions/36434706/pyqt-proper-use-of-emit-and-pyqtsignal

        # Setup layout
        self._layout_h = QHBoxLayout()

        self._valueEdit = QLineEdit()
        self._valueEdit.setFixedWidth(40)
        self._valueEdit.setText(str(self.get_value()))
        self._layout_h.addWidget(self._valueEdit)

        delete_button = QPushButton()
        delete_button.setText("Del")
        delete_button.setFixedWidth(30)
        self._layout_h.addWidget(delete_button)

        self._layout_h.setAlignment(Qt.AlignLeft)
        self._layout_h.setSpacing(0)
        self.setLayout(self._layout_h)

        # Finish setting up widgets
        self._valueEdit.editingFinished.connect(self.value_was_edited)
        delete_button.clicked.connect(self.delete_was_clicked)

    # Child classes should override this
    def get_value(self):
        """
        Returns the current *internal* value of the cell (not the currently displayed value).
        """
        pass

    # Child classes should override this
    def value_was_edited(self):
        pass

    # Child classes should override this
    def delete_was_clicked(self):
        pass


# https://wiki.qt.io/Clickable_QLabel
# http://codestudyblog.com/cnb2010/1006231406.html
# https://stackoverflow.com/questions/3891465/how-to-connect-pyqtsignal-between-classes-in-pyqt
# https://stackoverflow.com/questions/36434706/pyqt-proper-use-of-emit-and-pyqtsignal
# https://stackoverflow.com/questions/45575626/make-qlabel-clickable
class ClickableLabel(QLabel):
    """Label that can be clicked"""

    leftClicked = pyqtSignal(str)
    rightClicked = pyqtSignal(str)
    # modified and deleted are not used, but required for selected_manager
    modified = pyqtSignal(str)
    deleted = pyqtSignal(str)

    def __init__(self, identifier: str, label_name: str):
        self._identifier = identifier
        super().__init__(label_name)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.leftClicked.emit(self._identifier)
        elif ev.button() == Qt.RightButton:
            self.rightClicked.emit(self._identifier)
