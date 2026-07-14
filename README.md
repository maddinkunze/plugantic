# 🧩 Plugantic - Simplified extendable composition with pydantic

## 🤔 Why use `plugantic`?

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
 - **Not extensible**: adding a different config afterwards would required to update the `AllOutputConfigs` type and all of the objects using it
 - **Redundant definition** of the discriminator field (i.e. `Literal[<x>] = <x>`)

This library solves all of these issues (and more), so you can just write

```python
from plugantic import PluginModel, PluginAdapter

class OutputConfig(PluginModel, varname_type="mode"):
    def print(self): ...

class TextConfig(OutputConfig):
    # No redundant "text" definition here!
    # (see in the concise section below, if it doesnt work for you)
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
# You can just use the base type inside a plugin adapter as a field type!
# (if you just use the base type, only the specific model can be validated)
class CommonConfig(BaseModel):
    output: PluginAdapter[OutputConfig]

# You can even add new configs after the fact!
# (see in the extensibility section below, if it doesnt work for you)
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

## ✨ Features

### 🔌 Extensibility

You can add new plugins after the fact!

To do so, you will have to ensure one of the following prerequisites:

**1. Use `ForwardRef`s**

```python
from __future__ import annotations # either by importing annotations from the __future__ package

class BaseConfig(PluginModel):
    ...

...

class CommonConfig1(BaseModel):
    config: PluginAdapter[BaseConfig]

class CommonConfig2(BaseModel):
    config: "PluginAdapter[BaseConfig]" # or by using a string as the type annotation


class NumberConfig(BaseConfig): # now you can declare new types after the fact (but before using/validating the models)!
    ...
```

**2. Enable `defer_build`**

```python
class BaseConfig(PluginModel):
    ...

class CommonConfig(BaseModel):
    config: PluginAdapter[BaseConfig]

    model_config = {"defer_build": True}
```

### 🤏 Shorthands

You can define custom enum-like values that can be set via a literal from everywhere and show up in the json schema for your plugin model:

```python
class Source(PluginModel):
    ...

class UrlSource(Source, value="url"):
    url: str

class FileSource(Source, value="file"):
    path: Path

RANDOM = FileSource(path=Path("/dev/random")).register_as_shorthand("random")
SEARCH = UrlSource(url="https://example.com/search").register_as_shorthand("search", "web_search")

class MyConfig(BaseModel):
    source: PluginAdapter[Source]

MyConfig.model_validate({"source": "random"}) # this is a shorthand for
MyConfig.model_validate({"source": {"type": "file", "path": "/dev/null"}})

MyConfig.model_validate({"source": "search"}) # this and
MyConfig.model_validate({"source": "web_search"}) # this are shorthands for
MyConfig.model_validate({"source": {"type": "url", "url": "https://example.com/search"}})
```

### 🪡 ‍Concise Code

The entire project aims to reduce unnecessary repetitions. Thus, you can write the following code and it will work as intended:

```python
class Logger(PluginModel):
    ...

class StdoutLogger(Logger):
    type: Literal["stdout", "standardout"] # no need to declare an explicit default (no `= "stdout"`)
    ...

logger = StdoutLogger() # will work, but might show a type warning
print(logger.type) # -> "stdout" (always injects the first declared value, if not explicitly instantiated otherwise)
```

Depending on your type-checker, this might show a warning that you did not pass a value to the "required" argument `type`. At runtime this will work as is, but to make the type-checker happy, you can use the following syntax:

```python
class StdoutLogger(Logger):
    type: Literal["stdout", "standardout"] = DEFAULT_LITERAL # no need to repeat the declared values

logger = StdoutLogger() # will work without showing a type warning
print(logger.typ) # -> "stdout"
```

### 🚦 Intersection Types

TL;DR: Plugantic introduces a `value: Model1 & Model2` type annotation

Sometimes, you want to have the same base interface and then some interfaces built on top of that, with slightly different features.

For example you could imaging the following:

```python
class Logger(PluginModel):
    def log(self, text: str): ...

class LoggerWithColors(Logger):
    def change_color(self, color: str): ...

class LoggerWithEmojis(Logger):
    def log_emoji(self, emoji: str): ...
```

Due to multiple inheritance in python, it is easy to define a class that supports both features:

```python
class StdoutLogger(LoggerWithColors, LoggerWithEmojis):
    def log(self, text):
        ...
    def change_color(self, color):
        ...
    def log_emoji(self, emoji):
        ...
```

However, you cannot easily declare a type annotation in python that requires both features. You would wish that something like this existed in python (and plugantic introduces it):

```python
class SomeOtherConfig(BaseModel):
    logger: PluginAdapter[LoggerWithColor] & PluginAdapter[LoggerWithEmojis]
```

Note, that this will break with most type checkers, as this is not a valid type annotation in python ([yet](https://github.com/python/typing/issues/18)?). It does work at runtime though and it is very obvious what this syntax means. You can use `# type: ignore[operator]` to the end of the type annotation to stop the warnings about the incorrect type annotation from your linter.
Alternatively, you can use the following syntax, although it is not actually properly enforced by type checkers (will be treated as `Union[...]` at type-checking time):

```python
class SomeOtherConfig(BaseModel):
    logger: PluginIntersection[LoggerWithColor, LoggerWithEmojis]
```


### 📝 Type Checker Friendliness

The type checker can infer the type of the plugin model, so you don't need to define a union type or a discriminator field!
Apart from annotated unions and intersection types, everything follows Python or Pydantic standards, so it can be used as usual since type checkers already understand those concepts very well.


## 🏛️ Leading Principles

### Composition over Inheritance

Composition is preferred over inheritance.

### Dont repeat yourself (DRY)

Having to inherit from a base class just to then declare an annotated union or having to declare a discriminator field both as an annotation and with a default being the same as the annotation is a violation of the DRY principle. This library tackles all of these issues at once.

### Be conservative in what you send and liberal in what you accept

Using automatic downcasts, this library allows developers to accept every possible value when validating a model.


## 💻 Development

### 📁 Code structure

The code is structured as follows:

- `src/plugantic/` contains the source code
- `tests/` contains the tests

Most of the actual logic is in the `src/plugantic/plugin.py` file.

### 📦 Distribution

To build the package, you can do the following:

```bash
uv build
```
    
<details>
<summary>Publishing</summary>

> 💡 This section is primarily relevant for the maintainers of this package (me), as it requires permission to push a package to the `plugantic` repository on PyPI.

```bash
uv publish --token <token>
```

</details>

### 🎯 Tests

To run all tests, you can do the following:

```bash
uv run pytest
```
