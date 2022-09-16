import copy

from backend.builtin_function import BuiltinFunction
from backend.demonstration import Demonstration
from backend.exceptions import ModeError, NoneAsFunArg, AlgotRuntimeError
from backend.functions import Functions
from backend.helper_type import PValue, Value, Path
from backend.lists import Lists
from backend.registers import Registers

from backend.helpers import infer_value_type

from backend.unify import Num, Bool, List

# Integer representation of different modes
BETWEEN = -1  # Mode to interact with state in between examples
INTERACTIVE = 0  # Mode to interact with state without restrictions
DEMONSTRATION = 1  # Mode during function synthesis

# NOTE: If a comment contains "backend" without it making sense, it could be that it should actually be "refactor"
#  instead (caused by renaming the package from refactor to backend)
# NOTE: If you return something to the user, pay attention whether you return a mutable reference
# NOTE: Don't forget to clear selected if needed! (think about whether we should clear selected when we switch between
#   modes
# TODO: Fix the exceptions: Separate classes, add documentation (e.g., using ValueError can lead us to accidentally
#  catching the wrong exceptions)
# TODO: Deal with the cases where we have function calls which are different, but equivalent to public functions we
#  have (e.g. private get_value vs public get_value)

# Type for taking a snapshot of the state attribute. Snapshots are used to make sure we don't end up in an inconsistent
# state
StateSnap = tuple[Registers, Lists, Functions, Demonstration | None, int, list[tuple[str, bool]], int]


