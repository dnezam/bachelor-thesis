from backend.state import State

"""
This file contains various (basic, hardcoded) test cases which directly interact with the backend. This was pretty
useful in early development to see whether the basic ideas would actually work out.

How to use this file
--------------------
To use this file, first load the file into an interactive Python console (see https://stackoverflow.com/q/5280178).
Since the test cases return the resulting state for further inspection, you can store the return value and then print
it. For example:

# Run test_addition() and look at the resulting state [assuming the file is already loaded]
s = test_addition()
print(s)
"""


def test_addition() -> State:
    """Generates a new function f0(a) = a + a"""
    s = State()

    # Generate function
    s.create_function()
    s.create_register(3)  # r0 = 3
    s.create_register(20)  # r1 = 20
    s._select_demonstration("r0", True)
    s._select_demonstration("r0", True)
    s._apply_demonstration("+", False)  # temp0 = r0 + r0 (6)
    s._select_demonstration("temp0", False)
    s.ret()  # return temp0

    # Test function
    s._select_interactive_between("r1")
    s._apply_interactive_between("f0")  # r2 = 40
    print(s)
    return s


def test_uop() -> State:
    """Generates f0(a, b) = b a a (b is applied to a and a)"""
    s = State()
    # Create function f0
    s.create_function()
    s.create_register(3)  # r0 = 3
    s.create_register(20)  # r1 = 20
    s.create_register(True)  # r2 = True
    s._select_demonstration("r0", True)
    s._select_demonstration("r0", True)
    s._apply_demonstration("+", True)
    s._select_demonstration("temp0", False)
    s.ret()

    # Try out f0
    s._select_interactive_between("r1")
    s._select_interactive_between("+")
    s._apply_interactive_between("f0")  # r3 = 20 + 20 = 40

    s._select_interactive_between("r1")
    s._select_interactive_between("-")
    s._apply_interactive_between("f0")  # r4 = 20 - 20 = 0

    s._select_interactive_between("r1")
    s._select_interactive_between("*")
    s._apply_interactive_between("f0")  # r5 = 20 * 20 = 400

    s._select_interactive_between("r1")
    s._select_interactive_between("!=")
    s._apply_interactive_between("f0")  # r6 = 20 != 20 = False

    s._select_interactive_between("r1")
    s._select_interactive_between("==")
    s._apply_interactive_between("f0")  # r7 = 20 == 20 = True

    s._select_interactive_between("r2")
    s._select_interactive_between("and")
    s._apply_interactive_between("f0")  # r8 = True and True = True
    print(s)
    return s


def test_branch() -> State:
    """Creates a function f(a), which returns [0,0] if a is even and [1, 1] if a is odd"""
    # Setup state
    s = State()
    s.create_register(4)  # r0 = 4
    s.create_register(2)  # r1 = 2
    s.create_register(0)  # r2 = 0

    s.create_function()  # Generate function

    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("%", False)  # temp0 = r0 % 2 (0)
    s._select_demonstration("temp0", False)
    s._select_demonstration("r2", False)
    s._apply_demonstration("==", False)  # temp1 = temp0 == 0 (True)
    s._select_demonstration("temp1", False)

    s.branch()  # branch temp1
    s.create_list([0, 0])  # l0 = [0, 0]
    s._select_demonstration("l0", False)
    s.ret()  # return [0, 0]

    # Change input to something uneven
    s.update_register("r0", 3)
    s.cont()

    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("%", False)  # temp0 = r0 % 2 (1)
    s._select_demonstration("temp0", False)
    s._select_demonstration("r2", False)
    s._apply_demonstration("==", False)  # temp1 = temp0 == 0 (False)
    s._select_demonstration("temp1", False)

    s.branch()  # branch temp1
    s.create_list([1, 1])  # l1 = [1, 1]
    s._select_demonstration("l1", False)
    s.ret()  # return [1, 1]

    # Test function
    s.create_register(42)  # r3 = 42
    s.create_register(43)  # r4 = 43
    s._select_interactive_between("r3")
    s._apply_interactive_between("f0")  # l2 = [0, 0]
    s._select_interactive_between("r4")
    s._apply_interactive_between("f0")  # l3 = [1, 1]
    print(s)
    return s


def test_map() -> State:
    """Test whether the built-in function map works"""

    s = State()
    s.create_list([])  # l0
    s.create_list([1])  # l1
    s.create_list([1, 2, 3])  # l2
    s.create_list([True, False])  # l3

    # Create function which increments number by 1
    s.create_function()
    s.create_register(0)  # r0
    s.create_register(1)  # r1
    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("+", False)  # temp0 = r0 + 1
    s._select_demonstration("temp0", True)
    s.ret()  # ret temp0 => f0

    # Create function which increments elements in list by 1
    s.create_function()
    s._select_demonstration("f0", False)  # f0(x) = x + 1
    s._select_demonstration("l1", True)
    s._apply_demonstration("map", False)
    s._select_demonstration("temp0", True)
    s.ret()  # f1

    s._select_interactive_between("f0")
    s._select_interactive_between("l0")
    s._apply_interactive_between("map")  # l4: []

    s._select_interactive_between("f0")
    s._select_interactive_between("l1")
    s._apply_interactive_between("map")  # l5: [2]

    s._select_interactive_between("f0")
    s._select_interactive_between("l2")
    s._apply_interactive_between("map")  # l6: [2, 3, 4]

    s._select_interactive_between("not")
    s._select_interactive_between("l3")
    s._apply_interactive_between("map")  # l7: [False, True]

    s._select_interactive_between("l6")
    s._apply_interactive_between("f1")  # l8: [3, 4, 5]

    print(s)
    return s


