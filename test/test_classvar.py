from typing_extensions import Literal, ClassVar
from plugantic import PluginModel, PluginDowncastHandler, PluginFeature
from pydantic import BaseModel, Field

def test_classvar():
    Feature = PluginFeature["feature1"]

    def enable_feature(handler: PluginDowncastHandler):
        handler.enable_feature(Feature)
        handler.set_class_var("test", 2)

    class Base(PluginModel):
        type: Literal["feature"]
        a: int|None = Field(default=3)

        test: ClassVar[int] = 1

        plugantic_config = {"auto_downcasts": (enable_feature,)}
        
    
    class SomeConfig1(BaseModel):
        config: Base

    v = SomeConfig1.model_validate({"config": {
        "type": "feature",
        "a": 1
    }})

    assert v.config.test == 1


    class SomeConfig2(BaseModel):
        config: Base[Feature]

    v = SomeConfig2.model_validate({"config": {
        "type": "feature",
        "a": 1
    }})

    assert v.config.test == 2

def test_feature_classvar():
    Feature = PluginFeature["feature1"]
    ClassVar[Feature] # should not throw an error
