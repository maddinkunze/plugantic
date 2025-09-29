from typing_extensions import Literal
from plugantic import PluginModel, PluginDowncastHandler, PluginFeature
from pydantic import BaseModel, Field

def test_missing_field_inheritance():
    Feature = PluginFeature["feature1"]

    def enable_feature(handler: PluginDowncastHandler):
        handler.enable_feature(Feature)
        handler.set_field_annotation("a", int)

    class Base(PluginModel):
        type: Literal["feature"]
        a: int|None = Field(default=3)

        plugantic_config = {"auto_downcasts": (enable_feature,)}
    
    
    class SomeConfig(BaseModel):
        config: Base[Feature]

    SomeConfig.model_validate({"config": {
        "type": "feature",
        "a": 1
    }})

    try:
        SomeConfig.model_validate({"config": {
            "type": "feature",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

def test_enable_field_inheritance():
    Feature = PluginFeature["feature1"]

    def enable_feature(handler: PluginDowncastHandler):
        handler.enable_feature(Feature)
        handler.set_field_annotation("a", int, merge_with_existing=True)

    class Base(PluginModel):
        type: Literal["feature"]
        a: int|None = Field(default=3)

        plugantic_config = {"auto_downcasts": (enable_feature,)}
    
    
    class SomeConfig(BaseModel):
        config: Base[Feature]

    SomeConfig.model_validate({"config": {
        "type": "feature",
        "a": 1
    }})

    SomeConfig.model_validate({"config": {
        "type": "feature",
    }})
