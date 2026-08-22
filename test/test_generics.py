from src.plugantic import PluginModel, PluginAdapter, DEFAULT_LITERAL
from pydantic import BaseModel
from typing_extensions import Literal, Generic, TypeVar

from ._common import InvalidTestStateException

T = TypeVar("T", bound=int)
S = TypeVar("S", bound=float, contravariant=True)

class Test(Generic[S]):
    ...

class Impl(Test[T], Generic[T]):
    ...


def test_basic_generics():
    T = TypeVar("T")
    R = TypeVar("R")

    class Base(PluginModel, Generic[T, R]):
        pass

    class Impl1(Base[str, int]):
        type: Literal["impl1"] = DEFAULT_LITERAL

    class Impl2(Base[int, str]):
        type: Literal["impl2"] = DEFAULT_LITERAL

    class Impl3(Base[int, int]):
        type: Literal["impl3"] = DEFAULT_LITERAL

    class Impl4(Base[T, R], Generic[R, T]):
        ...

    breakpoint()

    class SomeConfig(BaseModel):
        config: PluginAdapter[Base[int]]

    try:
        SomeConfig(config=Impl1()) # type: ignore
        raise InvalidTestStateException("Expected validation error for type mismatch")
    except InvalidTestStateException: raise
    except Exception: pass
    SomeConfig(config=Impl2())
    SomeConfig(config=Impl3())

    try:
        SomeConfig.model_validate({"config": {"type": "impl1"}})
        raise InvalidTestStateException("Expected validation error for type mismatch")
    except InvalidTestStateException: raise
    except Exception: pass
    c1 = SomeConfig.model_validate({"config": {"type": "impl2"}})
    c2 = SomeConfig.model_validate({"config": {"type": "impl3"}})

    assert isinstance(c1.config, Impl2)
    assert isinstance(c2.config, Impl3)

def test_bound_generics():
    class BaseFeature:
        pass

    class Feature1(BaseFeature):
        pass

    class Feature2(BaseFeature):
        pass

    class Feature3(Feature2):
        pass

    T = TypeVar("T", bound=BaseFeature)
    
    class Base(PluginModel, Generic[T]):
        pass
    
    class Impl1(Base[Feature1]):
        type: Literal["impl1"] = DEFAULT_LITERAL
    
    class Impl2(Base[Feature2]):
        type: Literal["impl2"] = DEFAULT_LITERAL
    
    class Impl3(Base[Feature3]):
        type: Literal["impl3"] = DEFAULT_LITERAL
    
    class SomeConfig(BaseModel):
        config: PluginAdapter[Base[Feature2]]
    
    try:
        SomeConfig(config=Impl1()) # type: ignore
        raise InvalidTestStateException("Expected validation error for type mismatch")
    except InvalidTestStateException: raise
    except Exception: pass
    SomeConfig(config=Impl2())
    try:
        SomeConfig(config=Impl3()) # type: ignore
        raise InvalidTestStateException("Expected validation error for type mismatch")
    except InvalidTestStateException: raise
    except Exception: pass

    try:
        SomeConfig.model_validate({"config": {"type": "impl1"}})
        raise InvalidTestStateException("Expected validation error for type mismatch")
    except InvalidTestStateException: raise
    except Exception: pass
    c1 = SomeConfig.model_validate({"config": {"type": "impl2"}})
    try:
        SomeConfig.model_validate({"config": {"type": "impl3"}})
        raise InvalidTestStateException("Expected validation error for type mismatch")
    except InvalidTestStateException: raise
    except Exception: pass
    
    assert isinstance(c1.config, Impl2)

# TODO: add tests (and implementations XD) for plugin classes with covariant and contravariant type arguments
