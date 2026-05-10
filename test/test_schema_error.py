from plugantic import PluginModel, PluginAdapter
from pydantic import BaseModel

from ._common import InvalidTestStateException

def test_schema_error():
    class TestBase(PluginModel):
        value: str

    class TestImpl1(TestBase, value="text"):
        text: str

    class TestImpl2(TestBase, value="number"):
        number: int|None = None

    class OtherConfig(BaseModel):
        config: PluginAdapter[TestBase]

    try:
        class TestImpl3(TestBase, value="image"):
            size: int = 0
        raise InvalidTestStateException("Creating a new subclass (TestImpl3) of already collected TestBase should not be allowed")
    except InvalidTestStateException:
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
        config: PluginAdapter[TestBase]

        model_config = {"defer_build": True}

    class TestImpl3(TestBase, value="image"):
        size: int = 0

    config = OtherConfig.model_validate({"config": {
        "type": "image",
        "value": "image",
        "size": 0,
    }})
        
    assert isinstance(config.config, TestImpl3)

def test_schema_error_suppress():
    class TestBase(PluginModel):
        value: str

    class TestImpl1(TestBase, value="text"):
        text: str

    class TestImpl2(TestBase, value="number"):
        number: int|None = None

    class OtherConfig(BaseModel):
        config: PluginAdapter[TestBase]

    class TestImpl3(TestBase, value="image", allow_changes_after_collection=True):
        size: int = 0

    try:
        OtherConfig.model_validate({"config": {
            "type": "image",
            "value": "image",
            "size": 0,
        }})
        raise InvalidTestStateException("Creating a new subclass (TestImpl3) of already collected TestBase should not be allowed")
    except InvalidTestStateException:
        raise
    except:
        pass

    config = OtherConfig(config=TestImpl3(value="image"))
    assert isinstance(config.config, TestImpl3)

def test_schema_no_valid_value():
    class TestBase(PluginModel):
        pass

    class OtherConfig(BaseModel):
        config: PluginAdapter[TestBase]

    schema = OtherConfig.model_json_schema() # should not raise an error
    assert schema["properties"]["config"]["not"] == {} # should be a schema that matches nothing

    try:
        OtherConfig.model_validate({"config": {}})
        raise InvalidTestStateException("Validation should fail when no valid implementations are available")
    except InvalidTestStateException:
        raise
    except:
        pass
