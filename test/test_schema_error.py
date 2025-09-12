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
    except ValueError:
        pass
    except:
        raise

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
