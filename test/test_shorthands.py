from typing import Literal
from pydantic import BaseModel
from plugantic import PluginModel, PluginAdapter, Field

from ._common import InvalidTestStateException

def test_shorthands_annotated():
    class TestBase(PluginModel):
        pass
        
    class TestImplText(TestBase):
        type: Literal["text"] = Field(default=...)
        text: str
        
    class TestImplNumber(TestBase):
        type: Literal["number", "num"] = Field(default=...)
        number: int|None = None
    
    EMPTY = TestImplText(text="").model_add_as_shorthand()
    TEST = TestImplText(text="test").model_add_as_shorthand("test")
    ZERO = TestImplNumber(number=0).model_add_as_shorthand()

    class OtherConfig(BaseModel):
        config: PluginAdapter[TestBase]

    OtherConfig(config=EMPTY)
    OtherConfig(config=TEST)
    OtherConfig(config=ZERO)
    OtherConfig(config="test") # pyright: ignore[reportArgumentType]
    OtherConfig(config=TestImplText(text="other text"))
    OtherConfig(config=TestImplNumber(number=3))

    c1 = OtherConfig.model_validate({"config": "text"})
    c2 = OtherConfig.model_validate({"config": "test"})
    c3 = OtherConfig.model_validate({"config": "number"})
    c4 = OtherConfig.model_validate({"config": "num"})
    c5 = OtherConfig.model_validate({"config": {"type": "text", "text": "other text"}})
    c6 = OtherConfig.model_validate({"config": {"type": "num", "number": 3}})

    assert isinstance(c1.config, TestImplText)
    assert c1.config.text == ""
    assert isinstance(c2.config, TestImplText)
    assert c2.config.text == "test"
    assert isinstance(c3.config, TestImplNumber)
    assert c3.config.number == 0
    assert isinstance(c4.config, TestImplNumber)
    assert c4.config.number == 0
    assert isinstance(c5.config, TestImplText)
    assert c5.config.text == "other text"
    assert isinstance(c6.config, TestImplNumber)
    assert c6.config.number == 3

    try:
        OtherConfig.model_validate({"config": "unknown"})
        raise InvalidTestStateException("Validation should fail for unknown shorthand")
    except InvalidTestStateException:
        raise
    except:
        pass

def test_shorthands_subclass_args():
    class TestBase(PluginModel):
        pass
        
    class TestImplText(TestBase, value="text"):
        text: str
        
    class TestImplNumber(TestBase, value=("number", "num")):
        number: int|None = None
    
    EMPTY = TestImplText(text="").model_add_as_shorthand()
    TEST = TestImplText(text="test").model_add_as_shorthand("test")
    ZERO = TestImplNumber(number=0).model_add_as_shorthand()

    class OtherConfig(BaseModel):
        config: PluginAdapter[TestBase]

    OtherConfig(config=EMPTY)
    OtherConfig(config=TEST)
    OtherConfig(config=ZERO)
    OtherConfig(config="test") # pyright: ignore[reportArgumentType]
    OtherConfig(config=TestImplText(text="other text"))
    OtherConfig(config=TestImplNumber(number=3))

    c1 = OtherConfig.model_validate({"config": "text"})
    c2 = OtherConfig.model_validate({"config": "test"})
    c3 = OtherConfig.model_validate({"config": "number"})
    c4 = OtherConfig.model_validate({"config": "num"})
    c5 = OtherConfig.model_validate({"config": {"type": "text", "text": "other text"}})
    c6 = OtherConfig.model_validate({"config": {"type": "num", "number": 3}})

    assert isinstance(c1.config, TestImplText)
    assert c1.config.text == ""
    assert isinstance(c2.config, TestImplText)
    assert c2.config.text == "test"
    assert isinstance(c3.config, TestImplNumber)
    assert c3.config.number == 0
    assert isinstance(c4.config, TestImplNumber)
    assert c4.config.number == 0
    assert isinstance(c5.config, TestImplText)
    assert c5.config.text == "other text"
    assert isinstance(c6.config, TestImplNumber)
    assert c6.config.number == 3

    try:
        OtherConfig.model_validate({"config": "unknown"})
        raise InvalidTestStateException("Validation should fail for unknown shorthand")
    except InvalidTestStateException:
        raise
    except:
        pass

