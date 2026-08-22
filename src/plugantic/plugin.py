from abc import abstractmethod
from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler, Field
from pydantic_core.core_schema import CoreSchema, union_schema, tagged_union_schema, literal_schema, no_info_plain_validator_function, json_or_python_schema
from typing_extensions import Any, Self, Literal, Union, ClassVar, Tuple, Set, Dict, Mapping, Type, TypeVar, TypeVarTuple, TypeAlias, Iterable, Collection, Callable, TypeIs, Sentinel, get_origin, get_args, get_type_hints, overload, TYPE_CHECKING
from propert import classproperty, cached_classproperty

_LiteralType: TypeAlias = Union[str, int, float, bool, None]

def is_literal_value(value: Any) -> TypeIs[_LiteralType]:
    if value is None:
        return True
    if isinstance(value, (str, int, float, bool)):
        return True
    return False

def ensure_literal_value_collection(value: _LiteralType|Collection[_LiteralType]) -> Collection[_LiteralType]:
    if is_literal_value(value):
        return (value,)
    return value

_UNSET_LITERAL: Any = Sentinel("_UNSET_LITERAL")
DEFAULT_LITERAL: Any = Sentinel("DEFAULT_LITERAL")

_CollectedSubclassesType = Collection[Type["PluginModel"]]
_CollectedDiscriminatedType = Mapping[str, Mapping[_LiteralType, Collection[Type["PluginModel"]]]]
_CollectedShorthandsType = Mapping[_LiteralType, "PluginModel|Callable[[], PluginModel]"]
_CollectedOptionsType = Tuple[_CollectedSubclassesType, _CollectedDiscriminatedType, _CollectedShorthandsType]

_MutableOptionsSubclasses = Set[Type["PluginModel"]]
_MutableOptionsDiscriminator = Dict[str, Dict[_LiteralType, Set[Type["PluginModel"]]]]
_MutableOptionsLiterals = Dict[_LiteralType, "PluginModel|Callable[[], PluginModel]"]

_P = TypeVar("_P", bound=BaseModel)

@overload
def _get_pydantic_origin(item: Type[_P]) -> Type[_P]: ...
@overload
def _get_pydantic_origin(item: Any) -> Type[BaseModel]|None: ...
def _get_pydantic_origin(item):
    if not isinstance(item, type(BaseModel)):
        return None
    origin = item.__pydantic_generic_metadata__.get("origin")
    if origin is None:
        return item
    return origin

def _get_pydantic_args(item):
    if not isinstance(item, type(BaseModel)):
        return (), ()
    metadata = item.__pydantic_generic_metadata__
    return metadata.get("args", ()), metadata.get("parameters", ())
    
def _get_plugantic_model(item: Type, check_meta: bool=False) -> Tuple[Type["PluginModel"]|None, "_PluginMeta|None"]:
    if isinstance(item, type) and issubclass(item, PluginModel):
        item = _get_pydantic_origin(item)
        return item, None
    if check_meta and isinstance(item, _PluginMeta):
        return None, item
    
    origin = get_origin(item)
    if isinstance(origin, type) and issubclass(origin, PluginModel):
        origin = _get_pydantic_origin(origin)
        return origin, None
    if check_meta and isinstance(origin, _PluginMeta):
        return None, origin

    args = get_args(item)
    if (origin == Annotated):
        anned = args[0]
        if isinstance(anned, type) and issubclass(anned, PluginModel):
            anned = _get_pydantic_origin(anned)
            return anned, None
        if check_meta and isinstance(anned, _PluginMeta):
            return None, anned

    return None, None

class PydanticNeverType: # TODO: there has to be a better way to have a type in pydantic that matches no value
    @classmethod
    def __get_pydantic_core_schema__(cls, *_1, **_2):
        def reject_all(*_3, **_4):
            raise ValueError("no value accepted")
        return no_info_plain_validator_function(reject_all)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, *_1, **_2):
        return {"not": {}}  # Matches nothing

