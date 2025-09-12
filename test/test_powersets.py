from typing_extensions import TypeGuard
from plugantic._helpers import recursive_powerset

def isint(x) -> TypeGuard[int]:
    return isinstance(x, int)

def test_powerset_1():
    inputs = [1, 2, 3]
    expected = [(1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)]
    expected_out = list(map(sum, expected))

    output = recursive_powerset(inputs, isint, sum)
    for e in output:
        expected_out.remove(e)
    assert not expected_out

def test_powerset_2():
    inputs = [1, 2, (3, 4)]
    expected = [(1,), (2,), (3,), (4,), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (1, 2, 3), (1, 2, 4)]
    expected_out = list(map(sum, expected))

    output = recursive_powerset(inputs, isint, sum)
    for e in output:
        expected_out.remove(e)
    assert not expected_out

def test_powerset_3():
    inputs = [1, (2, 3), (4, 5)]
    expected = [(1,), (2,), (3,), (4,), (5,), (1, 2), (1, 3), (1, 4), (1, 5), (2, 4), (2, 5), (3, 4), (3, 5), (1, 2, 4), (1, 2, 5), (1, 3, 4), (1, 3, 5)]
    expected_out = list(map(sum, expected))

    output = recursive_powerset(inputs, isint, sum)
    for e in output:
        expected_out.remove(e)
    assert not expected_out
