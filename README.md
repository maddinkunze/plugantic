# Plugantic - Simplify extendable composition with pydantic

## Why?

You may have learned that you should avoid inheritance in favor of composition. When using pydantic you can achieve that by using something like the following:

```python
# Declare a base config
class OutputConfig(BaseModel):
    mode: str
    def print(self): ...

# Declare all implementations of the base config
class TextConfig(OutputConfig):
    mode: Literal["text"] = "text"
    text: str
    def print(self):
        print(self.text)

class NumberConfig(OutputConfig):
    mode: Literal["number"] = "number"
    number: float
    precision: int = 2
    def print(self):
        print(f"{self.number:.{self.precision}f}")

# Define a union type of all implementations
AllOutputConfigs = Annotated[Union[
    TextConfig,
    NumberConfig,
], Field(discriminator="mode")]

# Use the union type in your model
class CommonConfig(BaseModel):
    output: AllOutputConfigs

...

CommonConfig.model_validate({"output": {
    "mode": "text",
    "text": "Hello World"
}})
```

Whilst this works, there are multiple issues and annoyances with that approach:
 - **Hard to maintain**: you need to declare a type union and update it with every change
 - **Not extensible**: adding a different config afterwards would required to updatethe `AllOutputConfigs` type and all the objects using it
 - **Redundant definition** of the discriminator field (i.e. `Literal[<x>] = <x>`)

This library solves all of these issues (and more), so you can just write

```python
from plugantic import PluginModel

class OutputConfig(PluginModel):
    mode: str
    def print(self): ...

class TextConfig(OutputConfig):
    # No redundant "text" definition here!
    mode: Literal["text"]
    text: str
    def print(self):
        print(self.text)

class NumberConfig(OutputConfig):
    # No redundant definition here either!
    mode: Literal["number"]
    number: float
    precision: int = 2
    def print(self):
        print(f"{self.number:.{self.precision}f}")

# No need to define a union type or a discriminator field!
# You can just use the base type as a field type!
class CommonConfig(BaseModel):
    output: OutputConfig

# You can even add new configs after the fact!
class BytesConfig(OutputConfig):
    mode: Literal["bytes"]
    content: bytes
    def print(self):
        print(self.content.decode("utf-8"))

...

# The actual type is only evaluated when it is actually needed!
CommonConfig.model_validate({"output": {
    "mode": "text",
    "text": "Hello World"
}})
```

## Features

### Extensibility

You can add new plugins after the fact!

### Type Checker Friendliness

The type checker can infer the type of the plugin model, so you don't need to define a union type or a discriminator field!
