from backend.helper_type import PValue
from backend.helpers import infer_value_type
from backend.unify import Num, Bool


def _check_value_type(value: PValue) -> None:
    """Checks whether ``value`` is a supported "primary" value

    Raises
    ------
    TypeError
        If type of value is unsupported (i.e. not Num or Bool)

    Notes
    -----
    Inputs, which the system cannot recognize (e.g. strings), will fail during ``infer_value_type`` with an
    ``AssertionError``
    """
    value_type = infer_value_type(value)
    match value_type:
        case Num() | Bool():
            return
        case _:
            raise TypeError(f"{value_type} is an unsupported register type")


class Registers:
    """Names and keeps track of all registers, which store "primary" values like int, float and bool"""

    def __init__(self):
        self._registers: dict[str, PValue] = {}
        self._next_id: int = 0

    def __str__(self):
        return f"Register assignments: {self._registers}, next id: {self._next_id}"

    def is_valid_register(self, register: str) -> bool:
        """Returns whether ``register`` is a valid register."""
        return register in self._registers

    def create_register(self, value: PValue = 0) -> str:
        """Creates a new register with value ``value``. Returns the name of the newly created register.

        Returns
        -------
        str
            Name of newly created register

        Raises
        ------
        TypeError
            If type of `value` is unsupported (i.e. not Num or Bool)
        """
        _check_value_type(value)
        register_name = f"r{self._next_id}"
        self._registers[register_name] = value
        self._next_id += 1
        return register_name

    def get_register(self, register: str) -> PValue:
        """Returns the value of register ``register``

        Raises
        ------
        KeyError
            If register does not exist
        """
        return self._registers[register]

    def get_names(self) -> list[str]:
        """Returns a list of the names of all registers"""
        return list(self._registers.keys())

    def delete_register(self, register: str) -> None:
        """Deletes register ``register``

        Raises
        ------
        KeyError
            If register does not exist
        """
        del self._registers[register]

    def update_register(self, register: str, value: PValue) -> None:
        """Updates the value of register ``register`` with value ``value``

        Raises
        ------
        ValueError
            If register does not exist

        TypeError
            If type of value is unsupported (i.e. not Num or Bool)
        """
        if not self.is_valid_register(register):
            raise ValueError(f"{register} does not exist")
        _check_value_type(value)
        self._registers[register] = value