def test_filter() -> State:
    """Test whether the built-in function filter works"""
    s = State()

    # Create function which returns whether the input number is even
    s.create_function()
    s.create_register(1)  # r0
    s.create_register(2)  # r1
    s.create_register(0)  # r2
    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("%", False)  # temp0 = r0 % 2 (1)
    s._select_demonstration("temp0", True)
    s._select_demonstration("r2", False)
    s._apply_demonstration("==", False)  # temp1 = temp0 == 0 (False)
    s._select_demonstration("temp1", True)
    s.ret()  # ret temp1

    s.create_list([1, 2, 3, 4, 5, 6, 7, 8, 9])  # l0
    s._select_interactive_between("f0")
    s._select_interactive_between("l0")
    s._apply_interactive_between("filter")  # l1: [2, 4, 6, 8]

    return s


def test_recurse() -> State:
    """Test whether we can create a user-defined map function"""
    s = State()

    # Create function which returns whether the input list is empty
    s.create_function()
    s.create_list([1, 2, 3])  # l0
    s.create_register(0)  # r0
    s._select_demonstration("l0", True)
    s._apply_demonstration("len", False)  # temp0 = len(l0) (3)
    s._select_demonstration("temp0", True)
    s._select_demonstration("r0", False)
    s._apply_demonstration("==", False)  # temp1 = temp0 == 0
    s._select_demonstration("temp1", True)
    s.ret()  # f0

    # Create map, starting with base case
    s.create_function()
    s.create_list([])  # l1
    s._select_demonstration("l1", True)
    s._apply_demonstration("f0", False)  # temp0 = f0 l1 (True: l1 is empty)
    s._select_demonstration("temp0", True)
    s.branch()  # branch temp0
    s._select_demonstration("l1", False)
    s.ret()  # ret []

    # Continue with non-base case
    s.append_to_list("l1", True)  # l1: [True]
    s.cont()
    s._select_demonstration("l1", True)
    s._apply_demonstration("f0", False)  # temp0: False (l1 is not empty)
    s._select_demonstration("temp0", True)
    s.branch()  # Branch: False
    s._select_demonstration("l1", True)
    s._apply_demonstration("head", False)  # temp1: True (first element of list)
    s._select_demonstration("l1", True)
    s._apply_demonstration("tail", False)  # temp2: [] (list without its first element)
    s._select_demonstration("temp1", True)
    s._apply_demonstration("not", True)  # temp3: False (apply function to first element; function is variable)
    s._select_demonstration("temp2", True)
    s._select_demonstration("not", True)
    s.recurse()  # temp4: []
    s._select_demonstration("temp3", True)
    s._select_demonstration("temp4", True)
    s._apply_demonstration("cons", False)  # temp5: [False] (after applying the function, combine the result)
    s._select_demonstration("temp5", True)
    s.ret()

    # Create function which increments list by 1
    s.create_function()
    s.create_register(1)  # r1
    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("+", False)
    s._select_demonstration("temp0", True)
    s.ret()  # f2

    s._select_interactive_between("l0")
    s._select_interactive_between("f2")
    s._apply_interactive_between("f1")  # l2: [2, 3, 4]
    print(s)
    return s


def test_recurse_recursive_step_first() -> State:
    """Test whether we can create a user-defined map function by showing the recursive step before the base case"""
    s = State()

    # Create function isEmpty
    s.create_function()
    s.create_list([1, 2, 3])  # l0
    s.create_register(0)  # r0
    s._select_demonstration("l0", True)
    s._apply_demonstration("len", False)  # temp0
    s._select_demonstration("temp0", True)
    s._select_demonstration("r0", False)
    s._apply_demonstration("==", False)  # temp1
    s._select_demonstration("temp1", True)
    s.ret()  # f0

    # Create function which increments list by 1
    s.create_function()
    s.create_register(1)  # r1
    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("+", False)
    s._select_demonstration("temp0", True)
    s.ret()  # f1

    # Map: Step case first
    s.create_function()
    s._select_demonstration("l0", True)
    s._apply_demonstration("f0", False)  # temp0: False
    s._select_demonstration("temp0", True)
    s.branch()  # Branch: False
    s._select_demonstration("l0", True)
    s._apply_demonstration("head", False)  # temp1: 1
    s._select_demonstration("l0", True)
    s._apply_demonstration("tail", False)  # temp2: [2, 3]
    s._select_demonstration("temp1", True)
    s._apply_demonstration("f1", True)  # temp3: 2
    s._select_demonstration("temp2", True)
    s._select_demonstration("f1", True)
    s.recurse()  # temp4: "[3, 4]" / None
    s._select_demonstration("temp3", True)
    s._select_demonstration("temp4", True)
    s._apply_demonstration("cons", False)  # temp5: [2, 3, 4]
    s._select_demonstration("temp5", True)
    s.ret()

    # Map: Base case
    s.update_list("l0", [])
    s.cont()
    s._select_demonstration("l0", True)
    s._apply_demonstration("f0", False)  # temp0
    s._select_demonstration("temp0", True)
    s.branch()
    s._select_demonstration("l0", False)
    s.ret()

    return s


