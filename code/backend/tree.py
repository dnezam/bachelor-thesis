from __future__ import annotations
# https://stackoverflow.com/questions/2358045/how-can-i-implement-a-tree-in-python
from backend.helper_type import Instruction, Path


class Tree:
    """Binary tree to keep track of branches presented during examples

    Parameters
    ----------
    path
        Path from root to node to be created.

    Notes
    -----
    Example for path: ["T", "F"] means that from the root, we can reach the node to be created/self by first following
    the "true" branch and then the "false" branch.
    """

    def __init__(self, path: list[str]):
        self._path: Path = path
        self._block: list[Instruction] = []
        self._true: Tree | None = None
        self._false: Tree | None = None

    def get_instruction(self, pos: int) -> Instruction:
        """Return instruction at position ``pos``

        Raises
        ------
        IndexError
            If pos is invalid
        """
        return self._block[pos]

    def append_instruction(self, instr: Instruction) -> None:
        """Append instruction to instruction block"""
        self._block.append(instr)

    def remaining_examples(self) -> list[Path]:
        """
        Returns a list of paths, which represents the (additional) examples required for function synthesis

        Examples
        --------
        [["T", "F"], ["F", "F"]] means that we will need two examples:
        One where the first condition is True and the second False, and another one where both conditions are false.
        """

        true_empty = self._true is None
        false_empty = self._false is None

        if not true_empty and not false_empty:  # Both are not None => Go deeper
            return self._true.remaining_examples() + self._false.remaining_examples()
        elif true_empty and not false_empty:
            return [self._path + ["T"]] + self._false.remaining_examples()
        elif not true_empty and false_empty:
            return self._true.remaining_examples() + [self._path + ["F"]]
        elif true_empty and false_empty:  # Both are None => There is no branching
            return []

    def get_true(self, modify: bool = False) -> Tree:
        """
        Returns child node "true". Creates a new child if it doesn't exist and modify is set to True.

        Raises
        ------
        ValueError
            If "true" child does not exist and modify is False
        """
        if self._true is None:
            if modify:
                self._true = Tree(self._path + ["T"])
            else:
                raise ValueError("true child does not exist + not allowed to create a new child")
        return self._true

    def get_false(self, modify: bool = False) -> Tree:
        """
        Return child node false. Creates a new child if it doesn't exist.

        Raises
        ------
        ValueError
            If "false" child does not exist and modify is False
        """
        if self._false is None:
            if modify:
                self._false = Tree(self._path + ["F"])
            else:
                raise ValueError("false child does not exist + not allowed to create a new child")
        return self._false
