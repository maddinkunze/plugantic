from typing import Literal
from plugantic import PluginModel
from pydantic import BaseModel

def test_combined_usage():
    class Base(PluginModel):
        pass

    class Feature1(Base):
        pass

    class Feature2(Base):
        pass
    
    class Feature3(Base):
        pass
    
    class Impl1(Feature1, Feature2):
        type: Literal["impl1"] = "impl1"

    class Impl2(Feature2, Feature3):
        type: Literal["impl2"] = "impl2"

    class Impl3(Feature3):
        type: Literal["impl3"] = "impl3"

    class Impl4(Base):
        type: Literal["impl4"] = "impl4"

    class Config1(BaseModel):
        config: Base

    class Config2(BaseModel):
        config: Feature1

    class Config3(BaseModel):
        config: Feature1 & Feature2 # type: ignore[operator]
        
    class Config4(BaseModel):
        config: Feature1 | Feature3

    class Config5(BaseModel):
        config: (Feature1 & Feature2) | Feature3 # type: ignore[operator]

    Config1.model_validate({"config": {"type": "impl1"}})
    Config2.model_validate({"config": {"type": "impl1"}})
    Config3.model_validate({"config": {"type": "impl1"}})
    Config4.model_validate({"config": {"type": "impl1"}})
    Config5.model_validate({"config": {"type": "impl1"}})

    Config1.model_validate({"config": {"type": "impl2"}})
    
    try:
        Config2.model_validate({"config": {"type": "impl2"}})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        Config3.model_validate({"config": {"type": "impl2"}})
        assert False
    except AssertionError:
        raise
    except:
        pass
        
    Config4.model_validate({"config": {"type": "impl2"}})
    Config5.model_validate({"config": {"type": "impl2"}})

    Config1.model_validate({"config": {"type": "impl3"}})
        
    try:
        Config2.model_validate({"config": {"type": "impl3"}})
        assert False
    except AssertionError:
        raise
    except:
        pass
        
    try:
        Config3.model_validate({"config": {"type": "impl3"}})
        assert False
    except AssertionError:
        raise
    except:
        pass
        
    Config4.model_validate({"config": {"type": "impl3"}})
    Config5.model_validate({"config": {"type": "impl3"}})

    Config1.model_validate({"config": {"type": "impl4"}})
    
    try:
        Config2.model_validate({"config": {"type": "impl4"}})
        assert False
    except AssertionError:
        raise
    except:
        pass
        
    try:
        Config3.model_validate({"config": {"type": "impl4"}})
        assert False
    except AssertionError:
        raise
    except:
        pass
        
    try:
        Config4.model_validate({"config": {"type": "impl4"}})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        Config5.model_validate({"config": {"type": "impl4"}})
        assert False
    except AssertionError:
        raise
    except:
        pass