class PluganticConfigDict(ConfigDict, total=False):
    discriminator: str|None
    value: _LiteralType|Collection[_LiteralType]
    allow_changes_after_collection: bool
    show_in_schema: bool
    show_sub_in_schema: bool

class PluginModel(BaseModel):
    __plugantic_declared_values__: ClassVar[Collection[_LiteralType]] = ()
    __plugantic_shorthands__: ClassVar[Dict[_LiteralType, Self|Callable[[], Self]]] = {}
    __plugantic_discriminator__: ClassVar[str|None] = "type"
    __plugantic_collected_options__: ClassVar[Dict[Tuple[Type], _CollectedOptionsType]] = {}
    __plugantic_check_collected__: ClassVar[bool] = True
    __plugantic_show_in_schema__: ClassVar[bool|None] = None
    __plugantic_show_sub_in_schema__: ClassVar[bool] = True

    if TYPE_CHECKING:
        model_config: ClassVar[ConfigDict|PluganticConfigDict]
    else:
        __plugantic_order__: ClassVar[int]
        model_plugin_type: ClassVar[Any]

    @cached_classproperty
    @classmethod
    def __plugantic_order__(cls) -> int:
        return cls.mro().index(PluginModel)

    @classproperty
    @classmethod
    def model_plugin_type(cls) -> "Type[PluginAdapter[Self]]":
        return PluginAdapter[cls]
    
    @overload
    @classmethod
    def model_add_shorthand(cls, item: Self, shorthand: _LiteralType, *shorthands: _LiteralType) -> None: ...

    @overload
    @classmethod
    def model_add_shorthand(cls, item: Callable[[], Self], shorthand: _LiteralType, *shorthands: _LiteralType, cached: bool=False) -> None: ...

    @classmethod
    def model_add_shorthand(cls, item: Self|Callable[[], Self], shorthand: _LiteralType, *shorthands: _LiteralType, cached: bool=False) -> None:
        if cached and callable(item):
            item_cb = item
            item_cache = None
            def item_cached():
                nonlocal item_cache
                if item_cache is None:
                    item_cache = item_cb()
                return item_cache
            item = item_cached

        shorthands = (shorthand, *shorthands)
        for shorthand in shorthands:
            if cls.__plugantic_shorthands__.get(shorthand, item) != item:
                raise ValueError(f"Shorthand {shorthand} is already registered for a different item")
            cls.__plugantic_shorthands__[shorthand] = item

    def model_add_as_shorthand(self, *shorthands: _LiteralType) -> Self:
        if not shorthands:
            shorthands = tuple(self.__plugantic_declared_values__)
        if not shorthands:
            raise ValueError(f"No shorthands provided for {self} and no declared values found")
        self.model_add_shorthand(self, *shorthands)
        return self
    
    if not TYPE_CHECKING:
        def __init__(self, *args, **kwargs):
            if self.__plugantic_declared_values__:
                # if the discriminator value is explicitly set to the default sentinel, remove it so a valid value can be set
                if kwargs.get(self.__plugantic_discriminator__, None) is DEFAULT_LITERAL:
                    kwargs.pop(self.__plugantic_discriminator__)

                # if no value is provided for the discriminator (or if it was explicitly unset/removed by the previous rules), set it to the first declared value so the model can be validated
                kwargs.setdefault(self.__plugantic_discriminator__, next(iter(self.__plugantic_declared_values__)))
            super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *,
        discriminator: str|None=_UNSET_LITERAL,
        value: _LiteralType|Collection[_LiteralType]=_UNSET_LITERAL,
        allow_changes_after_collection: bool|None=None,
        show_in_schema: bool|None=None,
        show_sub_in_schema: bool|None=None,
    **kwargs):
        cls.__plugantic_shorthands__ = {}
        cls.__plugantic_collected_options__ = {}

        allow_changes = cls.model_config.get("allow_changes_after_collection", None)
        if allow_changes_after_collection is not None:
            cls.__plugantic_check_collected__ = not allow_changes_after_collection
        elif allow_changes is not None:
            cls.__plugantic_check_collected__ = not allow_changes

        if not cls._are_plugantic_changes_allowed():
            raise ValueError("Cannot create a new PluginModel subclass after the plugin schema for it has been created. Make sure to define all PluginModel subclasses before using them in a PluginAdapter or similar or make sure the consumer of PluginAdapter uses `defer_build` or similar mechanisms.")
        
        cls.__plugantic_show_in_schema__ = cls.model_config.get("show_in_schema", show_in_schema)

        show_sub_in_schema_mc = cls.model_config.get("show_sub_in_schema", None)
        if show_sub_in_schema is not None:
            cls.__plugantic_show_sub_in_schema__ = show_sub_in_schema
        elif show_sub_in_schema_mc is not None:
            cls.__plugantic_show_sub_in_schema__ = show_sub_in_schema_mc

        discriminator_mc = cls.model_config.get("discriminator", _UNSET_LITERAL)
        if discriminator is not _UNSET_LITERAL:
            cls.__plugantic_discriminator__ = discriminator
        elif discriminator_mc is not _UNSET_LITERAL:
            cls.__plugantic_discriminator__ = discriminator_mc

        values_set: Collection[_LiteralType]|None = None
        values_mc = cls.model_config.get("value", _UNSET_LITERAL)
        if value is not _UNSET_LITERAL:
            values_set = ensure_literal_value_collection(value)
        elif values_mc is not _UNSET_LITERAL:
            values_set = ensure_literal_value_collection(values_mc)
        discriminator = cls.__plugantic_discriminator__
        if (values_set is None) and (discriminator is not None):
            values_set = cls._get_declared_plugantic_values_from_annotations(discriminator)
        if values_set is not None:
            cls.__plugantic_declared_values__ = values_set
            if discriminator is not None:
                cls._create_plugantic_annotation(discriminator)

        if kwargs:
            raise ValueError(f"Unexpected keyword arguments in subclass definition: {kwargs.keys()}")

        super().__init_subclass__(**kwargs)

    @classmethod
    def _make_plugantic_literal(cls):
        return Literal.__getitem__(tuple(cls.__plugantic_declared_values__)) # type: ignore # essentially the same as `Literal[*value]`, but the unpacking syntax is not supported on older python versions (<3.11)

    @classmethod
    def _create_plugantic_annotation(cls, discriminator: str):
        """
        Create an annotation of value for the given name as a member variable of the class
        e.g. name="type" value=Literal["test"] -> `type: Literal["test"]`
        """
        if not hasattr(cls, "__annotations__"):
            cls.__annotations__ = {}
        existing_annotation = cls._get_plugantic_value_annotations(discriminator=discriminator)
        value = cls._make_plugantic_literal()
        if existing_annotation == value:
            return
        cls.__annotations__[discriminator] = value

    @classmethod
    def _get_plugantic_value_annotations(cls, discriminator: str) -> Any:
        annotation = None
        try:
            annotation = get_type_hints(cls).get(discriminator, None)
        except (NameError, TypeError):
            pass
        #if not annotation:
        #    field = cls.model_fields.get(cls.__plugantic_discriminator__, None)
        #    if field:
        #        annotation = field.annotation
        return annotation

    @classmethod
    def _get_declared_plugantic_values_from_annotations(cls, discriminator: str) -> Set[_LiteralType]|None:
        field = cls._get_plugantic_value_annotations(discriminator)

        if get_origin(field) is Literal:
            return set(get_args(field))

        return None

    @classmethod
    def _are_plugantic_changes_allowed(cls):
        if not cls.__plugantic_check_collected__:
            return True
        for supcls in cls.mro():
            if not issubclass(supcls, PluginModel):
                continue
            if supcls.__plugantic_collected_options__ is not None:
                return False
        return True

    @classmethod
    def _should_show_in_schema(cls, source: Type):
        if cls.__plugantic_show_in_schema__ is not None:
            return cls.__plugantic_show_in_schema__
        return cls.__plugantic_show_sub_in_schema__

    @classmethod
    def _collect_plugantic_options(cls, source: Type) -> _CollectedOptionsType:
        _cache_key = (source,)
        cached_options = cls.__plugantic_collected_options__.get(_cache_key, None)
        if cached_options is not None:
            return cached_options

        subclasses: _MutableOptionsSubclasses = set()
        discriminated: _MutableOptionsDiscriminator = {}
        shorthands: _MutableOptionsLiterals = {}

        discriminator = cls.__plugantic_discriminator__
        if cls._should_show_in_schema(source):
            if discriminator is None:
                subclasses.add(cls)
            else:
                for value in cls.__plugantic_declared_values__:
                    discriminated.setdefault(discriminator, {}).setdefault(value, set()).add(cls)
        for shorthand, item in cls.__plugantic_shorthands__.items():
            shorthands[shorthand] = item
            
        for subcls in cls.__subclasses__():
            subclasses_sub, discriminated_sub, shorthands_sub = subcls._collect_plugantic_options(source)
            subclasses.update(subclasses_sub)
            for discriminator, subcls_map in discriminated_sub.items():
                for value, subcls_set in subcls_map.items():
                    discriminated.setdefault(discriminator, {}).setdefault(value, set()).update(subcls_set)
            for shorthand, item in shorthands_sub.items():
                if shorthands.get(shorthand, item) != item:
                    raise ValueError(f"Shorthand {shorthand} was given to multiple items: {item!r} and {shorthands[shorthand]!r}")
                shorthands[shorthand] = item

        cls.__plugantic_collected_options__[_cache_key] = subclasses, discriminated, shorthands
        return subclasses, discriminated, shorthands

