from abc import abstractmethod
from typing_extensions import ClassVar, Type, Self, Literal, Any, TypeVar, Set, Collection, Sequence, get_type_hints, get_origin, get_args, TYPE_CHECKING
from pydantic import BaseModel, GetCoreSchemaHandler, Field, ConfigDict, model_validator
from pydantic.fields import FieldInfo
from pydantic_core.core_schema import tagged_union_schema, union_schema, literal_schema, no_info_plain_validator_function, CoreSchema

_LiteralType = str|int|float|bool|None

if TYPE_CHECKING:
    _LiteralUnset = None
else:
    _LiteralUnset = object()

class PydanticNeverType:
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        def reject_all(v):
            raise ValueError("no value accepted")
        return no_info_plain_validator_function(reject_all)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        return {"not": {}}  # Matches nothing

class PluganticConfigDict(ConfigDict, total=False):
    varname_type: str
    value: _LiteralType|Collection[_LiteralType]
    auto_downcast: bool
    downcast_order: int

_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")

class PluganticModelMeta(type(BaseModel)):
    def __and__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(cls, PluginModel) and (issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel)):
            return PluganticCombinedAnd(cls, other) # pyright: ignore[reportReturnType]
        return NotImplemented

    def __rand__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(cls, PluginModel) and (issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel)):
            return PluganticCombinedAnd(other, cls) # pyright: ignore[reportReturnType]
        return NotImplemented

    def __or__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(cls, PluginModel) and (issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel)):
            return PluganticCombinedOr(cls, other) # pyright: ignore[reportReturnType]
        return NotImplemented

    def __ror__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(cls, PluginModel) and (issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel)):
            return PluganticCombinedOr(other, cls) # pyright: ignore[reportReturnType]
        return NotImplemented
    
if TYPE_CHECKING:
    _PluginModelMeta = type(BaseModel)
    
else:
    _PluginModelMeta = PluganticModelMeta

