from typing_extensions import Literal, TypeAlias
from plugantic import PluginModel, PluginFeature
from pydantic import BaseModel

def test_feature_usage_subclass_getitem():
    Feature1: TypeAlias = PluginFeature["feature1"]
    Feature2: TypeAlias = PluginFeature["feature2"]
    
    class TestBase(PluginModel):
        value: str

    class TestImpl1(TestBase[Feature1]):
        type: Literal["test1"]

    class TestImpl2(TestBase[Feature2]):
        type: Literal["test2"]

    class TestImpl3(TestBase[Feature1, Feature2]):
        type: Literal["test3"]


    class OtherConfig1(BaseModel):
        config: TestBase[Feature1]

    class OtherConfig2(BaseModel):
        config: TestBase[Feature2]

    class OtherConfig3(BaseModel):
        config: TestBase[Feature1, Feature2]
    

    OtherConfig1.model_validate({"config": {
        "type": "test1",
        "value": "some value",
    }})

    try:
        OtherConfig1.model_validate({"config": {
            "type": "test2",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    OtherConfig1.model_validate({"config": {
        "type": "test3",
        "value": "some value",
    }})

    try:
        OtherConfig2.model_validate({"config": {
            "type": "test1",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    OtherConfig2.model_validate({"config": {
        "type": "test2",
        "value": "some value",
    }})
    
    OtherConfig2.model_validate({"config": {
        "type": "test3",
        "value": "some value",
    }})

    try:
        OtherConfig3.model_validate({"config": {
            "type": "test1",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        OtherConfig3.model_validate({"config": {
            "type": "test2",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    OtherConfig3.model_validate({"config": {
        "type": "test3",
        "value": "some value",
    }})


def test_feature_usage_oneof():
    Feature1: TypeAlias = PluginFeature["feature1"]
    Feature2: TypeAlias = PluginFeature["feature2"]
    Feature3: TypeAlias = PluginFeature["feature3"]
    
    class TestBase(PluginModel):
        value: str
    
    class TestImpl1(TestBase[Feature1]):
        type: Literal["test1"]
    
    class TestImpl2(TestBase[Feature2]):
        type: Literal["test2"]
    
    class TestImpl3(TestBase[Feature1, Feature2]):
        type: Literal["test3"]
    
    class TestImpl4(TestBase[Feature1, Feature3]):
        type: Literal["test4"]
    
    
    class OtherConfig1(BaseModel):
        config: TestBase[Feature1|Feature2]

    class OtherConfig2(BaseModel):
        config: TestBase[Feature1|Feature2, Feature3]
    

    OtherConfig1.model_validate({"config": {
        "type": "test1",
        "value": "some value",
    }})

    OtherConfig1.model_validate({"config": {
        "type": "test2",
        "value": "some value",
    }})
    
    OtherConfig1.model_validate({"config": {
        "type": "test3",
        "value": "some value",
    }})

    OtherConfig1.model_validate({"config": {
        "type": "test4",
        "value": "some value",
    }})

    try:
        OtherConfig2.model_validate({"config": {
            "type": "test1",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        OtherConfig2.model_validate({"config": {
            "type": "test2",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        OtherConfig2.model_validate({"config": {
            "type": "test3",
            "value": "some value",
        }})
        assert False
    except AssertionError:
        raise
    except:
        pass

    OtherConfig2.model_validate({"config": {
        "type": "test4",
        "value": "some value",
    }})

def test_feature_usage_mixed():
    Feature1: TypeAlias = PluginFeature["feature1"]
    Feature2: TypeAlias = PluginFeature["feature2"]
    Feature3: TypeAlias = PluginFeature["feature3"]
    
    class TestBase(PluginModel):
        value: str
    
    class TestImpl1(TestBase[Feature1]):
        type: Literal["test1"]
    
    class TestImpl2(TestBase[Feature2]):
        type: Literal["test2"]
    
    class TestImpl3(TestBase[Feature1, Feature2]):
        type: Literal["test3"]
    
    class OtherConfig(BaseModel):
        config: TestBase
    
    OtherConfig(config=TestImpl1(value="some value"))
    OtherConfig(config=TestImpl2(value="some value"))
    OtherConfig(config=TestImpl3(value="some value"))

    OtherConfig.model_validate({"config": {
        "type": "test1",
        "value": "some value",
    }})
    OtherConfig.model_validate({"config": {
        "type": "test2",
        "value": "some value",
    }})
    OtherConfig.model_validate({"config": {
        "type": "test3",
        "value": "some value",
    }})
