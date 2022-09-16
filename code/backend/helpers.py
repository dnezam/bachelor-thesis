# https://www.stefaanlippens.net/circular-imports-type-hints-python.html
from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.helper_type import Value

from backend.unify import Num, Bool, List, Var, Term, alpha_conversion, App

import backend.function as function

ARGUMENT_TYPE_PREFIX = "z"  # Prefix of type variables in argument signature
FUNCTION_TYPE_PREFIX = "y"  # Prefix of type variables in function signature


# From https://docs.python.org/3/library/itertools.html#itertools-recipes
def all_equal(iterable) -> bool:
    """Returns True if all the elements are equal to each other"""
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def infer_value_type(value: "Value") -> Term:
    """
    Given a value, return a term that can be used during unification

    Examples
    --------
    >>> infer_value_type(True)
    Bool()

    Notes
    -----
    - Empty lists always return List(a) - alpha conversion might be required to ensure correctness when combining terms
    - Type of list is determined by its first element. We do not check whether all elements have the same type or
    whether the system actually supports the resulting type of list (e.g. List(List(Num())) might be unsupported)
    """
    match value:
        # Checking for bool needs to happen before checking for int/float, since bool is a subclass of int
        # https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance
        case bool(_):
            return Bool()
        case int(_) | float(_):
            return Num()
        case []:
            return List(Var("a"))
        case [x, *_]:
            return List(infer_value_type(x))
        case function.Function(function_signature=type_signature, unique_id=_):
            return type_signature
        case _:
            assert False, f"Pattern matching in infer_value_type failed for value {value}"


def get_supported_element_types(value: "Value") -> frozenset[Term]:
    """
    Returns set of types of values that can be added to the list `value`.
    Returns empty set if `value` is not a valid list.
    """
    match infer_value_type(value):
        case List(Var(_)):
            return frozenset([Num(), Bool()])
        case List(Num()):
            return frozenset([Num()])
        case List(Bool()):
            return frozenset([Bool()])
        case _:
            return frozenset()


def combine_into_app(terms: list[Term]) -> Term:
    """
    Given a list of terms, combines them into a chain of App() (which is then returned)

    Examples
    --------
    >>> combine_into_app([Num(), Bool(), Var("out")])
    App(Num(), App(Bool(), Var("out"))  # Num -> Bool -> out

    Raises
    ------
    ValueError
        If terms is an empty list
    """
    match terms:
        case []:
            raise ValueError(f"Cannot use combine_into_app on an empty list")
        case [x]:
            return x
        case [x, y]:
            return App(x, y)
        case [x, *others]:
            return App(x, combine_into_app(others))
        case _:
            assert False, "Pattern matching in combine_into_app failed"


def infer_argument_signature(args: list["Value"]) -> Term:
    """
    Given a list of values, constructs a type that can be used for unification (which is then returned).

    Examples
    --------
    >>> infer_argument_signature([1, 2, True])
    App(Num, App(Num, Bool())))  # Num -> Num -> Bool

    Notes
    -----
    Type variables are of the form `<ARGUMENT_TYPE_SIGNATURE><X>`, where `<X>` is a unique non-negative integer.

    Raises
    ------
    ValueError
        If args is an empty list
    """
    arg_types: list[Term] = [infer_value_type(arg) for arg in args]
    offset = 0
    for i in range(0, len(arg_types)):
        arg_types[i], offset = alpha_conversion(arg_types[i], ARGUMENT_TYPE_PREFIX, offset)

    # NOTE: Combination should not happen before independent alpha conversion of each term.
    #  Otherwise, we might introduce unnecessary constraints (e.g. all empty lists need to hold the same type of value).
    #  Arguably, the more restrictive version might be fine as well in some cases, since if a more general case holds
    #  the restrictive case should hold as well. Nonetheless, we go for the most general type, as we want to keep as
    #  much freedom as possible, in case I end up using this function for something different as well.
    return combine_into_app(arg_types)


def decompose_term(t: Term) -> list[Term]:
    """
    Given a term of the form a -> b -> c, decomposes it into the list [a, b, c] (which is then returned).
    """
    def aux(inner_t: Term, acc: list[Term]) -> list[Term]:
        match inner_t:
            case App(a, b):
                return acc + [a] + decompose_term(b)
            case Var(_) | Num() | Bool() | List(_):
                return acc + [inner_t]
            case _:
                assert False, f"Pattern matching inside decompose_term failed: received inner_t of type {type(inner_t)}"
    return aux(t, [])


def drop_last_type_app(t: Term) -> Term:
    """Given a term of the form a -> b, drops the last type (b) and returns a.

    Notes
    -----
    Will fail with terms that only contain a single type t = Var | Num | Bool | List

    Raises
    ------
    ValueError
        If dropping the last type of t would result in an "empty" type
    """
    decomposition = decompose_term(t)
    del decomposition[-1]
    return combine_into_app(decomposition)