def test_shorthands_subclass_config():
    class TestBase(PluginModel):
        pass
        
    class TestImplText(TestBase):
        text: str
        model_config = {"value": "text"}
        
    class TestImplNumber(TestBase):
        number: int|None = None
        model_config = {"value": ("number", "num")}
    
    EMPTY = TestImplText(text="").model_add_as_shorthand()
    TEST = TestImplText(text="test").model_add_as_shorthand("test")
    ZERO = TestImplNumber(number=0).model_add_as_shorthand()

    class OtherConfig(BaseModel):
        config: PluginAdapter[TestBase]

    OtherConfig(config=EMPTY)
    OtherConfig(config=TEST)
    OtherConfig(config=ZERO)
    OtherConfig(config="test") # pyright: ignore[reportArgumentType]
    OtherConfig(config=TestImplText(text="other text"))
    OtherConfig(config=TestImplNumber(number=3))

    c1 = OtherConfig.model_validate({"config": "text"})
    c2 = OtherConfig.model_validate({"config": "test"})
    c3 = OtherConfig.model_validate({"config": "number"})
    c4 = OtherConfig.model_validate({"config": "num"})
    c5 = OtherConfig.model_validate({"config": {"type": "text", "text": "other text"}})
    c6 = OtherConfig.model_validate({"config": {"type": "num", "number": 3}})

    assert isinstance(c1.config, TestImplText)
    assert c1.config.text == ""
    assert isinstance(c2.config, TestImplText)
    assert c2.config.text == "test"
    assert isinstance(c3.config, TestImplNumber)
    assert c3.config.number == 0
    assert isinstance(c4.config, TestImplNumber)
    assert c4.config.number == 0
    assert isinstance(c5.config, TestImplText)
    assert c5.config.text == "other text"
    assert isinstance(c6.config, TestImplNumber)
    assert c6.config.number == 3

    try:
        OtherConfig.model_validate({"config": "unknown"})
        raise InvalidTestStateException("Validation should fail for unknown shorthand")
    except InvalidTestStateException:
        raise
    except:
        pass

def test_shorthands_conflicting():
    class TestBase(PluginModel):
        pass
        
    class TestImpl1(TestBase, value="text"):
        text: str
        
    class TestImpl2(TestBase, value="number"):
        number: int|None = None

    try:
        TestImpl1(text="").model_add_as_shorthand("sh1")
        TestImpl2().model_add_as_shorthand("sh1")
        PluginAdapter[TestBase].model_json_schema()
        raise InvalidTestStateException("Conflicting shorthands should not be allowed")
    except InvalidTestStateException:
        raise
    except:
        pass

def test_shorthands_combined():
    class TestBase1(PluginModel):
        pass
        
    class TestImpl11(TestBase1, value="text"):
        text: str
        
    class TestImpl12(TestBase1, value="number"):
        number: int|None = None

    class TestBase2(PluginModel):
        pass

    class TestImpl21(TestBase2, value="bool"):
        flag: bool

    class TestImpl22(TestBase1, TestBase2, value="none"):
        pass

    TestBase1Ref = PluginAdapter[TestBase1]
    TestBase2Ref = PluginAdapter[TestBase2]

    TEXT1 = TestImpl11(text="").model_add_as_shorthand()
    NUMBER = TestImpl12().model_add_as_shorthand()
    BOOL = TestImpl21(flag=False).model_add_as_shorthand()
    NONE = TestImpl22().model_add_as_shorthand()

    class OtherConfig1(BaseModel):
        config: TestBase1Ref | TestBase2Ref

    class OtherConfig2(BaseModel):
        config: TestBase1Ref & TestBase2Ref # type: ignore[operator]

    c1 = OtherConfig1.model_validate({"config": "number"})
    c2 = OtherConfig1.model_validate({"config": "bool"})
    c3 = OtherConfig1.model_validate({"config": "text"})
    c4 = OtherConfig2.model_validate({"config": "none"})

    assert isinstance(c1.config, TestImpl12)
    assert isinstance(c2.config, TestImpl21)
    assert isinstance(c3.config, TestImpl11)
    assert isinstance(c4.config, TestImpl22)

    c5 = OtherConfig2.model_validate({"config": "none"})

    assert isinstance(c5.config, TestImpl22)

    try:
        OtherConfig2.model_validate({"config": "number"})
        raise InvalidTestStateException("Validation should fail for unknown shorthand")
    except InvalidTestStateException:
        raise
    except:
        pass

    try:
        OtherConfig2.model_validate({"config": "bool"})
        raise InvalidTestStateException("Validation should fail for unknown shorthand")
    except InvalidTestStateException:
        raise
    except:
        pass

    try:
        OtherConfig2.model_validate({"config": "text"})
        raise InvalidTestStateException("Validation should fail for unknown shorthand")
    except InvalidTestStateException:
        raise
    except:
        pass
