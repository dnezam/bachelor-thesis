import copy


class Snapper:
    """Implement undo/redo functionality for arbitrary objects

    Attributes
    ----------
    _snapshots : list[object]
        Keeps track of all snapshots
    _current_snapshot : int
        Keeps track of current snapshot
    _last_valid : int
        Keeps track of the latest valid snapshot
    _history_size : int
        Keeps track of how many snapshots to store in total
    """

    def __init__(self, history_size: int):
        """
        Parameters
        ----------
        history_size : int
            Maximum history size. Should be larger or equal to 2. Default: 10

        Raises
        ------
        ValueError
            If history_size is less than 2
        """
        if history_size < 2:
            raise ValueError(f"history_size should be at least 2.")
        self._snapshots = [None] * history_size  # https://stackoverflow.com/a/10712044
        self._current_snapshot = -1
        self._last_valid = -1
        self._history_size = history_size

    def create_snapshot(self, obj) -> None:
        """Creates and stores a new snapshot.

        Parameters
        ----------
        obj
            Object which should be snapshot
        """
        # We already have _history_size many valid snapshots
        if self._current_snapshot == self._history_size - 1:
            # https://stackoverflow.com/a/23903661
            self._snapshots.append(copy.deepcopy(obj))
            # Set the last self._history_size snapshots as the new snapshot list
            self._snapshots = self._snapshots[-self._history_size:]
            # No need to change _current_snapshot, as it already points to the last element
        else:
            self._current_snapshot += 1
            self._snapshots[self._current_snapshot] = copy.deepcopy(obj)

        self._last_valid = self._current_snapshot

    def undo(self):
        """Returns a copy of previous snapshot, which becomes the current one.

        Raises
        -----
        ValueError
            If there is no previous snapshot
        """
        if self._current_snapshot <= 0:
            raise ValueError("Cannot undo: No previous snapshot available.")

        self._current_snapshot -= 1
        return copy.deepcopy(self._snapshots[self._current_snapshot])

    def redo(self):
        """Returns a copy of the next snapshot, which becomes the current one.

        Raises
        -----
        ValueError
            If there is no next valid snapshot
        """
        assert self._current_snapshot < len(self._snapshots)
        if self._current_snapshot >= self._last_valid:
            raise ValueError("Cannot redo: No valid next snapshot available.")

        self._current_snapshot += 1
        return copy.deepcopy(self._snapshots[self._current_snapshot])

    def restore(self):
        """Returns a copy of the current snapshot

        Raises
        ------
        ValueError
            If there is no current valid snapshot
        """
        assert len(self._snapshots) == self._history_size
        assert self._current_snapshot < self._history_size
        if self._current_snapshot == -1:
            raise ValueError("Cannot restore: No valid current snapshot available.")

        return copy.deepcopy(self._snapshots[self._current_snapshot])