T = TypeVar("T", bound=PluginModel)

class _PluginMeta:
    @property
    def _plugin_union_expansion(self) -> Tuple["_PluginMeta", ...]:
        return (self,)
    
    @property
    def _plugin_intersection_expansion(self) -> Tuple["_PluginMeta", ...]:
        return (self,)
    
    def __or__(self, other):
        if not isinstance(other, _PluginMeta):
            return Union[self, other]
        return _PluginUnion(*self._plugin_union_expansion, *other._plugin_union_expansion)
    
    def __ror__(self, other):
        if not isinstance(other, _PluginMeta):
            return Union[other, self]
        return _PluginUnion(*other._plugin_union_expansion, *self._plugin_union_expansion)
    
    def __and__(self, other):
        if not isinstance(other, _PluginMeta):
            return NotImplemented # TODO: replace with intersection type once it is implemented in python
        return _PluginIntersection(*self._plugin_intersection_expansion, *other._plugin_intersection_expansion)
    
    def __rand__(self, other):
        if not isinstance(other, _PluginMeta):
            return NotImplemented # TODO: replace with intersection type once it is implemented in python
        return _PluginIntersection(*other._plugin_intersection_expansion, *self._plugin_intersection_expansion)
    
    @abstractmethod
    def _collect_plugantic_options(self) -> _CollectedOptionsType|None: ...

    @abstractmethod
    def _check_isinstance(self, instance) -> bool: ...

    def __get_pydantic_core_schema__(self, source, handler: GetCoreSchemaHandler) -> CoreSchema:
        collected_options = self._collect_plugantic_options()
        if collected_options is None:
            return handler.generate_schema(PydanticNeverType)

        schemas = []

        def _check_isinstance(v):
            # simple check to see if the value is aready an instance of the required plugin type, this allows to skip the more expensive validation if the value is already correct
            # also allows passing instantiated plugin models whose class was declared after the plugin schema was created, which would otherwise not be accepted due to the way plugin options are collected and cached
            if self._check_isinstance(v):
                return v
            raise ValueError(f"Value {v!r} is not an instance of the required plugin type")
        schema_isinstance = no_info_plain_validator_function(_check_isinstance)

        options_classes, options_discriminators, options_literals = collected_options

        if options_literals:
            values_literals = list(options_literals.keys())
            def validate_literal(v):
                if not is_literal_value(v):
                    raise ValueError(f"Expected a literal value (str, int, float, bool or None), got {v!r}")
                value = options_literals.get(v, None)
                if value is None:
                    raise ValueError(f"Unknown literal value {v}, expected one of {values_literals}")
                if callable(value):
                    return value()
                return value
            schemas.append(no_info_plain_validator_function(validate_literal, json_schema_input_schema=literal_schema(values_literals)))

        for discriminator, choices in options_discriminators.items():
            choices_discriminator = {}
            for value, options in choices.items():
                if not options:
                    continue

                options_ordered = sorted(options, key=lambda x: x.__plugantic_order__, reverse=True)
                schemas_ordered = [handler.generate_schema(option) for option in options_ordered]

                if len(schemas_ordered) == 1:
                    schema_option = schemas_ordered[0]
                else:
                    schema_option = union_schema(list(schemas_ordered), mode="left_to_right")

                choices_discriminator[value] = schema_option
            schemas.append(tagged_union_schema(choices_discriminator, discriminator))

        if options_classes:
            options_ordered = sorted(options_classes, key=lambda x: x.__plugantic_order__, reverse=True)
            schemas_ordered = [handler.generate_schema(option) for option in options_ordered]
            if len(schemas_ordered) == 1:
                schema_option = schemas_ordered[0]
            else:
                schema_option = union_schema(list(schemas_ordered), mode="left_to_right")
            schemas.append(schema_option)

        if not schemas:
            json_schema = handler.generate_schema(PydanticNeverType)
            python_schema = schema_isinstance
        elif len(schemas) == 1:
            json_schema = schemas[0]
            python_schema = union_schema([schema_isinstance, json_schema], mode="left_to_right")
        else:
            json_schema = union_schema(schemas, mode="left_to_right")
            python_schema = union_schema([schema_isinstance, *schemas], mode="left_to_right")
        return json_or_python_schema(json_schema, python_schema)
        
