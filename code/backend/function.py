# https://www.stefaanlippens.net/circular-imports-type-hints-python.html
from __future__ import annotations
from typing import TYPE_CHECKING

from backend.exceptions import NoneAsFunArg

if TYPE_CHECKING:
    from backend.helper_type import Value

import backend.helpers as helpers
from backend.unify import Term, unify, NoSolutionError, App, Var, Num, Bool, List


class Function:
    """Basic functionality expected to be supported by functions

    Parameters
    ----------
    function_signature
        Type signature of function
    unique_id
        Number that should be unique across all functions that exist in the system

    Notes
    -----
    This class basically acts as a kind of abstract class. That is, it shouldn't be instantiated directly. Instead, an
    implementation of a function class (e.g. BuiltinFunction) should extend this class and implement compute(self, args)
    in a sensible way.
    unique_id is used to check whether two functions are the same (they are the same iff they have the same unique_id)
    """

    def __init__(self, function_signature: Term, unique_id: int):
        self.function_signature: Term = function_signature
        self.unique_id: int = unique_id  # Needed for reliable comparison

    def __str__(self):
        return str(self.function_signature)  # NOTE: Maybe the string representation should include more information?

    def input_context(self, args: list["Value"]) -> dict[str, "Value"]:
        """
        Checks whether the type of the arguments is valid and returns input context

        Notes
        -----
        The input context is a map from names to values. This allows the function to refer to all values by name.

        Raises
        ------
        NoneAsFunArg
            If the function receives None as an argument (i.e. None is in args)
        ValueError
            If args is empty even though the function expects at least one argument
        TypeError
            If unification fails (i.e. expected types of arguments don't match received types of arguments)
        """
        input_context: dict[str, "Value"] = {}

        if None in args:
            raise NoneAsFunArg(f"Arguments {args} contain None - cannot compute.")

        # Check whether function actually takes any arguments
        match self.function_signature:
            case App(_, _):
                pass
            case Var(_) | Num() | Bool() | List(_):
                return {}
            case _:
                assert False, f"Pattern matching inside input_context failed: received function_signature " \
                              f"{self.function_signature}"

        # Do type checking
        argument_signature = helpers.infer_argument_signature(args)
        function_input_signature = helpers.drop_last_type_app(self.function_signature)
        try:
            unify([(argument_signature, function_input_signature)])
        except NoSolutionError as e:
            raise TypeError(f"Unification failed: {e}")

        # Generate input context
        i = 0
        for argument in args:
            input_context[f"in{i}"] = argument
            i += 1

        return input_context

    # Child classes need to override this
    def compute(self, args: list["Value"]) -> "Value":
        """Computes and returns the result of the function given the arguments ``args``

        Raises
        ------
        NoneAsFunArg
            If the function receives None as an argument (i.e. None is in args)
        ValueError
            If args is empty even though the function expects at least one argument
        TypeError
            If unification fails (i.e. expected types of arguments don't match received types of arguments)

        [CustomFunction] IndexError
            If next instruction doesn't exist (e.g. missing return due to executing compute(args) before function
            synthesis has fully terminated)

        [BuiltinFunction] AlgotRuntimeError
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init)
        """
        pass
