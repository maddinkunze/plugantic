from typing import Literal
from pydantic import BaseModel
from plugantic import PluginModel, Field

def test_shorthands_annotated():
    class TestBase(PluginModel):
        pass
        
    class TestImplText(TestBase):
        type: Literal["text"] = Field(default=...)
        text: str
        
    class TestImplNumber(TestBase):
        type: Literal["number", "num"] = Field(default=...)
        number: int|None = None
    
    EMPTY = TestImplText(text="").register_as_shorthand()
    TEST = TestImplText(text="test").register_as_shorthand("test")
    ZERO = TestImplNumber(number=0).register_as_shorthand()

    class OtherConfig(BaseModel):
        config: TestBase

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
        assert False
    except AssertionError:
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
    
    EMPTY = TestImplText(text="").register_as_shorthand()
    TEST = TestImplText(text="test").register_as_shorthand("test")
    ZERO = TestImplNumber(number=0).register_as_shorthand()

    class OtherConfig(BaseModel):
        config: TestBase

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
        assert False
    except AssertionError:
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
    
    EMPTY = TestImplText(text="").register_as_shorthand()
    TEST = TestImplText(text="test").register_as_shorthand("test")
    ZERO = TestImplNumber(number=0).register_as_shorthand()

    class OtherConfig(BaseModel):
        config: TestBase

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
        assert False
    except AssertionError:
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
        TestImpl1(text="").register_as_shorthand("sh1")
        TestImpl2().register_as_shorthand("sh1")
        TestBase.model_json_schema()
        assert False
    except AssertionError:
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

    class TestImpl21(TestBase2, value="text"):
        text: str

    class TestImpl22(TestBase2, value="bool"):
        flag: bool

    TEXT1 = TestImpl11(text="").register_as_shorthand()
    NUMBER = TestImpl12().register_as_shorthand()
    TEXT2 = TestImpl21(text="").register_as_shorthand()
    BOOL = TestImpl22(flag=False).register_as_shorthand()

    class OtherConfig1(BaseModel):
        config: TestBase1 | TestBase2

    class OtherConfig2(BaseModel):
        config: TestBase1 & TestImpl11 # type: ignore[operator]

    c1 = OtherConfig1.model_validate({"config": "number"})
    c2 = OtherConfig1.model_validate({"config": "bool"})

    assert isinstance(c1.config, TestImpl12)
    assert isinstance(c2.config, TestImpl22)

    try:
        OtherConfig1.model_validate({"config": "text"})
        assert False
    except AssertionError:
        raise
    except:
        pass

    c3 = OtherConfig2.model_validate({"config": "text"})

    assert isinstance(c3.config, TestImpl11)

    try:
        OtherConfig2.model_validate({"config": "number"})
        assert False
    except AssertionError:
        raise
    except:
        pass

    try:
        OtherConfig2.model_validate({"config": "bool"})
        assert False
    except AssertionError:
        raise
    except:
        pass