class _PluginWrapper(_PluginMeta):
    def __init__(self, plugin_type: Type[PluginModel], *, plugin_base: Type[PluginModel]|None=None):
        self._plugin_type = plugin_type
        if plugin_base is None:
            plugin_base, _ = _get_plugantic_model(plugin_type)
        assert plugin_base is not None, "plugin_base must not be None; if you manually instantiated _PluginWrapper, try passing a direct subclass of PluginModel to the plugin_base kwarg"
        self._plugin_base = plugin_base

    def __class_getitem__(cls, item):
        base, _ = _get_plugantic_model(item)
        if base is None:
            raise TypeError(f"PluginAdapter can only be used with {PluginModel.__name__} subclasses, got {item}")
        return cls(item, plugin_base=base)
    
    def _collect_plugantic_options(self):
        return self._plugin_base._collect_plugantic_options(self._plugin_type)

    def _check_isinstance(self, instance) -> bool:
        return isinstance(instance, self._plugin_base)

class _PluginMultiMeta(_PluginMeta):
    def __init__(self, *plugin_types: _PluginMeta):
        self._plugin_types = plugin_types

    def __class_getitem__(cls, item):
        if not isinstance(item, tuple):
            item = (item,)
        items = set()
        for plugin_type in item:
            plugin_type_model, plugin_type_meta = _get_plugantic_model(plugin_type, check_meta=True)
            if plugin_type_model is not None:
                plugin_type = _PluginWrapper(plugin_type, plugin_base=plugin_type_model)
            if not isinstance(plugin_type_meta, _PluginMeta):
                raise TypeError(f"{cls.__name__.lstrip('_')} can only be used with PluginMeta types (e.g. PluginAdapter, PluginUnion, PluginIntersection), got {plugin_type}")
            items.add(plugin_type_meta)
        return cls(*items)
    
    _check_isinstance_iterator: Callable[[Iterable[bool]], bool]
    def _check_isinstance(self, instance):
        if not self._plugin_types:
            return False
        return self._check_isinstance_iterator(t._check_isinstance(instance) for t in self._plugin_types) 

