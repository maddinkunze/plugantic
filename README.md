# Plugantic - Simplify extendable composition with pydantic

## Why?

You may have learned that you should avoid inheritance in favor of composition. When using pydantic you can achieve that by using something like the following:

```python
# Declare a base config
class OutputConfig(BaseModel):
    mode: str
    def your_desired_functionality(self): ...

# Declare all implementations of the base config
class TextConfig(OutputConfig):
    mode: Literal["text"] = "text"
    text: str
    def your_desired_functionality(self):
        print(self.text)

class NumberConfig(OutputConfig):
    mode: Literal["number"] = "number"
    number: float
    precision: int = 2
    def your_desired_functionality(self):
        print(f"{self.number:.{self.precision}f}")

# Define a union type of all implementations
AllOutputConfigs = Annotated[Union[TextConfig, NumberConfig], Field(discriminator="mode")]

# Use the union type in your model
class CommonConfig(BaseModel):
    output: AllOutputConfigs

CommonConfig.model_validate({"output": {"mode": "text", "text": "Hello World"}})
```

Whilst this works, there are multiple issues and annoyances with that approach:
 - **Not extensible**: if one were to add a different config afterwards, the `AllOutputConfigs` type would need to be updated and so do all objects using it
 - **Weird maintainability**: you need to declare a type union and maintain it with every change
 - **Redundant definition**: of the discriminator field (i.e. `Literal[<x>] = <x>`)

This library solves all these issues (and more), so you can just write

```python
from plugantic import PluginModel

class OutputConfig(PluginModel):
    mode: str
    def your_desired_functionality(self): ...

class TextConfig(OutputConfig):
    mode: Literal["text"] # No redundant definition here!
    text: str
    def your_desired_functionality(self):
        print(self.text)

class NumberConfig(OutputConfig):
    mode: Literal["number"] # No redundant definition here either!
    number: float
    precision: int = 2
    def your_desired_functionality(self):
        print(f"{self.number:.{self.precision}f}")

# No need to define a union type or a discriminator field!
# You can just use the base type as a field type!
class CommonConfig(BaseModel):
    output: OutputConfig

# You can even add new plugins after the fact!
class BytesConfig(OutputConfig):
    mode: Literal["bytes"]
    content: bytes
    def your_desired_functionality(self):
        print(self.content.decode("utf-8"))

# The actual type is only evaluated when it is actually needed!
CommonConfig.model_validate({"output": {"mode": "text", "text": "Hello World"}})
```

## Features

### Extensibility

You can add new plugins after the fact!

### Type Checker Friendliness

The type checker can infer the type of the plugin model, so you don't need to define a union type or a discriminator field!
