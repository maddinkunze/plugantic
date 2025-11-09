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
    config: BaseConfig

class CommonConfig2(BaseModel):
    config: "BaseConfig" # or by using a string as the type annotation


class NumberConfig(BaseConfig): # now you can declare new types after the fact (but before using/validating the models)!
    ...
```

**2. Enable `defer_build`**

```python
class BaseConfig(PluginModel):
    ...

class CommonConfig(BaseModel):
    config: BaseConfig

    model_config = {"defer_build": True}
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
    logger: LoggerWithColor & LoggerWithEmojis
```

Note, that this will break with most type checkers, as this is not a valid type annotation in python. It does work at runtime though and it is very obvious what this syntax means. You can use `# type: ignore[operator]` to the end of the type annotation to stop the warnings about the incorrect type annotation from your linter.


### 📝 Type Checker Friendliness

The type checker can infer the type of the plugin model, so you don't need to define a union type or a discriminator field!
Everything except for the annotated union and the intersection types is based on pydantic and as such can be used like before as type checkers are already familiar with pydantic.

### 🌀 Automatic Downcasts

Let's say you have the following logger:

```python
class LoggerBase(PluginModel):
    def log_line(self, line: str): ...

class LoggerWithPages(LoggerBase):
    def log_line(self, line: str, new_page: bool=False): ...

class LoggerStdout(LoggerBase, value="stdout"):
    new_page_token: str|None = None
    def log_line(self, line: str, new_page: bool=False):
        if new_page:
            if not self.new_page_token:
                raise ValueError("new_page_token is not set")
            print(self.new_page_token)
        print(line)

class Component1(BaseModel):
    logger: LoggerBase

class Component2(BaseModel):
    logger: LoggerWithPages
```

then users could not use `Component2` with `LoggerStdout` as it does not support (i.e. does not implement) the pages feature, even thoudh `LoggerStdout` would support it, if `new_page_token: str` was enforced.

Conventionally, this would require the developer to create two classes (i.e. `LoggerStdout` and `LoggerStdoutNewPage`) and then include either one in the final annotated union depending on if the component requires the new page functionality.

With `plugantic`, you can automatically create subtypes that are more strict than the base type and they will be automatically validated and downcast when using the model:

```python
class LoggerStdout(LoggerBase, value="stdout"):
    new_page_token: str|None = None
    def log_line(self, line: str, new_page: bool=False):
        if new_page:
            if not self.new_page_token:
                raise ValueError("new_page_token is not set")
            print(self.new_page_token)
        print(line)

class LoggerStdoutWithPages(LoggerStdout, LoggerWithPages):
    new_page_token: str
    # all the functionality is declared in the base class, we just add some type enforcements
```

If you have multiple features, that may need to be supported individually, you can automate these typed subclasses:

```python
class LoggerBase(PluginModel): ...
class LoggerWithPages(LoggerBase): ...
class LoggerWithColors(LoggerBase): ...

class LoggerStdout(LoggerBase, value="stdout"):
    new_page_token: str|None = None
    color: str|None = None

combinations = [(LoggerWithPages,), (LoggerWithColors,), (LoggerWithPages, LoggerWithColors)] # all the combinations we want to create; could be automated using itertools
for parents in combinations:
    class _(LoggerStdout, *parents):
        if LoggerWithPages in parents:
            new_page_token: str # add strict requirements for new page feature
        if LoggerWithColors in parents:
            color: str # add strict requirements for color feature
```

In these cases, you will not have type checker support for instantiating the classes using python, but plugantic will automatically downcast a valid parent class to the correct subclass. So the following is valid, even though `LoggerStdout` itself does not inherit from `LoggerWithColors` (because there is a subclass of `LoggerStdout` that _does_ inherit from `LoggerWithColors` _and_ has the same identifier "stdout")

```python
class SomeConfig(BaseModel):
    logger: LoggerWithColors

SomeConfig.model_validate({
    "logger": LoggerStdout(color="#801212")
})
```


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
uv run publish --token <token>
```

</details>

### 🎯 Tests

To run all tests, you can do the following:

```bash
uv run pytest
```
