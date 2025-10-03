from typing import Literal
from plugantic import PluginModel
from pydantic import BaseModel

def test_auto_downcast():
    class Base(PluginModel):
        pass
        
    class Feature1(Base):
        pass

    class Impl1(Base):
        type: Literal["impl1"]
        value: str|None

    class Impl2(Impl1, Feature1):
        value: str

    class Impl3(Impl1):
        pass

    class Config1(BaseModel):
        config: Base

    class Config2(BaseModel):
        config: Feature1

    Config1.model_validate({"config": {"type": "impl1", "value": None}})
    Config1.model_validate({"config": {"type": "impl1", "value": "text"}})

    Config1.model_validate({"config": Impl1(value=None)})
    Config1.model_validate({"config": Impl1(value="text")})

    Config1.model_validate({"config": Impl2(value="text")})

    Config1.model_validate({"config": Impl3(value=None)})
    Config1.model_validate({"config": Impl3(value="text")})

    try:
        Config2.model_validate({"config": {"type": "impl1", "value": None}})
        assert False
    except ValueError:
        pass
    except:
        raise

    Config2.model_validate({"config": {"type": "impl1", "value": "text"}})

    try:
        Config2.model_validate({"config": Impl1(value=None)})
        assert False
    except ValueError:
        pass
    except:
        raise

    Config2.model_validate({"config": Impl1(value="text")})
    Config2.model_validate({"config": Impl2(value="text")})
