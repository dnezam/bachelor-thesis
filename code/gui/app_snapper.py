from backend.state import State
from gui import singletons
from snapper.snapper import Snapper


class AppSnapper:
    """Adapts Snapper into snapshotting everything relevant about app.py: State, and the field applying in
    SelectedManager
    """
    def __init__(self, history_size: int = 100):
        self._snapper = Snapper(history_size)

    def create_snapshot(self) -> None:
        """Create and store snapshot of State and whether the user is trying to apply a function"""
        self._snapper.create_snapshot((singletons.state, singletons.selected_manager.applying))

    def undo(self) -> tuple[State, bool]:
        """Returns a copy of previous snapshot, which becomes the current one.

        Raises
        -----
        ValueError
            If there is no previous snapshot
        """
        return self._snapper.undo()

    def redo(self) -> tuple[State, bool]:
        """Returns a copy of the next snapshot, which becomes the current one.

        Raises
        -----
        ValueError
            If there is no next valid snapshot
        """
        return self._snapper.redo()

    def restore(self) -> tuple[State, bool]:
        """Returns a copy of the current snapshot

        Raises
        ------
        ValueError
            If there is no current valid snapshot
        """
        return self._snapper.restore()
