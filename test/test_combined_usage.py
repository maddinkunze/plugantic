from typing import Literal
from plugantic import PluginModel, PluginAdapter, PluginIntersection
from pydantic import BaseModel

from ._common import InvalidTestStateException

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

    BaseRef = PluginAdapter[Base]
    Feature1Ref = PluginAdapter[Feature1]
    Feature2Ref = PluginAdapter[Feature2]
    Feature3Ref = PluginAdapter[Feature3]

    class Config1(BaseModel):
        config: BaseRef

    class Config2(BaseModel):
        config: Feature1Ref

    class Config3(BaseModel):
        config: PluginIntersection[Feature1Ref, Feature2Ref] # type: ignore[operator]
        
    class Config4(BaseModel):
        config: Feature1Ref | Feature3Ref

    class Config5(BaseModel):
        config: PluginIntersection[Feature1Ref, Feature2Ref] | Feature3Ref # type: ignore[operator]

    Config1.model_validate({"config": {"type": "impl1"}})
    Config2.model_validate({"config": {"type": "impl1"}})
    Config3.model_validate({"config": {"type": "impl1"}})
    Config4.model_validate({"config": {"type": "impl1"}})
    Config5.model_validate({"config": {"type": "impl1"}})

    Config1.model_validate({"config": {"type": "impl2"}})
    
    try:
        Config2.model_validate({"config": {"type": "impl2"}})
        raise InvalidTestStateException("Impl2 should not be valid for Config2")
    except InvalidTestStateException:
        raise
    except:
        pass

    try:
        Config3.model_validate({"config": {"type": "impl2"}})
        raise InvalidTestStateException("Impl2 should not be valid for Config3")
    except InvalidTestStateException:
        raise
    except:
        pass
        
    Config4.model_validate({"config": {"type": "impl2"}})
    Config5.model_validate({"config": {"type": "impl2"}})

    Config1.model_validate({"config": {"type": "impl3"}})
        
    try:
        Config2.model_validate({"config": {"type": "impl3"}})
        raise InvalidTestStateException("Impl3 should not be valid for Config2")
    except InvalidTestStateException:
        raise
    except:
        pass
        
    try:
        Config3.model_validate({"config": {"type": "impl3"}})
        raise InvalidTestStateException("Impl3 should not be valid for Config3")
    except InvalidTestStateException:
        raise
    except:
        pass
        
    Config4.model_validate({"config": {"type": "impl3"}})
    Config5.model_validate({"config": {"type": "impl3"}})

    Config1.model_validate({"config": {"type": "impl4"}})
    
    try:
        Config2.model_validate({"config": {"type": "impl4"}})
        raise InvalidTestStateException("Impl4 should not be valid for Config2")
    except InvalidTestStateException:
        raise
    except:
        pass
        
    try:
        Config3.model_validate({"config": {"type": "impl4"}})
        raise InvalidTestStateException("Impl4 should not be valid for Config3")
    except InvalidTestStateException:
        raise
    except:
        pass
        
    try:
        Config4.model_validate({"config": {"type": "impl4"}})
        raise InvalidTestStateException("Impl4 should not be valid for Config4")
    except InvalidTestStateException:
        raise
    except:
        pass

    try:
        Config5.model_validate({"config": {"type": "impl4"}})
        raise InvalidTestStateException("Impl4 should not be valid for Config5")
    except InvalidTestStateException:
        raise
    except:
        pass