class PluginModel(BaseModel, metaclass=_PluginModelMeta):
    __plugantic_varname_type__: ClassVar[str] = "type"
    __plugantic_auto_downcast__: ClassVar[bool] = True
    __plugantic_downcast_order__: ClassVar[int|None] = None
    __plugantic_was_schema_created__: ClassVar[bool] = False
    __plugantic_check_schema_usage__: ClassVar[bool] = True
    __plugantic_shorthands__: ClassVar[dict[_LiteralType, Self]] = {}
    
    model_config: ClassVar[ConfigDict|PluganticConfigDict] = PluganticConfigDict(defer_build=True)

    @classmethod
    def register_shorthand(cls, item: Self, *names: _LiteralType) -> None:
        if not names:
            names = tuple(item._get_declared_types())

        for name in names:
            if name in cls.__plugantic_shorthands__:
                existing = cls.__plugantic_shorthands__[name]
                if existing is not item:
                    raise ValueError(f"Shorthand {repr(name)} is already registered for {existing.__class__.__name__}, cannot register it for {item.__class__.__name__}")
            cls.__plugantic_shorthands__[name] = item

    def register_as_shorthand(self, *names: _LiteralType) -> Self:
        self.register_shorthand(self, *names)
        return self

    if not TYPE_CHECKING:
        def __init__(self, *args, **kwargs):
            declared_type = self._get_declared_types()[0] # inject the default discriminator value if not provided
            if declared_type:
                kwargs = {
                    self.__plugantic_varname_type__: declared_type,
                    **kwargs
                }
            super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *,
        varname_type: str|None=None,
        value: _LiteralType|Collection[_LiteralType]=_LiteralUnset,
        auto_downcast: bool|None=None,
        downcast_order: int|None=None,
    **kwargs):
        if cls._check_plugantic_schema_usage():
            raise ValueError(f"Schema of {cls.__name__} has already been created. Creating new subclasses after the schema has been created will lead to undefined behaviour.")

        super().__init_subclass__(**kwargs)

        cls.__plugantic_shorthands__ = {}

        if cls.model_config:
            varname_type = cls.model_config.get("varname_type", None) or varname_type
            _mcval = cls.model_config.get("value", _LiteralUnset)
            if _mcval is not _LiteralUnset:
                value = _mcval
            auto_downcast = cls.model_config.get("auto_downcast", None) or auto_downcast
            downcast_order = cls.model_config.get("downcast_order", None) or downcast_order

        cls.__plugantic_was_schema_created__ = False
        cls.__plugantic_downcast_order__ = downcast_order

        if auto_downcast is not None:
            cls.__plugantic_auto_downcast__ = auto_downcast

        if varname_type is not None:
            cls.__plugantic_varname_type__ = varname_type

        if value is not _LiteralUnset:
            if isinstance(value, (str, int, float, bool)) or value is None:
                value = (value,)
            cls._create_annotation(cls.__plugantic_varname_type__, Literal[*value])
        
        cls._ensure_varname_default()

    @classmethod
    def _create_annotation(cls, name: str, value: Any, *, only_set_if_not_exists: bool=False, force_set: bool=False):
        """
        Create an annotation of value for the given name as a member variable of the class
        e.g. name="type" value=Literal["test"] -> `type: Literal["test"]`
        """
        if not hasattr(cls, "__annotations__"):
            cls.__annotations__ = {}
        existing_annotation = cls._get_declared_annotation(name)
        if (existing_annotation is None) and only_set_if_not_exists:
            return
        if existing_annotation == value and (not force_set):
            return
        cls.__annotations__[name] = value

    _NoValue = object()
    @classmethod
    def _create_field_default(cls, name: str, value: Any):
        actual_value = getattr(cls, name, cls._NoValue)
        if isinstance(actual_value, FieldInfo):
            if actual_value.default == value:
                return
            value = FieldInfo.merge_field_infos(actual_value, Field(default=value))
        
        if actual_value == value:
            return
        
        setattr(cls, name, value)

    @classmethod
    def _ensure_varname_default(cls):
        """
        Ensure that the discriminator name is associated with a value so that creating a direct instance does not require passing the value again
        e.g.:
        class SomeConfig(PluginModel):
            type: Literal["something"] # will be transformed to the equivalent of `type: Literal["something"] = "something"`

        SomeConfig() # works, because there is a default value set
        SomeConfig(type="something") # works
        SomeConfig(type="else") # fails
        """
        declared_types = cls._get_declared_types()
        if not declared_types:
            return
        cls._create_field_default(cls.__plugantic_varname_type__, declared_types[0])

    @classmethod
    def _get_declared_annotation(cls, name: str):
        annotation = None
        try:
            annotation = get_type_hints(cls).get(name, None)
        except (NameError, TypeError):
            pass
        if not annotation:
            field = cls.model_fields.get(name, None)
            if field:
                annotation = field.annotation
        return annotation

    @classmethod
    def _get_declared_types(cls) -> Sequence[_LiteralType]:
        """Get the value declared for the discriminator name (e.g. `type: Literal["something"]` -> "something")"""
        field = cls._get_declared_annotation(cls.__plugantic_varname_type__)

        if get_origin(field) is Literal:
            return get_args(field)

        return []

    @classmethod
    def _is_valid_subclass(cls) -> bool:
        if cls._get_declared_types():
            return True
        return False

    @classmethod
    def _get_valid_subclasses(cls) -> Set[Type[Self]]:
        valid = set()

        if cls._is_valid_subclass():
            valid.add(cls)

        for subcls in cls.__subclasses__():
            valid.update(subcls._get_valid_subclasses())

        return valid
    
    @classmethod
    def _get_valid_shorthands(cls) -> dict[_LiteralType, Self]:
        shorthands = cls.__plugantic_shorthands__.copy()
        for subcls in cls.__subclasses__():
            for name, item in subcls._get_valid_shorthands().items():
                if name in shorthands and shorthands[name] is not item:
                    raise ValueError(f"Shorthand {repr(name)} is already registered for {shorthands[name].__class__.__name__}, cannot register it for {item.__class__.__name__}")
                shorthands[name] = item
        return shorthands

    @classmethod
    def _as_tagged_union(cls, handler: GetCoreSchemaHandler):
        subclasses = set(cls._get_valid_subclasses())
        if len(subclasses) == 1:
            subcls = subclasses.pop()
            subcls._mark_schema_created()
            return handler(subcls)

        for subcls in subclasses:
            subcls._mark_schema_created()

        choices = dict[_LiteralType, Type[Self]]()

        for subcls in subclasses:
            types = subcls._get_declared_types()
            for type_ in types:
                existing = choices.get(type_, None)
                if existing:
                    subcls = existing.__plugantic_order__(subcls)
                choices[type_] = subcls

        choices = {
            type_: handler(subcls)
            for type_, subcls in choices.items()
        }

        if not choices:
            return None
        
        return tagged_union_schema(choices, discriminator=cls.__plugantic_varname_type__)

    @classmethod
    def _as_shorthand_union(cls):
        shorthands = cls._get_valid_shorthands()
        if not shorthands:
            return None
        keys = list(shorthands.keys())
        def validator(v):
            if v not in keys:
                raise ValueError(f"Unknown shorthand {repr(v)}; expected one of {keys}")
            return shorthands[v]
        return no_info_plain_validator_function(validator, json_schema_input_schema=literal_schema(keys))

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        cls._mark_schema_created()
        tagged_union = cls._as_tagged_union(handler)
        shorthand_union = cls._as_shorthand_union()
        schemas = [tagged_union, shorthand_union]
        schemas = [s for s in schemas if s is not None]
        if not schemas:
            return handler.generate_schema(PydanticNeverType) # no valid subclasses or shorthands, return an empty literal to make it always fail validation
        if len(schemas) == 1:
            return schemas[0]
        return union_schema(schemas)

    @classmethod
    def __plugantic_order__(cls, other: Type[Self]) -> Type[Self]:
        if cls.__plugantic_downcast_order__ is not None and other.__plugantic_downcast_order__ is not None:
            if cls.__plugantic_downcast_order__ < other.__plugantic_downcast_order__:
                return cls
            return other

        if other in cls.mro():
            return other
        if cls in other._get_valid_subclasses():
            return other
        
        return cls

    @classmethod
    def _mark_schema_created(cls) -> None:
        cls.__plugantic_was_schema_created__ = True
        
    @classmethod
    def _check_plugantic_schema_usage(cls) -> bool:
        """
        Return True if the schema of this class or any of its superclasses has been created
        This check can be circumvented by setting __plugantic_check_schema_usage__ to False
        """
        if not cls.__plugantic_check_schema_usage__:
            return False
        for supcls in cls.mro():
            if not issubclass(supcls, PluginModel):
                continue
            if supcls.__plugantic_was_schema_created__:
                return True
        return False

    @model_validator(mode="wrap")
    @classmethod
    def _try_downcast(cls, data, handler):
        if isinstance(data, cls):
            pass
        elif cls.__plugantic_auto_downcast__ and issubclass(cls, type(data)):
            try:
                data = cls(**data.model_dump())
            except Exception as e:
                raise ValueError(f"Failed to downcast given {repr(data)} to required {cls.__name__}; please provide the required config directly") from e
        return handler(data)

