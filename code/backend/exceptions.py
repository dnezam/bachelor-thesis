class ModeError(Exception):
    """Raise this error if we are not in the correct mode to perform an operation"""
    pass


class NoneAsFunArg(Exception):
    """Raise this error if None is passed to a built-in or custom function (i.e. result of a recursion)"""
    pass


class AlgotRuntimeError(Exception):
    """Raise this error if there is a runtime error like division by zero or taking the head of an empty list when
    executing a function in the system (i.e. during compute(args) of Function)"""
    pass
