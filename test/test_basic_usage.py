from typing_extensions import Literal
from plugantic import PluginModel, Field
from pydantic import BaseModel

def test_basic_usage_subclass_args():
    class TestBase(PluginModel):
        value: str

    class TestImplText(TestBase, value="text"):
        text: str

    class TestImplNumber(TestBase, value="number"):
        number: int|None = None

    class TestImplNumberStrict(TestImplNumber, value="number-strict"):
        number: int = 0 # pyright: ignore[reportIncompatibleVariableOverride]

    class OtherConfig(BaseModel):
        config: TestBase

    OtherConfig(config=TestImplText(value="some text", text="other text"))
    OtherConfig(config=TestImplNumber(value="some number"))
    OtherConfig(config=TestImplNumberStrict(value="strict number", number=3))

    c1 = OtherConfig.model_validate({"config": {
        "type": "text",
        "value": "some text",
        "text": "other text",        
    }})

    c2 = OtherConfig.model_validate({"config": {
        "type": "number",
        "value": "some number",
        "number": None,
    }})

    c3 = OtherConfig.model_validate({"config": {
        "type": "number-strict",
        "value": "strict number",
        "number": 7,
    }})

    assert isinstance(c1.config, TestImplText)
    assert isinstance(c2.config, TestImplNumber)
    assert not isinstance(c2.config, TestImplNumberStrict)
    assert isinstance(c3.config, TestImplNumberStrict)

def test_basic_usage_subclass_annotated():
    class TestBase(PluginModel):
        value: str
        
    class TestImplText(TestBase):
        type: Literal["text"] = Field(default=...)
        text: str
        
    class TestImplNumber(TestBase):
        type: Literal["number"]
        number: int|None = None
        
    class TestImplNumberStrict(TestImplNumber):
        type: Literal["number-strict"] # pyright: ignore[reportIncompatibleVariableOverride]
        number: int = 0 # pyright: ignore[reportIncompatibleVariableOverride]
        
    class OtherConfig(BaseModel):
        config: TestBase
        
    OtherConfig(config=TestImplText(value="some text", text="other text"))
    OtherConfig(config=TestImplNumber(value="some number")) # pyright: ignore[reportCallIssue]
    OtherConfig(config=TestImplNumberStrict(value="strict number", number=3)) # pyright: ignore[reportCallIssue]
    
    c1 = OtherConfig.model_validate({"config": {
        "type": "text",
        "value": "some text",
        "text": "other text",        
    }})
    
    c2 = OtherConfig.model_validate({"config": {
        "type": "number",
        "value": "some number",
        "number": None,
    }})
    
    c3 = OtherConfig.model_validate({"config": {
        "type": "number-strict",
        "value": "strict number",
        "number": 7,
    }})
    
    assert isinstance(c1.config, TestImplText)
    assert isinstance(c2.config, TestImplNumber)
    assert not isinstance(c2.config, TestImplNumberStrict)
    assert isinstance(c3.config, TestImplNumberStrict)

def test_basic_usage_subclass_config():
    class TestBase(PluginModel):
        value: str
        
    class TestImplText(TestBase):
        text: str
        model_config = {"value": "text"}
        
    class TestImplNumber(TestBase):
        number: int|None = None
        model_config = {"value": "number"}
        
    class TestImplNumberStrict(TestImplNumber):
        number: int = 0 # pyright: ignore[reportIncompatibleVariableOverride]
        model_config = {"value": "number-strict"}
        
    class OtherConfig(BaseModel):
        config: TestBase
        
    OtherConfig(config=TestImplText(value="some text", text="other text"))
    OtherConfig(config=TestImplNumber(value="some number"))
    OtherConfig(config=TestImplNumberStrict(value="strict number", number=3))
    
    c1 = OtherConfig.model_validate({"config": {
        "type": "text",
        "value": "some text",
        "text": "other text",        
    }})
    
    c2 = OtherConfig.model_validate({"config": {
        "type": "number",
        "value": "some number",
        "number": None,
    }})
    
    c3 = OtherConfig.model_validate({"config": {
        "type": "number-strict",
        "value": "strict number",
        "number": 7,
    }})
    
    assert isinstance(c1.config, TestImplText)
    assert isinstance(c2.config, TestImplNumber)
    assert not isinstance(c2.config, TestImplNumberStrict)
    assert isinstance(c3.config, TestImplNumberStrict)

def test_basic_usage_multiple_values():
    class TestBase(PluginModel, varname_type="type"):
        pass

    class TestImplText(TestBase, value=["text", "str"]):
        text: str

    class TestImplNumber(TestBase):
        number: int
        model_config = {"value": ["number", "num"]}

    class TestImplEmpty(TestBase):
        type: Literal["empty", "none"] = Field(default=...)

    class OtherConfig(BaseModel):
        config: TestBase

    OtherConfig(config=TestImplText(text="other text"))
    OtherConfig(config=TestImplNumber(number=3))
    OtherConfig(config=TestImplEmpty())

    c1 = OtherConfig.model_validate({"config": {
        "type": "text",
        "text": "some text",
    }})

    c2 = OtherConfig.model_validate({"config": {
        "type": "str",
        "text": "other text",
    }})

    c3 = OtherConfig.model_validate({"config": {
        "type": "number",
        "number": 3,
    }})

    c4 = OtherConfig.model_validate({"config": {
        "type": "num",
        "number": 3,
    }})

    c5 = OtherConfig.model_validate({"config": {
        "type": "empty",
    }})

    c6 = OtherConfig.model_validate({"config": {
        "type": "none",
    }})

    assert isinstance(c1.config, TestImplText)
    assert isinstance(c2.config, TestImplText)
    assert isinstance(c3.config, TestImplNumber)
    assert isinstance(c4.config, TestImplNumber)
    assert isinstance(c5.config, TestImplEmpty)
    assert isinstance(c6.config, TestImplEmpty)
