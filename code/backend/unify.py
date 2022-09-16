# TODO: Don't forget to copy over reference if you refactor something
# References:
# https://eli.thegreenplace.net/2018/unification/
# https://stackoverflow.com/questions/16258553/how-can-i-define-algebraic-data-types-in-python
# https://stackoverflow.com/questions/4828080/how-to-make-an-immutable-object-in-python
# https://stackoverflow.com/questions/16258553/how-can-i-define-algebraic-data-types-in-python
from __future__ import annotations

from dataclasses import dataclass
from typing import get_args


# This class contains the implementation of the unification algorithm which is heavily used for the type system we are
# implementing

# Define types of "objects" (in the general sense) in the system
# We define our types as immutable dataclass, so we can easily compare them for equivalence and use pattern matching
@dataclass(frozen=True)
class Var:
    name: str

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Num:
    def __str__(self):
        return "Num"


@dataclass(frozen=True)
class Bool:
    def __str__(self):
        return "Bool"


@dataclass(frozen=True)
class List:
    a: Term

    def __str__(self):
        return f"[{str(self.a)}]"


@dataclass(frozen=True)
class App:
    a: Term
    b: Term

    def __str__(self):
        return f"({str(self.a)} -> {str(self.b)})"


class NoSolutionError(Exception):
    """This exception is raised if we cannot unify a set of constraints"""
    pass


Fun = Num | Bool | List | App
Term = Fun | Var
Equation = tuple[Term, Term]


def free_variables(t: Term) -> set[Var]:
    """Return set of free variables in term t"""
    match t:
        case Var(_):
            return {t}
        case Num():
            return set()
        case Bool():
            return set()
        case List(a):
            return free_variables(a)
        case App(a, b):
            return free_variables(a) | free_variables(b)
        case _:
            assert False, f"Pattern matching in free_variables failed: received t of type {type(t)}"


def free_variables_equations(equations: list[Equation]) -> set[Var]:
    """Return set of free variables in the list of equations ``equations``"""
    result = set()
    for lhs, rhs in equations:
        result |= free_variables(lhs) | free_variables(rhs)
    return result


def substitute_term(x: Var, rt: Term, t: Term) -> Term:
    """Return a new term where all occurrences of variable x in term t are substituted with term rt"""
    match t:
        case Var(_):
            return rt if x == t else t
        case Num():
            return t
        case Bool():
            return t
        case List(a):
            subst_a = substitute_term(x, rt, a)
            return List(subst_a)
        case App(a, b):
            subst_a = substitute_term(x, rt, a)
            subst_b = substitute_term(x, rt, b)
            return App(subst_a, subst_b)


def alpha_conversion(x: Term, name: str, offset: int = 0) -> tuple[Term, int]:
    """Apply alpha conversion to x.

    Parameters
    ----------
    x
        Term on which we will do alpha conversion
    name
        Prefix of the new type variables
    offset
        Suffix added to the prefix starting from `offset`, such that the old and new term are alpha equivalent. Has
        to be non-negative

    Returns
    -------
    tuple[Term, int]
        First element of tuple is the new, alpha equivalent term. The second element is the new offset, which can
        be passed to the next call of `alpha_conversion`.


    Examples
    --------
    >>> alpha_conversion(App(Num(), App(Var("a"), Var("a"))), "new", 0)  # Num -> a -> a, "new", 0
    App(Num(), App(Var("new0"), Var("new0")))  # Num -> new0 -> new0

    >>> alpha_conversion(App(Bool(), App(Var("a"), Var("b"))), "new", 3)  # Bool -> a -> b, "new", 3
    App(Bool(), App(Var("new4"), Var("new3")))  # Bool -> new4 -> new3

    Notes
    -----
    When replacing the free variables, there is no guaranteed order (i.e. there is no guarantee that free variables
    from left to right are also replaced from left to right. Thus, the suffix of `name` does not necessarily increase
    monotonically from left to right.).

    Raises
    ------
    ValueError
        If offset is negative
    """

    if not offset >= 0:
        raise ValueError("offset has to be larger or equal to 0")

    work_set = free_variables(x)
    for free_variable in work_set:
        x = substitute_term(free_variable, Var(f"{name}{offset}"), x)
        offset += 1

    return x, offset


def substitute_equation(x: Var, rt: Term, eq: Equation) -> Equation:
    """Return a new equation where all occurrences of variable ``x`` in equation ``eq`` are substituted with term
    ``rt``"""
    return substitute_term(x, rt, eq[0]), substitute_term(x, rt, eq[1])


def substitute_list(x: Var, rt: Term, c: list) -> list:
    """Return a new list where all occurrences of variable ``x`` in list ``c`` are substituted with term ``rt``"""
    subst_c = []
    for eq in c:
        subst_eq = substitute_equation(x, rt, eq)
        subst_c.append(subst_eq)
    return subst_c