class _PluginUnion(_PluginMultiMeta):
    @property
    def _plugin_union_expansion(self):
        return tuple(t for ts in self._plugin_types for t in ts._plugin_union_expansion)
    
    _check_isinstance_iterator = any

    def _collect_plugantic_options(self):
        options_classes: _MutableOptionsSubclasses = set()
        options_discriminators: _MutableOptionsDiscriminator = {}
        options_literals: _MutableOptionsLiterals = {}

        for plugin_type in self._plugin_types:
            options = plugin_type._collect_plugantic_options()
            if options is None:
                continue
            options_classes_sub, options_discriminators_sub, options_literals_sub = options

            options_classes.update(options_classes_sub)

            for discriminator, choices_sub in options_discriminators_sub.items():
                for value, options_sub in choices_sub.items():
                    options_discriminators.setdefault(discriminator, {}).setdefault(value, set()).update(options_sub)
            
            for literal, item in options_literals_sub.items():
                if options_literals.get(literal, item) != item:
                    raise ValueError(f"Literal shorthand {literal} was given to multiple items: {item!r} and {options_literals[literal]!r}")
                options_literals[literal] = item

        return options_classes, options_discriminators, options_literals
    
class _PluginIntersection(_PluginMultiMeta):
    @property
    def _plugin_intersection_expansion(self):
        return tuple(t for ts in self._plugin_types for t in ts._plugin_intersection_expansion)
    
    _check_isinstance_iterator = all

    def _collect_plugantic_options(self):
        options_classes: _MutableOptionsSubclasses|None = None
        options_discriminators: _MutableOptionsDiscriminator|None = None
        options_literals: _MutableOptionsLiterals|None = None

        for plugin_type in self._plugin_types:
            options = plugin_type._collect_plugantic_options()
            if options is None:
                return None
            options_classes_sub, options_discriminators_sub, options_literals_sub = options

            if options_classes is None:
                options_classes = set(options_classes_sub)
            else:
                options_classes.intersection_update(options_classes_sub)

            if options_discriminators is None:
                options_discriminators = {v: {k: set(v) for k, v in vs.items()} for v, vs in options_discriminators_sub.items()}
            else:
                options_discriminators_new = {}
                for discriminator, options_sub in options_discriminators_sub.items():
                    if discriminator not in options_discriminators:
                        continue
                    options_values_new = {}
                    for value, options_sub in options_sub.items():
                        if value not in options_discriminators[discriminator]:
                            continue
                        options_values_new[value] = options_discriminators.get(discriminator, {}).get(value, set()).intersection(options_sub)
                    if options_values_new:
                        options_discriminators_new[discriminator] = options_values_new
                options_discriminators = options_discriminators_new
            
            if options_literals is None:
                options_literals = {**options_literals_sub}
            else:
                options_literals_new = {}
                for literal, item in options_literals_sub.items():
                    if options_literals.get(literal) != item:
                        continue
                    options_literals_new[literal] = item
                options_literals = options_literals_new

        return options_classes or set(), options_discriminators or {}, options_literals or {}

if TYPE_CHECKING:
    PluginAdapter: TypeAlias = T
    PluginUnion = Union
    PluginIntersection = Union
else:
    PluginAdapter = _PluginWrapper
    PluginUnion = _PluginUnion
    PluginIntersection = _PluginIntersection