def test_cond_map() -> State:
    """Test whether we can create a conditional map: Pass a boolean, two functions and a list. Depending on the value
    of the boolean, the conditional map either "maps" the first or second function to the list"""
    s = State()

    # Create function isEmpty
    s.create_function()
    s.create_list([1, 2, 3])  # l0
    s.create_register(0)  # r0
    s._select_demonstration("l0", True)
    s._apply_demonstration("len", False)  # temp0
    s._select_demonstration("temp0", True)
    s._select_demonstration("r0", False)
    s._apply_demonstration("==", False)  # temp1
    s._select_demonstration("temp1", True)
    s.ret()  # f0

    # Create isEven function
    s.create_function()
    s.create_register(1)  # r1
    s.create_register(2)  # r2
    s._select_demonstration("r1", True)
    s._select_demonstration("r2", False)
    s._apply_demonstration("%", False)  # temp0
    s._select_demonstration("temp0", True)
    s._select_demonstration("r0", False)
    s._apply_demonstration("==", False)  # temp1
    s._select_demonstration("temp1", True)
    s.ret()  # f1

    # Create function which increments number by 1
    s.create_function()
    s._select_demonstration("r0", True)
    s._select_demonstration("r1", False)
    s._apply_demonstration("+", False)
    s._select_demonstration("temp0", True)
    s.ret()  # f2

    # Create conditional map: Depending on passed boolean apply either f1 or f2
    s.create_function()
    # Check length of list + branch
    s._select_demonstration("l0", True)
    s._apply_demonstration("f0", False)  # temp0 = False
    s._select_demonstration("temp0", False)
    s.branch()
    # Boolean to decide which function we want to map
    s.create_register(True)  # r3 = True
    s._select_demonstration("r3", True)
    s.branch()
    # Recursively apply first function
    s._select_demonstration("l0", True)
    s._apply_demonstration("head", False)  # temp1
    s._select_demonstration("l0", True)
    s._apply_demonstration("tail", False)  # temp2
    s._select_demonstration("temp1", True)
    s._apply_demonstration("f1", True)  # temp3
    s._select_demonstration("temp2", True)
    s._select_demonstration("r3", True)
    s._select_demonstration("f1", True)
    s.recurse()  # temp4
    s._select_demonstration("temp3", True)
    s._select_demonstration("temp4", True)
    s._apply_demonstration("cons", False)
    s._select_demonstration("temp5", True)
    s.ret()

    # Check whether list is empty
    s.update_register("r3", False)
    s.cont()
    s._select_demonstration("l0", True)
    s._apply_demonstration("f0", False)  # temp0 = False
    s._select_demonstration("temp0", False)
    s.branch()
    # Boolean to decide which function we want to map
    s._select_demonstration("r3", True)
    s.branch()
    # Recursively apply second function
    s._select_demonstration("l0", True)
    s._apply_demonstration("head", False)  # temp6
    s._select_demonstration("l0", True)
    s._apply_demonstration("tail", False)  # temp7
    s._select_demonstration("temp6", True)
    s._apply_demonstration("f2", True)  # temp8
    s._select_demonstration("temp7", True)
    s._select_demonstration("r3", True)
    s._select_demonstration("f1", True)
    s._select_demonstration("f2", True)
    s.recurse()  # temp9
    s._select_demonstration("temp8", True)
    s._select_demonstration("temp9", True)
    s._apply_demonstration("cons", False)  # temp10
    s._select_demonstration("temp10", True)
    s.ret()

    s.update_list("l0", [])
    s.cont()
    s._select_demonstration("l0", True)
    s._apply_demonstration("f0", False)  # temp0 = True
    s._select_demonstration("temp0", False)
    s.branch()
    s._select_demonstration("l0", False)
    s.ret()  # f3

    # Create identity function
    s.create_function()
    s._select_demonstration("r0", True)
    s.ret()  # f4

    # Test conditional map (f3)
    s.create_list([True, False, True, True, False])
    s.update_register("r3", True)
    s._select_interactive_between("l1")
    s._select_interactive_between("r3")
    s._select_interactive_between("not")
    s._select_interactive_between("f4")
    s._apply_interactive_between("f3")  # Expected: [False, True, False, False, True]

    s.update_register("r3", False)
    s._select_interactive_between("l1")
    s._select_interactive_between("r3")
    s._select_interactive_between("not")
    s._select_interactive_between("f4")
    s._apply_interactive_between("f3")  # Expected: [True, False, True, True, False]
    print(s)
    return s

# TODO Add test for constant function - especially pay attention to the type
