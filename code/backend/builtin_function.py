# https://www.stefaanlippens.net/circular-imports-type-hints-python.html
import itertools

import backend.exceptions
import backend.helpers as helpers

from backend.function import Function
from backend.helper_type import Value
from backend.unify import Term, Num, App, Bool, List, Var, Fun


class BuiltinFunction(Function):
    """Implements built-in functions.

    Parameters
    ----------
    builtin
        Name of the built-in to be instantiated
    function_signature
        Type signature of function
    unique_id
        Number that should be unique across all functions that exist in the system
    """

    # Set up supported built-ins

    # Define variables to make definition of array_operations slightly more readable
    type_variable_0 = Var(f"{helpers.FUNCTION_TYPE_PREFIX}0")
    list_type_variable_0 = List(type_variable_0)
    type_variable_1 = Var(f"{helpers.FUNCTION_TYPE_PREFIX}1")
    list_type_variable_1 = List(type_variable_1)

    # Function signature: Num -> Num -> Num
    arithmetic_operations: dict[str, Term] = dict(itertools.product(["+", "-", "*", "/", "//", "%"],
                                                                    [App(Num(), App(Num(), Num()))]))

    # Function signature: # Num -> Num -> Bool
    comparison_operations: dict[str, Term] = dict(itertools.product(["==", "!=", ">", "<", ">=", "<="],
                                                                    [App(Num(), App(Num(), Bool()))]))

    # Function signature: # Bool -> Bool -> Bool
    boolean_operations: dict[str, Term] = {
        "and": App(Bool(), App(Bool(), Bool())),
        "or": App(Bool(), App(Bool(), Bool())),
        "not": App(Bool(), Bool())
    }

    # Similar to list functions from Haskell Prelude:
    # https://hackage.haskell.org/package/base-4.16.1.0/docs/Prelude.html
    # More information on cons (and Haskell in general): http://learnyouahaskell.com/starting-out
    list_operations: dict[str, Term] = {
        "len": App(list_type_variable_0, Num()),  # len: [y0] -> Num
        "head": App(list_type_variable_0, type_variable_0),  # head: [y0] -> y0
        "last": App(list_type_variable_0, type_variable_0),  # last: [y0] -> y0
        "tail": App(list_type_variable_0, list_type_variable_0),  # tail: [y0] -> [y0]
        "init": App(list_type_variable_0, list_type_variable_0),  # init: [0y] -> [y0]
        "concat": App(list_type_variable_0,
                      App(list_type_variable_0, list_type_variable_0)),  # concat: [y0] -> [y0] -> [y0]
        "map": App(App(type_variable_0, type_variable_1),
                   App(list_type_variable_0, list_type_variable_1)),  # map: (y0 -> y1) -> [y0] -> [y1]
        "filter": App(App(type_variable_0, Bool()),
                      App(list_type_variable_0, list_type_variable_1)),  # filter: (y0 -> Bool) -> [y0] -> [y0]
        "cons": App(type_variable_0, App(list_type_variable_0, list_type_variable_0))  # cons: y0 -> [y0] -> [y0]
    }

    supported_operations: dict[str, Term] = (arithmetic_operations | comparison_operations | boolean_operations |
                                             list_operations)

    def __init__(self, builtin: str, function_signature: Fun, unique_id: int):
        if builtin not in BuiltinFunction.supported_operations:
            raise ValueError(f"Invalid builtin {builtin}")

        super().__init__(function_signature, unique_id)
        self.builtin: str = builtin

    def compute(self, args: list[Value]) -> Value:
        """Computes and returns the result of the function given the arguments ``args``

        Raises
        ------
        NoneAsFunArg
            If the function receives None as an argument (i.e. None is in args)
        ValueError
            If args is empty even though the function expects at least one argument
        TypeError
            If unification fails (i.e. expected types of arguments don't match received types of arguments)
        AlgotRuntimeError
            If a runtime error occurs while the result is being computed (e.g. ZeroDivisionError, IndexError when
            working with list operations like head, last, tail and init)
        """
        context = self.input_context(args)

        match self.builtin:
            case "+":
                return context["in0"] + context["in1"]
            case "-":
                return context["in0"] - context["in1"]
            case "*":
                return context["in0"] * context["in1"]
            case "/":
                try:
                    return context["in0"] / context["in1"]
                except ZeroDivisionError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot divide by zero")
            case "//":
                try:
                    return context["in0"] // context["in1"]
                except ZeroDivisionError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot do integer division by zero")
            case "%":
                try:
                    return context["in0"] % context["in1"]
                except ZeroDivisionError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot do modulo by zero")
            case "==":
                return context["in0"] == context["in1"]
            case "!=":
                return context["in0"] != context["in1"]
            case ">":
                return context["in0"] > context["in1"]
            case "<":
                return context["in0"] < context["in1"]
            case ">=":
                return context["in0"] >= context["in1"]
            case "<=":
                return context["in0"] <= context["in1"]
            case "and":
                return context["in0"] and context["in1"]
            case "or":
                return context["in0"] or context["in1"]
            case "not":
                return not context["in0"]
            case "len":
                return len(context["in0"])
            case "head":
                # NOTE: Shallow copy (as created by slicing) should be fine here, as lists in the system should only
                #  hold primitive/primary values like ints, floats or bool
                try:
                    return context["in0"][0]
                except IndexError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot get first element of {context['in0']}")
            case "last":
                try:
                    return context["in0"][-1]
                except IndexError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot get last element of {context['in0']}")
            case "tail":
                try:
                    return context["in0"][1:]
                except IndexError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot get tail of {context['in0']}")
            case "init":
                try:
                    return context["in0"][:-1]
                except IndexError:
                    raise backend.exceptions.AlgotRuntimeError(f"Cannot get init of {context['in0']}")
            case "concat":
                return context["in0"] + context["in1"]
            case "map":
                result = []
                for element in context["in1"]:
                    result.append(context["in0"].compute([element]))
                return result
            case "filter":
                result = []
                for element in context["in1"]:
                    if context["in0"].compute([element]):
                        result.append(element)
                return result
            case "cons":
                return [context["in0"]] + context["in1"]
            case _:
                assert False, f"Cannot handle {self.builtin} as builtin"
