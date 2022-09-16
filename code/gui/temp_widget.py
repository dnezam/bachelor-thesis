from PyQt5.QtWidgets import (
    QGroupBox, QHBoxLayout
)

from gui import singletons
from gui.helper_widgets import ClickableLabel


class TemporaryCollection(QGroupBox):
    """Widget for representing temporaries"""

    def __init__(self):
        super().__init__("Temporaries")
        self._temporaries_collection = QHBoxLayout()
        self.setLayout(self._temporaries_collection)

    def create_temp_widget(self, identifier: str):
        computation = " ".join(singletons.state.get_computation(identifier))
        label = f"{identifier} = {singletons.state.get_value(identifier)} [{computation}]"
        temp_widget = ClickableLabel(identifier, label)
        singletons.selected_manager.watch_widget(temp_widget)
        self._temporaries_collection.addWidget(temp_widget)

    def clear_all(self):
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self._temporaries_collection.count())):
            self._temporaries_collection.itemAt(i).widget().deleteLater()

    def rebuild(self):
        self.clear_all()
        for temp in singletons.state.get_temp_names():
            self.create_temp_widget(temp)
