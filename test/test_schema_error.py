from plugantic import PluginModel
from pydantic import BaseModel

def test_schema_error():
    class TestBase(PluginModel):
        value: str

    class TestImpl1(TestBase, value="text"):
        text: str

    class TestImpl2(TestBase, value="number"):
        number: int|None = None

    class OtherConfig(BaseModel):
        config: TestBase

    try:
        class TestImpl3(TestBase, value="image"):
            size: int = 0
        assert False
    except AssertionError:
        raise
    except:
        pass

def test_schema_error_fix():
    class TestBase(PluginModel):
        value: str

    class TestImpl1(TestBase, value="text"):
        text: str

    class TestImpl2(TestBase, value="number"):
        number: int|None = None

    class OtherConfig(BaseModel):
        config: TestBase

        model_config = {"defer_build": True}

    class TestImpl3(TestBase, value="image"):
        size: int = 0

    config = OtherConfig.model_validate({"config": {
        "type": "image",
        "value": "image",
        "size": 0,
    }})
        
    assert isinstance(config.config, TestImpl3)

def test_schema_no_valid_value():
    class TestBase(PluginModel):
        pass

    class OtherConfig(BaseModel):
        config: TestBase

    schema = OtherConfig.model_json_schema() # should not raise an error
    assert schema["properties"]["config"]["not"] == {} # should be a schema that matches nothing

    try:
        OtherConfig.model_validate({"config": {}})
        assert False
    except AssertionError:
        raise
    except:
        pass
