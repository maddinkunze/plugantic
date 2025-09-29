from typing_extensions import Literal
from plugantic import PluginModel, PluginDowncastHandler, PluginFeature
from pydantic import BaseModel

def test_recursive_annotation():
    Feature1 = PluginFeature["feature1"]
    Feature2 = PluginFeature["feature2"]
    
    class TestBase(PluginModel):
        pass

    def enable_feature2(handler: PluginDowncastHandler):
        handler.enable_feature(Feature2)
        handler.require_recursive_features("test", Feature2)

    class RecursiveTestImpl(TestBase[Feature1]):
        type: Literal["recursive"]
        test: TestBase[Feature1]

        plugantic_config = {"auto_downcasts": (enable_feature2,)}

    class TestImpl1(TestBase[Feature1]):
        type: Literal["test1"]

    class TestImpl2(TestBase[Feature1, Feature2]):
        type: Literal["test2"]

    
    class SomeConfig1(BaseModel):
        config: TestBase[Feature1]

    class SomeConfig2(BaseModel):
        config: TestBase[Feature1, Feature2]
        
    #breakpoint()
    SomeConfig1.model_validate({"config": {"type": "test1"}})
    SomeConfig1.model_validate({"config": {"type": "recursive", "test": {"type": "test1"}}})
    SomeConfig1.model_validate({"config": {"type": "recursive", "test": {"type": "test2"}}})

    SomeConfig2.model_validate({"config": {"type": "test2"}})

    try:
        SomeConfig2.model_validate({"config": {"type": "recursive", "test": {"type": "test1"}}})
        assert False
    except AssertionError:
        raise
    except:
        pass

    SomeConfig2.model_validate({"config": {"type": "recursive", "test": {"type": "test2"}}})

def test_mutual_exclusive_recursive_annotation():
    Feature1 = PluginFeature["feature1"]
    Feature2 = PluginFeature["feature2"]
    
    class TestBase(PluginModel):
        pass

    def enable_feature1(handler: PluginDowncastHandler):
        handler.enable_feature(Feature1)
        handler.require_recursive_features("test", Feature2)

    def enable_feature2(handler: PluginDowncastHandler):
        handler.enable_feature(Feature2)
        handler.require_recursive_features("test", Feature1)

    class RecursiveTestImpl(TestBase):
        type: Literal["recursive"]
        test: TestBase

        plugantic_config = {"auto_downcasts": ((enable_feature1, enable_feature2),)}

    class TestImpl1(TestBase[Feature1]):
        type: Literal["test1"]

    class TestImpl2(TestBase[Feature2]):
        type: Literal["test2"]

    
    class SomeConfig1(BaseModel):
        config: TestBase[Feature1]

    class SomeConfig2(BaseModel):
        config: TestBase[Feature2]
        
    #breakpoint()
    SomeConfig1.model_validate({"config": {"type": "test1"}})
    SomeConfig1.model_validate({"config": {"type": "recursive", "test": {"type": "test2"}}})

    try:
        SomeConfig1.model_validate({"config": {"type": "recursive", "test": {"type": "test1"}}})
        assert False
    except AssertionError:
        raise
    except:
        pass

    SomeConfig2.model_validate({"config": {"type": "test2"}})
    SomeConfig2.model_validate({"config": {"type": "recursive", "test": {"type": "test1"}}})

    try:
        SomeConfig2.model_validate({"config": {"type": "recursive", "test": {"type": "test2"}}})
        assert False
    except AssertionError:
        raise
    except:
        pass
