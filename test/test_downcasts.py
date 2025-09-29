from typing_extensions import Literal, TypeAlias
from plugantic import PluginModel, PluginDowncastHandler, PluginFeature
from pydantic import BaseModel

def test_auto_downcasts():
    Feature1: TypeAlias = PluginFeature["feature1"]
    Feature2: TypeAlias = PluginFeature["feature2"]
    Feature3: TypeAlias = PluginFeature["feature3"]

    class TestBase(PluginModel):
        pass

    class TestImpl1(TestBase[Feature1]):
        type: Literal["test1"]

    def enable_feature1(handler: PluginDowncastHandler):
        handler.enable_feature(Feature1)
        handler.set_field_annotation("text", str)
        handler.remove_field_default("text")

    def enable_feature2(handler: PluginDowncastHandler):
        handler.enable_feature(Feature2)
        handler.set_field_annotation("number", int)
        handler.set_field_default("number", 3)

    def enable_feature3(handler: PluginDowncastHandler):
        handler.enable_feature(Feature3)
        handler.set_field_annotation("unit", str)
        

    class TestImpl2(TestBase, auto_downcasts=((enable_feature1, enable_feature2), enable_feature3)):
        type: Literal["test2"]
        text: str|None = None
        number: int|None = None
        unit: str|None = "cm"


    class SomeConfig1(BaseModel):
        config: TestBase[Feature1]

    class SomeConfig2(BaseModel):
        config: TestBase[Feature1, Feature2]

    class SomeConfig3(BaseModel):
        config: TestBase[Feature1, Feature3]

    
    SomeConfig1.model_validate({"config": {"type": "test1"}})

    SomeConfig1.model_validate({"config": {
        "type": "test2",
        "text": "some text",
    }})

    SomeConfig1.model_validate({"config": {
        "type": "test2",
        "text": "some text",
        "number": 3,
        "unit": "cm",
    }})

    try:
        SomeConfig1.model_validate({"config": {
            "type": "test2",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        SomeConfig2.model_validate({"config": {
            "type": "test2",
            "text": "some text",
            "number": 3,
            "unit": "cm",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    SomeConfig3.model_validate({"config": {
        "type": "test2",
        "text": "some text",
        "unit": "cm",
    }})

    SomeConfig3.model_validate({"config": {
        "type": "test2",
        "text": "some text",
        "number": 3,
        "unit": "cm",
    }})