class PluganticCombinedModel:
    def __init__(self, *args: "PluganticCombinedModel|Type[PluginModel]"):
        self.items = args
    
    @abstractmethod
    def _get_valid_subclasses(self) -> Set[Type[PluginModel]]:
        raise NotImplementedError()
    
    @abstractmethod
    def _get_valid_shorthands(self) -> dict[_LiteralType, PluginModel]:
        raise NotImplementedError()

    def __and__(self, other: Type):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedAnd(self, other)
        return NotImplemented

    def __rand__(self, other):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedAnd(other, self)
        return NotImplemented

    def __or__(self, other):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedOr(self, other)
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedOr(other, self)
        return NotImplemented

    def _as_tagged_union(self, handler: GetCoreSchemaHandler):
        subclasses = set(self._get_valid_subclasses())
        if len(subclasses) == 1:
            subcls = subclasses.pop()
            subcls._mark_schema_created()
            return handler(subcls)
        
        choices = dict[str, dict[_LiteralType, Type[PluginModel]]]()
        for subcls in subclasses:
            subcls._mark_schema_created()
            varname = subcls.__plugantic_varname_type__
            if varname is None:
                continue
            types = subcls._get_declared_types()
            for type_ in types:
                existing = choices.setdefault(varname, {}).get(type_, None)
                if existing:
                    subcls = existing.__plugantic_order__(subcls)
                choices[varname][type_] = subcls

        choices = {
            varname: {type_: handler(subcls) for type_, subcls in types.items()}
            for varname, types in choices.items()
        }

        choices = {varname: types for varname, types in choices.items() if types}

        unions: list = [
            tagged_union_schema(c, discriminator=d) for d, c in choices.items()
        ]

        if not unions:
            return None

        if len(unions) == 1:
            return unions.pop()

        return union_schema(unions)

    def _as_shorthand_union(self):
        shorthands = self._get_valid_shorthands()
        if not shorthands:
            return None
        return no_info_plain_validator_function(lambda v: shorthands[v], json_schema_input_schema=literal_schema(list(shorthands.keys())))
    
    def __get_pydantic_core_schema__(self, source, handler: GetCoreSchemaHandler):
        tagged_union = self._as_tagged_union(handler)
        shorthand_union = self._as_shorthand_union()
        schemas = [tagged_union, shorthand_union]
        schemas = [s for s in schemas if s is not None]
        if not schemas:
            return handler.generate_schema(PydanticNeverType) # no valid subclasses or shorthands, return an empty literal to make it always fail validation
        if len(schemas) == 1:
            return schemas[0]
        return union_schema(schemas)

class PluganticCombinedAnd(PluganticCombinedModel):
    def _get_valid_subclasses(self):
        items = None
        for item in self.items:
            if items is None:
                items = item._get_valid_subclasses()
                continue
            if not items:
                return items
            items.intersection_update(item._get_valid_subclasses())
        return items or set()
    
    def _get_valid_shorthands(self):
        if not self.items:
            return {}
        shorthands = self.items[0]._get_valid_shorthands().copy()
        for item in self.items[1:]:
            item_shorthands = item._get_valid_shorthands()
            shorthands = {name: shitem for name, shitem in shorthands.items() if (shitem is item_shorthands.get(name))}
        return shorthands

class PluganticCombinedOr(PluganticCombinedModel):
    def _get_valid_subclasses(self):
        items = None
        for item in self.items:
            if items is None:
                items = item._get_valid_subclasses()
                continue
            items.update(item._get_valid_subclasses())
        return items or set()

    def _get_valid_shorthands(self):
        shorthands = {}
        for item in self.items:
            for name, shitem in item._get_valid_shorthands().items():
                if name in shorthands and shorthands[name] is not shitem:
                    del shorthands[name] # remove ambiguous shorthands
                    continue
                shorthands[name] = shitem
        return shorthands