def _decompose_functions(lhs: Fun, rhs: Fun) -> list[Equation]:
    """Decompose f0(a, b, ...) = f1(c, d, ...) into [a = c, b = d, ...]

    Raises
    ------
    NoSolutionError
        If lhs = rhs cannot be decomposed
    """
    match lhs, rhs:
        case Num(), Num():
            return []
        case Bool(), Bool():
            return []
        case List(a), List(b):
            return [(a, b)]  # TODO: Can I make sure that a and b have the correct type annotated and not Any?
        case App(a, b), App(c, d):
            return [(a, c), (b, d)]
        case _:
            raise NoSolutionError(f"Cannot decompose {lhs} = {rhs}")


# References (for implementation)
# - Algorithm 1: Unification algorithm in pseudo-code from "Solving type inference constraints"
#   by Sofia Giampietro for Formal Methods and Functional Programming Spring Semester 2021
#   Notes: I think the pseudocode in that document contains a mistake. If we choose x = a -> b -> c from
#   {x = a -> b -> c, b = a -> d}, we will end up with {x = a -> b -> c, b = a -> d} again. The issue is, that one of
#   the lhs (b) is still contained in the rhs (x = a -> b -> c). This has been corrected in the implementation together
#   with the help of other references.
# - https://en.wikipedia.org/wiki/Unification_(computer_science) 09:43, 03. Mai. 2022
# - https://www.cmi.ac.in/~madhavan/courses/pl2009/lecturenotes/lecture-notes/node113.html 09:43, 03. Mai. 2022
def unify(equations: list[Equation]) -> list[Equation]:  # Test this
    """Unify list of equations and return the result as a new list of (unified) equations.

    Parameters
    ----------
    equations
        List of equations to be unified

    Raises
    ------
    NoSolutionError
        If unification failed (rule "conflict" or "check")
    ValueError
        If final unification result contains an unsupported type
    """
    if not equations:  # Unifier of empty list
        return []

    for idx in range(len(equations)):
        result, applied = _apply_rule(equations, idx)  # Try to apply a rule
        if applied:  # Do unification as long as we can apply a rule
            return unify(result)

    _check_list(equations)

    return equations  # No rule was applied to any equation in the list


# https://stackoverflow.com/questions/45957615/check-a-variable-against-union-type-at-runtime-in-python-3-6
def _apply_rule(equations: list[Equation], idx: int) -> tuple[list[Equation], bool]:
    """
    Tries to apply a unification rule on the equation at `idx`.
    Returns the resulting set of equations and whether a rule was actually applied.
    If no rule was applied, it restores the passed list.

    Raises
    ------
    NoSolutionError
        If rule "conflict" or "check" applies
    """
    lhs, rhs = equations.pop(idx)
    rest = equations
    if lhs == rhs:  # delete
        return rest, True
    elif isinstance(lhs, get_args(Fun)) and isinstance(rhs, get_args(Fun)):  # decompose and conflict
        return rest + _decompose_functions(lhs, rhs), True
    elif isinstance(lhs, get_args(Fun)) and isinstance(rhs, Var):  # swap
        return rest + [(rhs, lhs)], True
    # eliminate
    elif isinstance(lhs, Var) and (lhs not in free_variables(rhs)) and (lhs in free_variables_equations(rest)):
        return substitute_list(lhs, rhs, rest) + [(lhs, rhs)], True
    elif isinstance(lhs, Var) and isinstance(rhs, get_args(Fun)) and (lhs in free_variables(rhs)):  # check
        raise NoSolutionError(f"lhs: {lhs} occurs in rhs: {rhs}")
    else:  # If we cannot apply a rule: undo pop and return
        rest.insert(idx, (lhs, rhs))
        restored = rest
        return restored, False


def _check_type(term: Term) -> None:
    """Checks whether the type `term` is supported by the system.
    For example, we do not support lists of list, or lists of functions.

    Raises
    ------
    ValueError
        If term has an unsupported type
    """
    match term:
        case Var(_):
            pass
        case Num():
            pass
        case Bool():
            pass
        case List(a):
            match a:
                case Num():
                    pass
                case Bool():
                    pass
                case Var(_):
                    pass
                case _:
                    raise ValueError(f"System does not support type {term}")
        case App(a, b):
            _check_type(a)
            _check_type(b)
        case _:  # Although this case shouldn't even occur
            raise ValueError(f"System does not support type {term} [First level pattern matching failed]")


# NOTE: Maybe it would be better to have a generic function lifting functions from terms, to equations, to lists?
def _check_equation(eq: Equation) -> None:
    """Check whether both sides of the equation eq are valid types

    Raises
    -----
    ValueError
        If eq contains a term of unsupported type
    """
    _check_type(eq[0])
    _check_type(eq[1])


def _check_list(c: list[Equation]) -> None:
    """Check whether all equations in list l have valid types

    Raises
    ------
    ValueError
        If c contains a term of unsupported type
    """
    for eq in c:
        _check_equation(eq)
