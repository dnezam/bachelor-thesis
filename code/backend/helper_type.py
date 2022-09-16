# This is in a separate file to escape the circular import hole
from backend.function import Function

# "Primary"/"Primitive" values held by registers and lists
PValue = int | float | bool
# Values supported by the system (i.e. can be used as arguments for built-in and user-defined functions
Value = PValue | list[PValue] | Function
# Expressions within instructions which represent the (calculations to get the) value of a temporary
Expr = list[str]  # ["function name", "arg0", "arg1", ..., "argN"]
# Statements don't return a value, e.g. returning, branching
Stmt = list[str]
# Instructions that can later be executed
Instruction = tuple[str, Expr] | tuple[None, Stmt]
# Type to describe the path from the root of a tree to a node
Path = list[str]
