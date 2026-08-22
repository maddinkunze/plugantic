from typing_extensions import Any, Literal, Union, List, LiteralString
from src.plugantic.plugin import _is_assignable as is_assignable

def test_assignability_basic():
    assert is_assignable(int, int)         # x: int = 5
    assert is_assignable(int, object)      # x: object = 5
    assert not is_assignable(object, int)  # x: int = object()

def test_assignability_numbers():
    assert is_assignable(int, float)          # x: float = 5
    assert not is_assignable(float, int)      # x: int = 5.1
    assert is_assignable(int, complex)        # x: complex = 5
    assert not is_assignable(complex, int)    # x: int = 5 + 1j
    assert is_assignable(float, complex)      # x: complex = 5.1
    assert not is_assignable(complex, float)  # x: float = 5.1 + 1j

def test_assignability_none():
    assert is_assignable(type(None), type(None))  # x: NoneType = type(None)()
    assert is_assignable(type(None), None)        # x: NoneType = None
    assert is_assignable(None, type(None))        # x: None = type(None)()
    assert is_assignable(None, None)              # x: None = None

def test_assignability_literals():
    assert is_assignable(Literal[1, 2], int)             # x: int = 1
    assert not is_assignable(int, Literal[1, 2])         # x: Literal[1, 2] = 5
    assert is_assignable(Literal[1], Literal[1, 2])      # x: Literal[1, 2] = 1
    assert not is_assignable(Literal[1, 2], Literal[1])  # x: Literal[1] = 2

    assert is_assignable(Literal["a", "b"], str)                # x: str = "a"
    assert not is_assignable(str, Literal["a", "b"])            # x: Literal["a", "b"] = "c"
    assert is_assignable(Literal["a"], Literal["a", "b"])       # x: Literal["a", "b"] = "a"
    assert not is_assignable(Literal["a", "b"], Literal["a"])   # x: Literal["a"] = "b"
    assert is_assignable(Literal["a", "b"], LiteralString)      # x: LiteralString = "a"
    assert not is_assignable(LiteralString, Literal["a", "b"])  # x: Literal["a", "b"] = "c"

def test_assignability_unions():
    assert is_assignable(Union[int, str], object)                      # x: object = 5
    assert not is_assignable(object, Union[int, str])                  # x: Union[int, str] = object()
    assert is_assignable(str, Union[int, str])                         # x: Union[int, str] = "hello"
    assert not is_assignable(Union[int, str], str)                     # x: str = 5
    assert is_assignable(Union[int, str], Union[int, str, float])      # x: Union[int, str, float] = 5
    assert not is_assignable(Union[int, str, float], Union[int, str])  # x: Union[int, str] = 5.1

def test_assignability_any():
    assert is_assignable(int, Any)  # x: Any = 5
    assert is_assignable(Any, int)  # x: int = cast(Any, ...)

def test_assignability_basic_generics():
    #assert is_assignable(List[int], List[int])      # x: List[int] = [1, 2, 3]
    assert not is_assignable(List[int], List[str])  # x: List[str] = [1, 2, 3]

def test_assignability_inherited_generics():
    ...

def test_assignability_covariant_generics():
    ...

def test_assignability_contravariant_generics():
    ...
