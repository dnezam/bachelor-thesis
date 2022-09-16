import copy

from backend.helper_type import PValue
from backend.helpers import get_supported_element_types, infer_value_type, all_equal
from backend.unify import List, Num, Bool, Var


def _check_list_type(value: list[PValue]) -> None:
    """
    Check whether type of list `value` is supported

    Notes
    -----
    While infer_value_type would not allow lists of strings (since we have no valid type for string), it might allow a
    type like List(List(Num())), i.e. a list of list of numbers, something that the system cannot handle. These are the
    cases we have to eliminate.

    Raises
    ------
    TypeError
        If `value` has an unsupported list type
    """
    value_type = infer_value_type(value)
    match value_type:
        case List(Num()) | List(Bool()) | List(Var(_)):
            return
        case _:
            raise TypeError(f"{value_type} is an unsupported list type")


def _check_list_elements(value: list[PValue]) -> None:
    """
    Checks whether all elements inside `value` have the same type and whether the type of the elements is supported

    Raises
    ------
    TypeError
        If `value` has an unsupported list type or contains elements with different types
    """
    _check_list_type(value)
    element_types = [infer_value_type(elem) for elem in value]
    if not all_equal(element_types):
        raise TypeError(f"{value} contains different types of values")


def _check_type_add_value(list_value: list[PValue], value: PValue) -> None:
    """
    Check whether value has the correct type to be added to list list_name

    Raises
    ------
    TypeError
        If type of `value` is incompatible with types supported by `list_name`
    """
    supported_element_types = get_supported_element_types(list_value)
    value_type = infer_value_type(value)
    if value_type not in supported_element_types:
        raise TypeError(f"Type {value_type} is incompatible with types supported by {list_value}: "
                        f"({supported_element_types})")


class Lists:
    """Names and keeps track of all lists, which contain "primary" values like int, float and bool"""

    def __init__(self):
        self._lists: dict[str, list[PValue]] = {}
        self._next_id: int = 0

    def __str__(self):
        return f"List assignments: {self._lists}, next id: {self._next_id}"

    def create_list(self, value: list[PValue]) -> str:
        """Create new list with entries specified in ``value``. Returns the name of the newly created list.

        Returns
        -------
        str
            Name of newly created list

        Raises
        ------
        TypeError
            If value contains different types of values or unsupported elements
        """
        _check_list_elements(value)
        list_name: str = f"l{self._next_id}"
        self._lists[list_name] = copy.deepcopy(value)  # Making sure that sub-objects are not exposed
        self._next_id += 1
        return list_name

    def update_list(self, list_name: str, value: list[PValue]) -> None:
        """Update list ``list_name`` with entries specified in ``value``

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If value contains different types of values or unsupported elements
        """
        self._check_list_name(list_name)
        _check_list_elements(value)
        self._lists[list_name] = copy.deepcopy(value)

    # NOTE: Do we really want to return a reference here? Could result in leaking of sub-objects, leading to potentially
    #  unexpected side effects
    def get_list(self, list_name: str) -> list[PValue]:
        """Return list ``list_name``

        Raises
        ------
        KeyError
            If list_name is invalid
        """
        return self._lists[list_name]

    def get_names(self) -> list[str]:
        """Return a list of the names of all lists"""
        return list(self._lists.keys())

    def get_list_element(self, list_name: str, index: int) -> PValue:
        """Return element at index ``ìdx`` in list ``list_name``

        Raises
        ------
        KeyError
            If list_name is invalid
        IndexError
            If index is out-of-bounds
        """
        return self._lists[list_name][index]

    def is_valid_list(self, list_name: str) -> bool:
        """Returns whether a list with the name ``list_name`` actually exists"""
        return list_name in self._lists

    def delete_list(self, list_name: str) -> None:
        """Delete list ``list_name``

        Raises
        ------
        ValueError
            If list_name is invalid
        """
        self._check_list_name(list_name)
        del self._lists[list_name]

    def append_to_list(self, list_name: str, value: PValue) -> int:
        """Append element ``value`` to ``list_name``

        Returns
        -------
        int
            Index of added element

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If the type of the passed value is incompatible with the type of the values in list_name
        """
        self._check_list_name(list_name)
        _check_type_add_value(self.get_list(list_name), value)
        self._lists[list_name].append(value)
        return len(self._lists[list_name]) - 1

    def insert_list_element(self, list_name: str, value: PValue, index: int) -> None:
        """Insert element ``value`` at position ``index`` into ``list_name``

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If the type of the passed value is incompatible with the type of the values in list_name
        """
        self._check_list_name(list_name)
        _check_type_add_value(self.get_list(list_name), value)
        self._lists[list_name].insert(index, value)

    def update_list_element(self, list_name: str, value: PValue, index: int) -> None:
        """Update element at position ``index`` in ``list_name`` to ``value``

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If the type of the passed value is incompatible with the type of the values in list_name
        IndexError
            If index is invalid for list_name
        """
        self._check_list_name(list_name)
        list_value = self.get_list(list_name)
        # Value to be updated should not be considered when determining the type of the list. This allows us to update
        # a singleton list: [True] -> [0]
        _check_type_add_value(list_value[:index] + list_value[index+1:], value)
        self._lists[list_name][index] = value

    def delete_list_element(self, list_name: str, index: int) -> None:
        """Delete element at position ``index`` in ``list_name``

        Raises
        ------
        ValueError
            If list_name is invalid
        IndexError
            If index is invalid for list_name
        """
        self._check_list_name(list_name)
        self._lists[list_name].pop(index)

    def _check_list_name(self, list_name: str) -> None:
        """Checks whether ``list_name`` exists

        Raises
        ------
        ValueError
            If list_name is invalid, i.e. list with name list_name does not exist
        """
        if list_name not in self._lists:
            raise ValueError(f"{list_name} does not exist")
