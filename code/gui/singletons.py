from PyQt5.QtWidgets import QLabel

from gui.app_snapper import AppSnapper
from gui.function_widget import CustomFunctionCollection
from gui.list_widget import ListCollection
from gui.register_widget import RegisterCollection
from gui.selected_widget import SelectedManager
from gui.temp_widget import TemporaryCollection
from backend.state import State

# This file allows the sharing of variables between different files.

state: State | None = None
selected_manager: SelectedManager | None = None
prompt: QLabel | None = None
register_collection: RegisterCollection | None = None
list_collection: ListCollection | None = None
custom_function_collection: CustomFunctionCollection | None = None
temporary_collection: TemporaryCollection | None = None
app_snapper: AppSnapper | None = None


# https://stackoverflow.com/questions/13034496/using-global-variables-between-files
def initialize():
    global state, selected_manager, prompt, register_collection, list_collection, \
        custom_function_collection, temporary_collection, app_snapper
    state = State()
    selected_manager = SelectedManager()
    prompt = QLabel()
    register_collection = RegisterCollection()
    list_collection = ListCollection()
    custom_function_collection = CustomFunctionCollection()
    temporary_collection = TemporaryCollection()
    app_snapper = AppSnapper()
    app_snapper.create_snapshot()


def rebuild_prompt():
    """Update the text of the prompt"""
    if selected_manager.applying:
        prompt.setText(SelectedManager.APPLY_PROMPT)
    else:
        prompt.setText(state.current_mode())


def rebuild_gui():
    """Rebuilds all visible elements in the GUI that can change throughout the program

    Notes
    -----
    Call this if the state has changed significantly/in an unknown way.
    """
    # Rebuild prompt
    rebuild_prompt()

    # Rebuild register collection
    register_collection.rebuild()

    # Rebuild list collection
    list_collection.rebuild()

    # Rebuild custom function collection
    custom_function_collection.rebuild()

    # Rebuild selected collection
    selected_manager.rebuild_collection()

    # Rebuild temporary collection (only needed if we are in demonstration mode)
    # NOTE: The scenario where we only want to clear the shown temporaries and not get a list of current temps (for
    #  example because there is no valid demonstration anymore due to undo) does not occur: If we switch from
    #  interactive to demonstration mode, we create a snapshot where no temporaries are displayed in the GUI. Hence,
    #  it is not possible to go from demonstration back to interactive mode with (invalid) temporaries shown in
    #  the GUI using undo, as we will restore the snapshot where we are in demonstration mode without any generated
    #  temporaries on the way to interactive mode.
    if state.is_demonstration():
        temporary_collection.rebuild()
