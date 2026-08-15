from src.plugantic import PluginModel, PluginAdapter
from pydantic import BaseModel

def test_basic_nondiscriminated_usage():
    class Base(PluginModel, discriminator=None):
        pass
    
    class Impl1(Base):
        x: str
    
    class Impl2(Base):
        y: int
    
    class SomeConfig(BaseModel):
        config: PluginAdapter[Base]
    
    c1 = SomeConfig.model_validate({"config": {
        "x": "some value"
    }})
    c2 = SomeConfig.model_validate({"config": {
        "y": 3
    }})
    
    assert isinstance(c1.config, Impl1)
    assert not isinstance(c1.config, Impl2)
    
    assert not isinstance(c2.config, Impl1)
    assert isinstance(c2.config, Impl2)
    