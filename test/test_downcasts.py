from plugantic import PluginModel, PluginAdapter
from pydantic import BaseModel

from ._common import InvalidTestStateException

def test_basic_downcast():
    class Base1(PluginModel):
        value: str

    class Base2(PluginModel):
        number: int

    class Base3(PluginModel):
        pass

    class Impl1(Base1, value="impl"):
        pass

    class Impl2(Base2, value="impl"):
        pass

    class Impl3(Base3, value="impl"):
        pass

    class Impl4(Impl1, Impl2):
        pass

    class Impl5(Impl1, Impl3):
        pass

    class SomeConfig(BaseModel):
        config: PluginAdapter[Base1]

    c1 = SomeConfig.model_validate({"config": {
        "type": "impl",
        "value": "some value",
    }})
    c2 = SomeConfig.model_validate({"config": {
        "type": "impl",
        "value": "some value",
        "number": 3,
    }})

    c3 = SomeConfig(config=Impl4(value="some value", number=3))

    assert isinstance(c1.config, Impl1)
    assert not isinstance(c1.config, Impl2)
    assert isinstance(c1.config, Impl5)

    assert isinstance(c2.config, Impl1)
    assert isinstance(c2.config, Impl2)
    assert not isinstance(c2.config, Impl3)
    assert isinstance(c2.config, Impl4)

    assert isinstance(c3.config, Impl1)
    assert isinstance(c3.config, Impl2)
    assert not isinstance(c3.config, Impl3)
    assert isinstance(c3.config, Impl4)

    try:
        SomeConfig(Impl2(number=3)) # type: ignore
        raise InvalidTestStateException("Impl2 is not a valid implementation of Base1 and should not be accepted by SomeConfig")
    except InvalidTestStateException:
        raise
    except:
        pass
