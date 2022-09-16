import copy

from backend.custom_function import CustomFunction
from backend.function import Function
from backend.helper_type import Value, Expr, Instruction, Path
from backend.helpers import infer_value_type, combine_into_app
from backend.tree import Tree
from backend.unify import Equation, Term, Var, alpha_conversion, unify, Bool

ABSTRACT_TYPE_SIG = "w_sig"  # Type variable representing the final signature (cp. unification in generate_function)
ABSTRACT_TYPE_PREFIX = "w"  # Prefix of type variables for abstract types (internal to function)
ABSTRACT_TYPE_OUTPUT = "w_out"  # Name of return type of the function to be synthesized


class Demonstration:
    """Keeps track of information related to example demonstration and function synthesis"""

    def __init__(self):
        # Represent constant by names s.t. instruction can refer to values by a name
        self._constants: dict[str, Value] = {}
        self._next_id_constants: int = 0

        self._inputs: dict[str, str] = {}  # Mapping from names in state to inX
        self._next_id_inputs: int = 0

        self._types: dict[str, Term] = {}  # Mapping from names to abstract type
        self._next_id_type: int = 0  # Suffix for ABSTRACT_TYPE_PREFIX

        # Mapping from temporary names to the expression generating its value and the value itself if possible. If we
        # don't know the actual value (e.g. couldn't calculate the result of recursion), we set it to None
        self._temps: dict[str, tuple[Expr, Value | None]] = {}
        self._next_id_temps: int = 0
        # Required to make sure new temps get new names across multiple examples, while making sure that we use old temp
        # names when (old) instructions are expected (otherwise expected and actual instructions would always differ in
        # the name of the temporary).
        self._new_branch: bool = True
        self._prev_next_id_temps: int = 0

        # Keeps track of recursive calls in the program; int gives the location in the block of instruction in Tree
        self._recursive_calls: list[tuple[Tree, int]] = []

        # Keeps track of generated instructions
        self._tree: Tree = Tree([])
        # Represent position of the current instruction in current node
        self._current_node: Tree = self._tree
        self._block_counter: int = 0

        self._constraints: list[Equation] = []  # Type constraints

    def __str__(self):
        return (f"Temporaries assignments: {self._temps}\n"
                f"Input assignments: {self._inputs}\n"
                f"Type assignments: { {k: str(v) for k, v in self._types.items()} }\n")

    def is_used(self, name: str) -> bool:
        """Returns whether a name from the state (where state refers to values that are also accessible in interactive
        mode) is used in the current demonstration.

        Parameters
        ----------
        name
            Name to be checked whether it is used in the current demonstration
        """
        return name in self._inputs

    def get_temp(self, name: str) -> Value:
        """Return the value of temporary ``name``

        Parameters
        ----------
        name
            Name of the temporary to get the value from

        Raises
        ------
        KeyError
            If temporary name doesn't exist
        """
        return self._temps[name][1]

    def get_temp_names(self) -> list[str]:
        """Return a list with the names of all temporaries"""
        return list(self._temps.keys())

    def get_temp_computation(self, name: str) -> list[str]:
        """Return the expression which calculates the value of the temporary ``name``

        Parameters
        ----------
        name
            Name of the temporary to get the expression from

        Raises
        ------
        KeyError
            If temporary name doesn't exist
        """
        return self._temps[name][0]

    def add_constant(self, value: Value) -> str:
        """Returns the name used internally for the passed constant ``value``

        Parameters
        ---------
        value
            Value of constant to be added

        Notes
        -----
        If ``value`` already exists as a constant, we return the pre-existing name. Otherwise, we add the value to
        _constants with a new name first.
        """
        # Check whether constant for that value already exists
        for k, v in self._constants.items():
            # If both values are functions, compare them by their unique_id
            if isinstance(v, Function) and isinstance(value, Function):
                if v.unique_id == value.unique_id:
                    return k
            else:
                if v == value:
                    return k

        const_name = f"const{self._next_id_constants}"
        const_type = infer_value_type(value)

        # NOTE: Constants should not be able to change - hence we need a copy.
        self._constants[const_name] = copy.deepcopy(value)
        self._next_id_constants += 1

        # Type of constant is the type of the actual value
        self._types[const_name], self._next_id_type = alpha_conversion(const_type, ABSTRACT_TYPE_PREFIX,
                                                                       self._next_id_type)
        return const_name

    def add_input(self, s_in: str) -> str:
        """Return input name for ``s_in``

        Parameters
        ----------
        s_in
            Name of register/list/function from state

        Notes
        -----
        Check whether we have used `s_in` as an argument in the past - if yes, the uses are coupled
        (e.g. if we select the same register twice and apply +, we will synthesize a function which takes an input in0
        and returns in0 + in0. If we were to select two different registers, we will synthesize a function which takes
        two inputs in0 and in1 and returns in0 + in1)
        """
        if s_in not in self._inputs:  # First time the register/list/function gets used as an input
            input_name = f"in{self._next_id_inputs}"

            self._inputs[s_in] = input_name
            self._next_id_inputs += 1

            # Update past recursive calls with new inputs (otherwise they do not pass enough arguments to the recursive
            # call)
            for rcall in self._recursive_calls:
                # No need to add constraints, as type of input to function and argument to recursive call is the same
                rcall[0].get_instruction(rcall[1])[1].append(input_name)
                # NOTE We might need to update the associated type constraints - but probably not.
                #  (although we already fixed the associated bug, this thought might be good to keep around, at least
                #   for now)

            # Type of input is a general type variable - restrictions are enforced through constraints added by function
            # applications
            self._types[input_name] = Var(f"{ABSTRACT_TYPE_PREFIX}{self._next_id_type}")
            self._next_id_type += 1

        else:
            input_name = self._inputs[s_in]

        return input_name

    def add_function_application(self, expr: Expr, result: Value) -> str:
        """Adds ``expr`` as an instruction and returns the associated temporary name.

        Parameters
        ----------
        expr
            Function application expression (includes function name)
        result
            Value of evaluated function application expression

        Notes
        -----
        expr is stored together with result under a new temporary name in _temps, allowing us to easily get the value
        of the evaluated expression (assuming it is not None, i.e. assuming we actually know the value)

        Raises
        ------
        ValueError
            If the generated instruction does not match the expected instruction
        """
        self._switch_next_id_temps()
        temp_name = f"temp{self._next_id_temps}"
        instr = (temp_name, expr)

        self._add_instruction(instr)
        self._block_counter += 1

        self._temps[temp_name] = (expr, result)
        self._next_id_temps += 1

        if temp_name not in self._types:  # Need to add a type for temp_name
            self._types[temp_name] = Var(f"{ABSTRACT_TYPE_PREFIX}{self._next_id_type}")
            self._next_id_type += 1

        # Determine LHS: Expected types
        lhs = self._types[expr[0]]
        # Determine RHS: Given types (i.e. in and temp type)
        rhs_types = [self._types[key] for key in expr[1:]] + [self._types[temp_name]]
        rhs = combine_into_app(rhs_types)

        self._constraints.append((lhs, rhs))
        return temp_name

    def add_recursive_application(self, expr: Expr, result: Value | None) -> str:
        """Adds ``expr`` as an instruction and returns the associated temporary name. This function is called if the
        function application is recursive

        Parameters
        ----------
        expr
            Function application expression (includes self)
        result
            Value of evaluated function application expression, if it is possible to calculate

        Raises
        ------
        ValueError
            If the generated instruction does not match the expected instruction
        """
        self._switch_next_id_temps()
        temp_name = f"temp{self._next_id_temps}"
        instr = (temp_name, expr)

        self._add_instruction(instr)
        self._recursive_calls.append((self._current_node, self._block_counter))
        self._block_counter += 1

        self._temps[temp_name] = (expr, result)
        self._next_id_temps += 1

        if temp_name not in self._types:  # Need to add a type for temp_name
            self._types[temp_name] = Var(f"{ABSTRACT_TYPE_PREFIX}{self._next_id_type}")
            self._next_id_type += 1

        # Types of the input of the function need to match the types of the arguments passed to the recursive call
        # Temp has the same type as the output of the function
        lhs_types = [self._types[input_name] for input_name in self._inputs.values()] + [Var(ABSTRACT_TYPE_OUTPUT)]
        lhs = combine_into_app(lhs_types)
        rhs_types = [self._types[key] for key in expr[1:]] + [self._types[temp_name]]
        rhs = combine_into_app(rhs_types)

        self._constraints.append((lhs, rhs))
        return temp_name

    def branch(self, cnd_name: str, cnd_value: bool) -> None:
        """
        Add branch constraint and instruction + update the current node and block counter accordingly.

        Parameters
        ----------
        cnd_name
            Name of the condition to branch on
        cnd_value
            Value of the condition to branch on

        Raises
        ------
        ValueError
            If the generated instruction does not match the expected instruction
        """
        self._constraints.append((self._types[cnd_name], Bool()))
        self._add_instruction((None, ["branch", cnd_name]))

        if cnd_value:
            self._current_node = self._current_node.get_true(True)
        else:
            self._current_node = self._current_node.get_false(True)

        self._block_counter = 0

    def ret(self, name: str) -> None:
        """
        Return ``name`` in the context of function synthesis, adding the respective constraints and instruction

        Raises
        ------
        ValueError
            If the generated instruction does not match the expected instruction
        """
        self._constraints.append((self._types[name], Var(ABSTRACT_TYPE_OUTPUT)))
        self._add_instruction((None, ["ret", name]))
        self._new_branch = False

    def prepare(self) -> None:
        """Prepare for another example"""
        # Reset current node and block counter to beginning
        self._current_node = self._tree
        self._block_counter = 0
        # Clear temps, since we don't know their value if we are starting over
        self._temps = {}
        self._prev_next_id_temps = self._next_id_temps
        self._next_id_temps = 0

    def remaining_examples(self) -> list[Path]:
        """Return a list of paths indicating the remaining examples required for synthesis"""
        return self._tree.remaining_examples()

    def generate_function(self, unique_id: int) -> CustomFunction:
        """Generates a function from current demonstration

        Raises
        ------
        NoSolutionError
            If unification failed (rule "conflict" or "check")
        ValueError
            If final unification result contains an unsupported type
        """
        # Use unification to figure out the function signature
        # New constraint: LHS: name for resulting function signature, RHS: inputs -> output
        types = [self._types[input_name] for input_name in self._inputs.values()] + [Var(ABSTRACT_TYPE_OUTPUT)]
        # Cannot add this constraint permanently to self._constraints - otherwise we would get a contradiction in
        # subsequent recursive calls if the number of arguments increases
        unified_constraints = unify(self._constraints + [(Var(ABSTRACT_TYPE_SIG), combine_into_app(types))])

        # Find unified function signature
        function_signature = None
        for lhs, function_signature in unified_constraints:  # variables lhs and function_sig persist in scope
            if lhs == Var(ABSTRACT_TYPE_SIG):
                break

        # Get list of instructions
        instructions = self._tree

        return CustomFunction(function_signature, instructions, self._constants, unique_id)

    def is_valid_temp(self, name: str) -> bool:
        """Returns whether ``name`` is the name of a temporary

        Parameters
        ----------
        name
            Name to be checked whether it is a valid temporary
        """
        return name in self._temps

    def is_valid_name(self, name: str) -> bool:
        """Returns whether ``name`` is a valid name in the current demonstration

        Parameters
        ----------
        name
            Name to be checked whether it is valid

        Notes
        -----
        The function is kept general (i.e. different from is_valid_temp) in case more names beyond temporaries
        that could be interesting to "outsiders" (e.g. State) are added.
        We do not check whether ``name`` is a valid input or constant, as users shouldn't have to access these names
        directly. Instead, they should access registers/lists/functions where they know the value(s) they hold.
        """
        return self.is_valid_temp(name)

    # "Private" methods
    def _get_expected(self) -> Instruction | None:
        """Returns expected instruction. If no instruction is expected, returns None"""
        try:
            return self._current_node.get_instruction(self._block_counter)
        except IndexError:
            return None

    def _is_expected(self) -> bool:
        """Returns whether some instruction is expected"""
        return self._get_expected() is not None

    def _switch_next_id_temps(self) -> None:  # NOTE: Can't we move this functionality into branch?
        """Makes sure new temps get a unique name

        Notes
        -----
        On the one hand, the temp names need to match if there are expected instructions (otherwise instructions to be
        added would never match the expected ones), on the other hand, temp names need to be different from past ones
        if no instructions are expected (otherwise different constraints will collide due to reusing the same name)
        """
        if not self._new_branch and not self._is_expected():  # We did not register the change to the new path yet
            self._next_id_temps = self._prev_next_id_temps
            self._new_branch = True

    def _add_instruction(self, instr: Instruction) -> None:
        """Adds instruction to tree, if possible

        We can add an instruction if no instruction was expected or the passed instruction matches the expected one.

        Parameters
        ----------
        instr
            Instruction to be added

        Raises
        ------
        ValueError
            If passed instruction doesn't match expected instruction
        """
        expected = self._get_expected()
        if expected is None:
            self._current_node.append_instruction(instr)
        elif instr != expected:
            raise ValueError(f"Expected {expected}, received {instr}")