class State:
    """State required for the backend implementation"""

    def __init__(self):
        # NOTE: If we add any attributes, make sure to add it to _state_copy and state_restore
        # TODO: Make "If we add any attributes, make sure to add it to _state_copy and state_restore" irrelevant by
        #  using something like metaprogramming (i.e. the functions get a list of attributes themselves)
        self._registers: Registers = Registers()
        self._lists: Lists = Lists()
        self._functions: Functions = Functions()
        self._current_demonstration: Demonstration | None = None

        self._mode: int = 0
        self._selected: list[tuple[str, bool]] = []  # [(name, is_variable), ...]
        self._unique_id = 0

        # Initialize built-in functions
        result: dict[str, BuiltinFunction] = {}
        for name, signature in BuiltinFunction.supported_operations.items():
            result[name] = BuiltinFunction(name, signature, self._get_unique_id())

        self._functions.replace_builtins(result)

    def __str__(self):
        return (f"Registers: {self._registers}\n"
                f"Lists: {self._lists}\n"
                f"Functions: {self._functions}\n"
                f"Current demonstration: "
                f"{'None' if self._current_demonstration is None else self._current_demonstration}\n"
                f"Mode: {self.current_mode()}\n"
                f"Selected: {self._selected}\n")

    # "Public" methods
    def get_builtins(self) -> dict[str, BuiltinFunction]:
        """Return map from names to built-in functions supported by the system"""
        return self._functions.get_builtins()

    def get_value(self, name: str) -> Value:
        """Get value of ``name``

        Raises
        ------
        ValueError
            If name could not be found
        """
        # TODO: It might be a good idea to make sure that we don't accidentally return sub objects instead of copies of
        #  them (otherwise there is the risk of unexpected side-effects)
        try:
            return self._registers.get_register(name)
        except KeyError:
            pass
        try:
            return self._lists.get_list(name)
        except KeyError:
            pass
        try:
            return self._functions.get_function(name)
        except KeyError:
            pass
        try:
            return self._current_demonstration.get_temp(name)
        except KeyError:
            pass
        raise ValueError(f"Could not find {name}")

    def get_computation(self, name: str) -> list[str]:
        """Returns the expression which calculates the value of the temporary ``name``

        Raises
        ------
        ValueError
            If name is not a valid temporary
        """
        if not self.is_valid_temporary(name):
            raise ValueError(f"{name} is not a valid temporary")

        return self._current_demonstration.get_temp_computation(name)

    # Modes
    def is_interactive(self) -> bool:
        """Returns whether the state is currently in interactive mode"""
        return self._mode == INTERACTIVE

    def is_demonstration(self) -> bool:
        """Returns whether the state is currently in demonstration mode"""
        return self._mode == DEMONSTRATION

    def is_between(self) -> bool:
        """Returns whether the state is currently in between mode"""
        return self._mode == BETWEEN

    def current_mode(self) -> str:
        """Returns the name of the current mode as a string"""
        if self.is_interactive():
            return "INTERACTIVE"
        elif self.is_demonstration():
            return "DEMONSTRATION"
        elif self.is_between():
            return "BETWEEN"
        else:
            return "INVALID"

    # Selected
    def get_selected(self) -> list[tuple[str, bool]]:
        """Returns a copy of the list of currently selected names"""
        return copy.deepcopy(self._selected)

    # Registers
    def create_register(self, value: PValue = 0) -> str:
        """Creates a new register with passed value ``value``. Returns name of newly created register.

        Raises
        ------
        TypeError
            If type of `value` is unsupported (i.e. not Num or Bool)
        """
        return self._registers.create_register(value)

    def delete_register(self, register: str) -> None:
        """Deletes ``register``

        Notes
        -----
        When a register is deleted, its occurrences within self._selected are deleted as well. If the state is in
        demonstration/between mode, the register will only be deleted if it is not in use. See thesis for a more
        detailed explanation.

        Raises
        ------
        KeyError
            If register does not exist
        [Demonstration/Between mode] ValueError
            If register is still in use
        """
        if self.is_interactive():
            self._registers.delete_register(register)
            self._delete_selected(register)
        elif self.is_demonstration() or self.is_between():
            if self._is_used(register):
                raise ValueError(f"Cannot delete {register}, as it is still used")
            self._registers.delete_register(register)
            self._delete_selected(register)
        else:
            assert False, f"Invalid mode {self._mode}"

    def update_register(self, register: str, value: PValue) -> None:
        """Update ``register`` with value ``value``

        Notes
        -----
        If the state is in demonstration mode, the register can only be updated if it is not in use.

        Raises
        ------
        ValueError
            If register does not exist
        TypeError
            If type of `value` is unsupported (i.e. not Num or Bool)
        [Demonstration mode]
            If register is still in use
        """
        if self.is_interactive() or self.is_between():
            self._registers.update_register(register, value)
        elif self.is_demonstration():
            if self._is_used(register):
                raise ValueError(f"Cannot update {register}, as it is still used")
            self._registers.update_register(register, value)
        else:
            assert False, f"Invalid mode {self._mode}"

    def get_register(self, register_name: str) -> PValue:
        """Returns the value of the register ``register_name``

        Raises
        ------
        KeyError
            If register does not exist
        """
        return self._registers.get_register(register_name)

    def get_register_names(self) -> list[str]:
        """Returns a list of the names of all registers"""
        return self._registers.get_names()

    def is_valid_register(self, register_name: str) -> bool:
        """Returns whether ``register_name`` is a valid register."""
        return self._registers.is_valid_register(register_name)

    # Lists
    def create_list(self, value: list[PValue] | None = None) -> str:
        """Create new list with entries specified in ``value``. If no value is given, creates an empty list.
        Returns the name of the newly created list.

        Returns
        -------
        str
            Name of newly created list

        Raises
        ------
        TypeError
            If value contains different types of values or unsupported elements
        """
        if value is None:
            value = []
        return self._lists.create_list(value)

    def get_list(self, list_name: str) -> list[PValue]:
        """Return list ``list_name``

        Raises
        ------
        KeyError
            If list_name is invalid
        """
        return self._lists.get_list(list_name)

    def get_list_names(self) -> list[str]:
        """Return a list of the names of all lists"""
        return self._lists.get_names()

    def get_list_element(self, list_name: str, list_index: int) -> PValue:
        """Return element at index ``list_index`` in list ``list_name``

        Raises
        ------
        KeyError
            If list_name is invalid
        IndexError
            If index is out-of-bounds
        """
        return self._lists.get_list_element(list_name, list_index)

    def update_list(self, list_name: str, value: list[PValue]) -> None:
        """Update list ``list_name`` with entries specified in ``value``

        Notes
        -----
        If the state is in demonstration mode, list_name can only be updated if it is not in use.

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If value contains different types of values or unsupported elements
        [Demonstration mode] ValueError
            If list is still in use
        """
        if self.is_interactive() or self.is_between():
            self._lists.update_list(list_name, value)
        elif self.is_demonstration():
            if self._is_used(list_name):
                raise ValueError(f"Cannot update {list_name}, as it is still used")

    def delete_list(self, list_name: str) -> None:
        """Delete list ``list_name``

        Notes
        -----
        When a list is deleted, its occurrences within self._selected are deleted as well. If the state is in
        demonstration/between mode, the list will only be deleted if it is not in use. See thesis for a more
        detailed explanation.

        Raises
        ------
        ValueError
            If list_name is invalid
        [Demonstration/Between mode] ValueError
            If list is still in use
        """
        if self.is_interactive():
            self._lists.delete_list(list_name)
            self._delete_selected(list_name)
        elif self.is_demonstration() or self.is_between():
            if self._is_used(list_name):
                raise ValueError(f"Cannot delete {list_name}, since it is still used")
            self._lists.delete_list(list_name)
            self._delete_selected(list_name)
        else:
            assert False, f"Invalid mode {self._mode}"

    def append_to_list(self, list_name: str, value: PValue = 0) -> int:
        """Append element ``value`` to ``list_name``

        Returns
        -------
        int
            Index of added element

        Notes
        -----
        If the state is in demonstration mode, list_name can only be updated if it is not in use.

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If the type of the passed value is incompatible with the type of the values in list_name
        [Demonstration mode] ValueError
            If list is still in use
        """
        if self.is_interactive() or self.is_between():
            return self._lists.append_to_list(list_name, value)
        elif self.is_demonstration():
            if self._is_used(list_name):
                raise ValueError(f"Cannot change {list_name}, since it is still used")
            return self._lists.append_to_list(list_name, value)
        else:
            assert False, f"Invalid mode {self._mode}"

    def insert_list_element(self, list_name: str, value: PValue, index: int) -> None:
        """Insert element ``value`` at position ``index`` into ``list_name``

        Notes
        -----
        If the state is in demonstration mode, list_name can only be updated if it is not in use.

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If the type of the passed value is incompatible with the type of the values in list_name
        [Demonstration mode] ValueError
            If list is still in use
        """
        if self.is_interactive() or self.is_between():
            self._lists.insert_list_element(list_name, value, index)
        elif self.is_demonstration():
            if self._is_used(list_name):
                raise ValueError(f"Cannot change {list_name}, since it is still used")
            self._lists.insert_list_element(list_name, value, index)
        else:
            assert False, f"Invalid mode {self._mode}"

    def update_list_element(self, list_name: str, value: PValue, index: int) -> None:
        """Update element at position ``index`` in ``list_name`` to ``value``

        Notes
        -----
        If the state is in demonstration mode, list_name can only be updated if it is not in use.

        Raises
        ------
        ValueError
            If list_name is invalid
        TypeError
            If the type of the passed value is incompatible with the type of the values in list_name
        IndexError
            If index is invalid for list_name
        [Demonstration mode] ValueError
            If list is still in use
        """
        if self.is_interactive() or self.is_between():
            self._lists.update_list_element(list_name, value, index)
        elif self.is_demonstration():
            if self._is_used(list_name):
                raise ValueError(f"Cannot change {list_name}, since it is still used")
            self._lists.update_list_element(list_name, value, index)
        else:
            assert False, f"Invalid mode {self._mode}"

    def delete_list_element(self, list_name: str, index: int) -> None:
        """Delete element at position ``index`` in ``list_name``

        Notes
        -----
        If the state is in demonstration mode, list_name can only be updated if it is not in use.

        Raises
        ------
        ValueError
            If list_name is invalid
        IndexError
            If index is invalid for list_name
        [Demonstration mode] ValueError
            If list is still in use
        """
        if self.is_interactive() or self.is_between():
            self._lists.delete_list_element(list_name, index)
        elif self.is_demonstration():
            if self._is_used(list_name):
                raise ValueError(f"Cannot change {list_name}, since it is still used")
            self._lists.delete_list_element(list_name, index)
        else:
            assert False, f"Invalid mode {self._mode}"

    def is_valid_list(self, list_name: str) -> bool:
        """Returns whether a list with the name ``list_name`` actually exists"""
        return self._lists.is_valid_list(list_name)

    # Function
    def get_custom_function_names(self) -> list[str]:
        """Returns a list of the names of all custom functions"""
        return self._functions.get_custom_names()

    def create_function(self) -> None:
        """Changes the mode of the state from interactive to demonstration mode

        Raises
        ------
        ValueError
            If state is in demonstration or between mode.
        """
        if self.is_interactive():
            self._set_demonstration()
            self._current_demonstration = Demonstration()
        elif self.is_demonstration() or self.is_between():
            raise ValueError("Cannot create a new function in demonstration/between mode")
        else:
            assert False, f"Invalid mode {self._mode}"

    def delete_function(self, function_name: str) -> None:
        """Deletes the user-defined function ``function_name``

        Raises
        -------
        KeyError
            If function_name is not a valid user-defined function
        [Demonstration/Between mode] ValueError
            If state is in demonstration or between mode
        """
        if self.is_interactive():
            self._functions.delete_function(function_name)
        elif self.is_demonstration() or self.is_between():
            raise ValueError("Cannot delete function in demonstration/between mode")  # TODO: Why not?
        else:
            assert False, f"Invalid mode {self._mode}"

    # Interaction/Demonstration
    def select(self, identifier: str, is_variable: bool) -> int:
        """Select ``identifier`` (i.e. register, list, function or temp) as a variable or constant.

        Returns
        -------
        int
            Position of selected name in self._selected list
        """
        match self.current_mode():
            case "INTERACTIVE" | "BETWEEN":
                return self._select_interactive_between(identifier)
            case "DEMONSTRATION":
                return self._select_demonstration(identifier, is_variable)
            case _:
                assert False, "Invalid mode"

    def unselect(self, idx: int) -> None:
        """Removes element at position `idx` in the selected list

        Raises
        ------
        IndexError
            If idx is invalid
        """
        del self._selected[idx]

    def unselect_all(self) -> None:
        """Unselects all elements"""
        self._selected = []

    def apply(self, function_name: str, is_variable: bool) -> str:
        """Represents applying ``function_name`` to the currently selected elements in the context of function synthesis

        Returns
        -------
        str
            Name of temporary (demonstration mode) or register/list (interactive or between mode) in which the function
            application was stored in

        Raises
        -------
        NoSolutionError
            If unification failed (while generating the function)
        ValueError
            If final unification result of function synthesis contains an unsupported type OR
            If function name could not be found OR
            If args is empty even though the function expects at least one argument OR
            If expected types of arguments don't match received types of arguments OR
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init) OR
        IndexError
            If next instruction doesn't exist, even though it is not a recursive application
        [Interactive/Between mode] TypeError
            If type of `value` is unsupported (i.e. not Num or Bool) OR
            Value is a list and contains different types of values or unsupported elements
        [Demonstration] ValueError
            If the generated instruction does not match the expected instruction
        """
        state_snap = self._state_copy()
        try:
            match self.current_mode():
                case "INTERACTIVE" | "BETWEEN":
                    return self._apply_interactive_between(function_name)
                case "DEMONSTRATION":
                    return self._apply_demonstration(function_name, is_variable)
                case _:
                    assert False, "Invalid mode"
        except Exception as e:  # https://stackoverflow.com/a/4992124
            # NOTE: This is probably too coarse grained, but will probably work. Consider making it more fine-grained.
            print(f"Encountered error {e}. Restoring snapshot.")
            self._state_restore(state_snap)
            raise e

    def recurse(self) -> str:
        """Represents recursion applied to the currently selected elements in the context of function synthesis

        Returns
        -------
        str
            Name of temporary in which the recursion result is stored

        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        NoSolutionError
            If unification failed (while generating the function)
        ValueError
            If final unification result of function synthesis contains an unsupported type OR
            If function name could not be found OR
            If args is empty even though the function expects at least one argument OR
            If expected types of arguments don't match received types of arguments OR
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init) OR
            If the generated instruction does not match the expected instruction
        IndexError
            If next instruction doesn't exist, even though it is not a recursive application
        """
        self._check_demonstration()
        state_snap = self._state_copy()  # Create a snapshot that we can restore in case something goes wrong
        try:
            # TODO: Think about whether we should first calculate expr or result
            # NOTE: Pulled expr assignment before result for testing
            expr = ["self"] + self._add_to_function_context(self._selected)
            result: Value | None = self._get_apply_result("self")

            temp_name = self._current_demonstration.add_recursive_application(expr, result)

            self.unselect_all()
            return temp_name
        except Exception as e:  # https://stackoverflow.com/a/4992124
            # NOTE: This is probably too coarse grained, but will probably work. Consider making it more fine-grained.
            print(f"Encountered error {e}. Restoring snapshot.")
            self._state_restore(state_snap)
            raise e

    def branch(self) -> None:
        """Represents branching on the currently selected element in the context of function synthesis

        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        ValueError
            If not exactly one element is selected OR
            If currently selected element is definitely a constant OR
            If the generated instruction does not match the expected instruction
        TypeError
            If selected element is not of type Bool
        """
        self._check_demonstration()
        state_snap = self._state_copy()
        try:
            if len(self._selected) != 1:
                raise ValueError(f"Expected exactly one element to be selected. Number of selected elements: "
                                 f"{len(self._selected)}")

            if not self._selected[0][1]:  # if selected name is not variable
                raise ValueError(f"Cannot branch on something that is definitely a constant.")

            cond_value = self.get_value(self._selected[0][0])
            selected_type = infer_value_type(cond_value)
            if selected_type != Bool():
                raise TypeError(f"Expected {self._selected[0]} to be of type Bool(), and not {selected_type}")

            cond_name = self._add_to_function_context(self._selected)[0]  # needed if we want to branch on an input

            self._current_demonstration.branch(cond_name, cond_value)
            self.unselect_all()
        except Exception as e:  # https://stackoverflow.com/a/4992124
            # NOTE: This is probably too coarse grained, but will probably work. Consider making it more fine-grained.
            print(f"Encountered error {e}. Restoring snapshot.")
            self._state_restore(state_snap)
            raise e

    def ret(self) -> tuple[list[Path], str]:
        """Represents returning the currently selected element in the context of function synthesis

        Returns
        -------
        tuple[list[Path], str]
            If there are remaining examples, the first entry of the tuple contains a list of these remaining examples.
            If there are no more remaining examples, the second entry of the tuple contains the name of the newly
            generated function

        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        ValueError
            If not exactly one element is selected OR
            If the generated instruction does not match the expected instruction OR
            If final unification result of function synthesis contains an unsupported type
        NoSolutionError
            If unification during function generation failed
        """
        self._check_demonstration()
        state_snap = self._state_copy()
        try:
            if len(self._selected) != 1:
                raise ValueError(f"Expected exactly one element to be selected. Number of selected elements: "
                                 f"{len(self._selected)}")

            ret_name = self._add_to_function_context(self._selected)[0]  # We know this is a singleton list

            self._current_demonstration.ret(ret_name)
            self.unselect_all()

            remaining_examples = self._current_demonstration.remaining_examples()
            function_name = None

            if remaining_examples:  # There are still remaining examples
                self._current_demonstration.prepare()
                self._set_between()
            else:  # We are done, generate the function
                f = self._current_demonstration.generate_function(self._get_unique_id())
                function_name = self._functions.add_function(f)

                self._current_demonstration = None
                self._set_interactive()

            return remaining_examples, function_name
        except Exception as e:  # https://stackoverflow.com/a/4992124
            # NOTE: This is probably too coarse grained, but will probably work. Consider making it more fine-grained.
            print(f"Encountered error {e}. Restoring snapshot.")
            self._state_restore(state_snap)
            raise e

    def cont(self) -> None:
        """Switches from between mode to demonstration mode. Should be called when the user is done with modifying the
        example and wants to demonstrate the next example

        Raises
        ------
        ModeError
            If current mode is not between mode
        """
        self._check_between()
        self._set_demonstration()

    def is_valid_temporary(self, temp_name: str) -> bool:
        """Returns whether ``temp_name`` is the name of a temporary"""
        return self.is_demonstration() and self._current_demonstration.is_valid_temp(temp_name)

    def get_temp_names(self) -> list[str]:
        """Return a list with the names of all temporaries"""
        return self._current_demonstration.get_temp_names()

    # "Private" methods
    def _get_unique_id(self) -> int:
        """Returns a unique id.

        Notes
        -----
        Mainly used to generate unique ids for functions, allowing us to reliably compare them for "equality".
        """
        unique_id = self._unique_id
        self._unique_id += 1
        return unique_id

    # OPT: Replace check and similar functions with one function + list of modes to check
    def _select_interactive_between(self, name: str) -> int:
        """Select ``name`` in interactive or between mode

        Returns
        -------
        int
            Position of selected name in self._selected

        Raises
        ------
        ModeError
            If current mode is neither interactive nor between mode
        ValueError
            If name is not a valid name
        """
        self._check_interactive_between()
        if not self._is_valid_name(name):
            raise ValueError(f"{name} is not a valid name")

        self._selected.append((name, False))
        return len(self._selected) - 1

    def _select_demonstration(self, name: str, is_variable: bool) -> int:
        """Select ``name`` as variable or constant in demonstration mode

        Returns
        -------
        int
            Position of selected name in self._selected

        Notes
        -----
        is_variable indicates whether the selected name should be regarded as a constant or variable.
        When selecting a temporary, is_variable is ignored in general (e.g. in apply) and set to True - the assumption
        is that they might change (for example if its value depends on its inputs)


        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        ValueError
            If name is not a valid name
        """
        # Returns the position in the selected list
        self._check_demonstration()
        if not self._is_valid_name(name):
            raise ValueError(f"{name} is not a valid name")

        if self._current_demonstration.is_valid_temp(name):
            is_variable = True

        self._selected.append((name, is_variable))
        return len(self._selected) - 1

    def _apply_interactive_between(self, function_name: str) -> str:
        """Applies ``function_name`` to selected arguments in interactive mode

        Returns
        -------
        str
            Name of register/list in which the function application was stored in

        Raises
        ------
        ModeError
            If current mode is neither interactive nor between mode
        NoSolutionError
            If unification failed (while generating the function)
        ValueError
            If final unification result of function synthesis contains an unsupported type OR
            If function name could not be found OR
            If args is empty even though the function expects at least one argument OR
            If expected types of arguments don't match received types of arguments OR
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init)
        IndexError
            If next instruction doesn't exist, even though it is not a recursive application
        TypeError
            If type of `value` is unsupported (i.e. not Num or Bool) OR
            Value is a list and contains different types of values or unsupported elements
        """
        self._check_interactive_between()
        result = self._get_apply_result(function_name)
        identifier = self._store_value(result)
        self.unselect_all()
        return identifier

    def _apply_demonstration(self, function_name: str, is_variable: bool) -> str:
        """Applies ``function_name`` to selected arguments in demonstration mode

        Returns
        -------
        str
            Temporary in which the function application was stored in

        Notes
        -----
        is_variable indicates whether the function is a constant or variable (i.e. an input). This way, we can also
        synthesis functions like map (takes a function as input and applies it to every element in a list).

        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        NoSolutionError
            If unification failed (while generating the function)
        ValueError
            If final unification result of function synthesis contains an unsupported type OR
            If function name could not be found OR
            If args is empty even though the function expects at least one argument OR
            If expected types of arguments don't match received types of arguments OR
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init) OR
            If the generated instruction does not match the expected instruction
        IndexError
            If next instruction doesn't exist, even though it is not a recursive application
        """
        self._check_demonstration()
        result: Value = self._get_apply_result(function_name)  # Also functions as type checking

        # OPT: Maybe we can rewrite this to be a bit cleaner
        expr = self._add_to_function_context(self._selected + [(function_name, is_variable)])  # Function is added last
        # In expression, function is first, thus we need to shift the last element to the first position:
        # Method 2: https://www.geeksforgeeks.org/python-shift-last-element-to-first-position-in-list/
        expr.insert(0, expr.pop())

        identifier = self._current_demonstration.add_function_application(expr, result)

        self.unselect_all()
        return identifier

    def _check_interactive(self) -> None:
        """Check whether state is in interactive mode

        Raises
        ------
        ModeError
            If current mode is not interactive mode
        """
        if not self.is_interactive():
            raise ModeError("Check for being in interactive mode failed")

    def _check_demonstration(self) -> None:
        """Check whether state is in demonstration mode

        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        """
        if not self.is_demonstration():
            raise ModeError("Check for being in demonstration mode failed")

    def _check_between(self) -> None:
        """Check whether state is in between mode

        Raises
        ------
        ModeError
            If current mode is not between mode
        """
        if not self.is_between():
            raise ModeError("Check for being in between mode failed")

    def _check_interactive_between(self) -> None:
        """Check whether state is in interactive or between mode

        Raises
        ------
        ModeError
            If current mode is neither interactive nor between mode
        """
        if not (self.is_interactive() or self.is_between()):
            raise ModeError("Check for being in interactive or between mode failed")

    def _set_interactive(self) -> None:
        """Set mode to interactive"""
        self._mode = INTERACTIVE

    def _set_demonstration(self) -> None:
        """Set mode to demonstration"""
        self._mode = DEMONSTRATION

    def _set_between(self) -> None:
        """Set mode to between"""
        self._mode = BETWEEN

    def _is_valid_name(self, name: str) -> bool:
        """Return whether ``name`` is a valid name"""
        return (self._registers.is_valid_register(name) or
                self._lists.is_valid_list(name) or  # TODO We have equivalent public methods; Why not use those instead?
                self._functions.is_valid_function(name) or
                (self.is_demonstration() and self._current_demonstration.is_valid_name(name)))

    def _is_used(self, name: str) -> bool:
        """Returns whether ``name`` is used as an input

        Raises
        ------
        ModeError
            If current mode is not demonstration mode
        """
        self._check_demonstration()
        return self._current_demonstration.is_used(name)

    def _get_values(self, names: list[str]) -> list[Value]:
        """Returns the values of the names in ``names``

        Raises
        ------
        ValueError
            If a name could not be found
        """
        return [self.get_value(name) for name in names]

    def _store_value(self, value: Value) -> str:  # in interactive state
        """Stores ``value`` in state.

        Returns
        -------
        str
            Name of register/list in which value was stored

        Raises
        ------
        TypeError
            If type of `value` is unsupported (i.e. not Num or Bool) OR
            Value is a list and contains different types of values or unsupported elements
        """
        value_type = infer_value_type(value)
        match value_type:
            case Num() | Bool():
                return self.create_register(value)
            case List(_):
                return self.create_list(value)
            case _:
                assert False, "Trying to store something besides Num, Bool, List should not be possible"

    def _delete_selected(self, name: str) -> None:
        """Remove ``name`` from self._selected"""
        self._selected = [item for item in self._selected if item[0] != name]

    def _get_apply_result(self, function_name: str) -> Value | None:
        """Applies `function_name` to selected objects and returns the result.

        Raises
        ------
        NoSolutionError
            If unification failed (while generating the function)
        ValueError
            If final unification result of function synthesis contains an unsupported type OR
            If function name could not be found OR
            If args is empty even though the function expects at least one argument OR
            If expected types of arguments don't match received types of arguments OR
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init)
        IndexError
            If next instruction doesn't exist, even though it is not a recursive application
        """
        try:  # Get function
            if function_name == "self":
                f = self._current_demonstration.generate_function(self._get_unique_id())
            else:
                f = self._functions.get_function(function_name)
        except KeyError:
            raise ValueError(f"Could not find function {function_name}")

        try:  # Apply function
            selected_names = [name for name, _ in self._selected]
            result = f.compute(self._get_values(selected_names))
        except (TypeError, AlgotRuntimeError) as e:
            raise ValueError(e)
        except IndexError as e:  # Could not finish f.compute
            if function_name == "self":  # Could not finish recursive call due to missing instructions
                return None
            else:
                raise e
        except NoneAsFunArg:  # If a function receives None as argument, it returns None itself
            return None

        return result

    def _add_to_function_context(self, names: list[tuple[str, bool]]) -> list[str]:
        """Given a list of names + whether they are a variable (``names``), adds the entries to the function context and
        returns a list of the corresponding names in the function context
        """
        context_name = []

        for name, is_variable in names:
            if self._current_demonstration.is_valid_temp(name):
                context_name.append(name)
                continue

            if is_variable:
                input_name = self._current_demonstration.add_input(name)
                context_name.append(input_name)
            else:
                value = self.get_value(name)
                const_name = self._current_demonstration.add_constant(value)
                context_name.append(const_name)

        return context_name

    # TODO: Maybe rewrite _state_copy and _state_restore by accessing all the instance attributes of an object
    #  (Notion of instance attributes: https://dzone.com/articles/python-class-attributes-vs-instance-attributes)
    def _state_copy(self) -> StateSnap:
        """Return tuple with a copy of all of State's attributes"""
        state_tuple = (self._registers, self._lists, self._functions, self._current_demonstration, self._mode,
                       self._selected, self._unique_id)
        return copy.deepcopy(state_tuple)

    def _state_restore(self, state_snap: StateSnap) -> None:
        """Update current attributes with passed snapshot ``state_snap``"""
        (self._registers, self._lists, self._functions, self._current_demonstration, self._mode, self._selected,
         self._unique_id) = state_snap
