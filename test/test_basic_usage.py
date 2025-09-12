from typing_extensions import Literal
from plugantic import PluginModel
from pydantic import BaseModel

def test_basic_usage_subclass_args():
    class TestBase(PluginModel):
        value: str

    class TestImplText(TestBase, value="text"):
        text: str

    class TestImplNumber(TestBase, value="number"):
        number: int|None = None

    class TestImplNumberStrict(TestImplNumber, value="number-strict"):
        number: int = 0

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
        type: Literal["text"]
        text: str
        
    class TestImplNumber(TestBase):
        type: Literal["number"]
        number: int|None = None
        
    class TestImplNumberStrict(TestImplNumber):
        type: Literal["number-strict"]
        number: int = 0
        
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

def test_basic_usage_subclass_config():
    class TestBase(PluginModel):
        value: str
        
    class TestImplText(TestBase):
        text: str
        plugantic_config = {"value": "text"}
        
    class TestImplNumber(TestBase):
        number: int|None = None
        plugantic_config = {"value": "number"}
        
    class TestImplNumberStrict(TestImplNumber):
        number: int = 0
        plugantic_config = {"value": "number-strict"}
        
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

