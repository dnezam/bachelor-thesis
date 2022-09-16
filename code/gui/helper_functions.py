from backend.helper_type import PValue


def str_to_bool(s: str) -> bool:
    """Converts the passed string 'True'/'False' to boolean True/False

    Raises
    ------
    ValueError
        If the passed string is neither 'True' nor 'False'
    """
    if s == "True":
        return True
    elif s == "False":
        return False
    else:
        raise ValueError(f"Cannot convert {s} into a bool")


def str_to_int_float(s: str) -> int | float:
    """Converts the passed string into the respective int or float

    Notes
    -----
    We first try to convert the passed string into an int. Only if this fails we try to convert it into a float.

    Raises
    ------
    ValueError
        If the passed string cannot be converted into an int or float
    """
    try:
        return int(s)
    except ValueError:
        return float(s)


def str_to_pvalue(s: str) -> PValue:
    """
    Converts the passed string into a primary value like int, float or bool

    Raises
    ------
    ValueError
        If the passed string cannot be converted into a primary value like int, float or bool
    """
    try:
        return str_to_bool(s)
    except ValueError:
        pass
    try:
        return str_to_int_float(s)
    except ValueError:
        raise ValueError(f"Could not convert {s} into a bool, nor int, nor float")
