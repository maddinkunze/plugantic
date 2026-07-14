"""Plugantic: Simplify extendable composition with Pydantic."""
from ._consts import version as __version__
from .plugin import PluginModel, PluganticConfigDict as PluginConfig, Field, DEFAULT_LITERAL
from .plugin import PluginAdapter, PluginUnion, PluginIntersection
