import copy

from backend.builtin_function import BuiltinFunction
from backend.custom_function import CustomFunction
from backend.function import Function


class Functions:
    """Names and keeps track of all functions, both built-in and custom functions."""

    def __init__(self):
        self._builtin: dict[str, BuiltinFunction] = {}
        self._custom: dict[str, CustomFunction] = {}
        self._next_id_custom: int = 0

    def __str__(self):
        return (f"Builtins: {list(self._builtin.keys())}\n"
                f"Custom: { {k: str(v.function_signature) for k, v in self._custom.items()} }")

    def get_custom_names(self) -> list[str]:
        """Returns a list of the names of all custom functions"""
        return list(self._custom.keys())

    def get_builtins(self) -> dict[str, BuiltinFunction]:
        """Returns a map from the names of built-in functions to their respective implementation. (Includes all built-in
        functions in the system)"""
        return copy.deepcopy(self._builtin)

    def get_all_functions(self) -> dict[str, Function]:
        """Returns a map from the names of functions to their respective implementation. (Includes all functions, both
        built-in and custom)"""
        return self._builtin | self._custom

    def is_valid_function(self, function_name: str) -> bool:
        """Returns whether a function with the name ``function_name`` exists"""
        return function_name in self.get_all_functions()

    def get_function(self, function_name: str) -> Function:  # NOTE: Do we really want to return a reference here?
        """Returns stored function with name ``function_name``

        Raises
        ------
        KeyError
            If function ``function_name`` does not exist
        """
        return self.get_all_functions()[function_name]

    def add_function(self, f: CustomFunction) -> str:
        """Stores the user-defined function f and returns the name it was stored under."""
        function_name = f"f{self._next_id_custom}"
        self._custom[f"f{self._next_id_custom}"] = f  # NOTE: Should we really store a reference here?
        self._next_id_custom += 1
        return function_name

    def replace_builtins(self, builtins: dict[str, BuiltinFunction]) -> None:
        """Updates the map from names to built-in functions with the contents of argument ``builtins``"""
        self._builtin = copy.deepcopy(builtins)

    def delete_function(self, function_name: str) -> None:
        """Deletes the user-defined function ``function_name``

        Raises
        -------
        KeyError
            If function_name is not a valid user-defined function
        """
        del self._custom[function_name]
