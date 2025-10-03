from typing_extensions import ClassVar, Type, Self, Literal, Any, TypeVar, Set, Self, get_type_hints, get_origin, get_args
from pydantic import BaseModel, GetCoreSchemaHandler, Field, ConfigDict, model_validator
from pydantic.fields import FieldInfo
from pydantic_core.core_schema import tagged_union_schema, union_schema


class PluganticConfigDict(ConfigDict, total=False):
    varname_type: str
    value: str
    auto_downcast: bool
    downcast_order: int

_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")

class PluganticModelMeta(type(BaseModel)):
    def __and__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel):
            return PluganticCombinedAnd(cls, other)

        return super().__and__(other)

    def __rand__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel):
            return PluganticCombinedAnd(other, cls)

        return super().__rand__(other)

    def __or__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel):
            return PluganticCombinedOr(cls, other)

        return super().__or__(other)

    def __ror__(cls: Type[_T1], other: Type[_T2]) -> Type[_T1|_T2]:
        if issubclass(other, PluginModel) or isinstance(other, PluganticCombinedModel):
            return PluganticCombinedOr(other, cls)

        return super().__ror__(other)

class PluginModel(BaseModel, metaclass=PluganticModelMeta):
    __plugantic_varname_type__: ClassVar[str] = "type"
    __plugantic_auto_downcast__: ClassVar[bool] = True
    __plugantic_downcast_order__: ClassVar[int|None] = None
    __plugantic_was_schema_created__: ClassVar[bool] = False
    __plugantic_check_schema_usage__: ClassVar[bool] = True
    
    model_config: ClassVar[PluganticConfigDict] = PluganticConfigDict()

    def __init__(self, *args, **kwargs):
        declared_type = self._get_declared_type()
        if declared_type:
            kwargs = {
                self.__plugantic_varname_type__: declared_type,
                **kwargs
            }
        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *,
        varname_type: str|None=None,
        value: str|None=None,
        auto_downcast: bool|None=None,
        downcast_order: int|None=None,
    **kwargs):
        if cls._check_plugantic_schema_usage():
            raise ValueError(f"Schema of {cls.__name__} has already been created. Creating new subclasses after the schema has been created will lead to undefined behaviour.")

        super().__init_subclass__(**kwargs)

        if cls.model_config:
            varname_type = cls.model_config.get("varname_type", None) or varname_type
            value = cls.model_config.get("value", None) or value
            auto_downcast = cls.model_config.get("auto_downcast", None) or auto_downcast
            downcast_order = cls.model_config.get("downcast_order", None) or downcast_order

        cls.__plugantic_was_schema_created__ = False
        cls.__plugantic_downcast_order__ = downcast_order

        if auto_downcast is not None:
            cls.__plugantic_auto_downcast__ = auto_downcast

        if varname_type is not None:
            cls.__plugantic_varname_type__ = varname_type

        if value is not None:
            cls._create_annotation(cls.__plugantic_varname_type__, Literal[value])
        
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
        declared_type = cls._get_declared_type()
        if not declared_type:
            return
        cls._create_field_default(cls.__plugantic_varname_type__, declared_type)

    @classmethod
    def _get_declared_annotation(cls, name: str):
        annotation = None
        try:
            annotation = get_type_hints(cls).get(name, None)
        except NameError:
            pass
        if not annotation:
            field = cls.model_fields.get(name, None)
            if field:
                annotation = field.annotation
        return annotation

    @classmethod
    def _get_declared_type(cls) -> str|None:
        """Get the value declared for the discriminator name (e.g. `type: Literal["something"]` -> "something")"""
        field = cls._get_declared_annotation(cls.__plugantic_varname_type__)

        if get_origin(field) is Literal:
            return get_args(field)[0]

        return None

    @classmethod
    def _is_valid_subclass(cls) -> bool:
        if cls._get_declared_type():
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
    def _as_tagged_union(cls, handler: GetCoreSchemaHandler):
        subclasses = set(cls._get_valid_subclasses())
        if len(subclasses) == 1:
            subcls = subclasses.pop()
            subcls._mark_schame_created()
            return handler(subcls)

        for subcls in subclasses:
            subcls._mark_schame_created()

        choices = dict[str, Type[Self]]()

        for subcls in subclasses:
            type_ = subcls._get_declared_type()
            existing = choices.get(type_, None)
            if existing:
                subcls = existing.__plugantic_order__(subcls)
            choices[type_] = subcls

        choices = {
            type_: handler(subcls)
            for type_, subcls in choices.items()
        }
        
        return tagged_union_schema(choices, discriminator=cls.__plugantic_varname_type__)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        cls._mark_schame_created()
        return cls._as_tagged_union(handler)

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
    def _mark_schame_created(cls) -> None:
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
    def _try_downcast(cls, data, handler):
        if isinstance(data, cls):
            pass
        elif cls.__plugantic_auto_downcast__ and issubclass(cls, type(data)):
            try:
                data = cls(**data.model_dump())
            except Exception as e:
                raise ValueError(f"Failed to downcast given {repr(data)} to required {cls.__name__}; please provide the required config directly") from e
        return handler(data)
    
    model_config = {"defer_build": True}

class PluganticCombinedModel:
    def __init__(self, *args: "PluganticCombinedModel|type[PluginModel]"):
        self.items = args
    
    def _get_valid_subclasses(self) -> Set[type[PluginModel]]: ...

    def __and__(self, other: Type):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedAnd(self, other)
        return super().__and__(other)

    def __rand__(self, other):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedAnd(other, self)
        return super().__rand__(other)

    def __or__(self, other):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedOr(self, other)
        return super().__or__(other)

    def __ror__(self, other):
        if isinstance(other, PluganticCombinedModel) or issubclass(other, PluginModel):
            return PluganticCombinedOr(other, self)
        return super().__ror__(other)

    def __get_pydantic_core_schema__(self, source, handler: GetCoreSchemaHandler):
        subclasses = set(self._get_valid_subclasses())
        if len(subclasses) == 1:
            subcls = subclasses.pop()
            subcls._mark_schame_created()
            return handler(subcls)
        
        choices = dict[str, dict[str, Type[PluginModel]]]()
        for subcls in subclasses:
            subcls._mark_schame_created()
            varname = subcls.__plugantic_varname_type__
            type_ = subcls._get_declared_type()
            existing = choices.setdefault(varname, {}).get(type_, None)
            if existing:
                subcls = existing.__plugantic_order__(subcls)
            choices[varname][type_] = subcls

        choices = {
            varname: {type_: handler(subcls) for type_, subcls in types.items()}
            for varname, types in choices.items()
        }

        unions = [
            tagged_union_schema(c, discriminator=d) for d, c in choices.items()
        ]

        if len(unions) == 1:
            return unions.pop()

        return union_schema(unions)

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

class PluganticCombinedOr(PluganticCombinedModel):
    def _get_valid_subclasses(self):
        items = None
        for item in self.items:
            if items is None:
                items = item._get_valid_subclasses()
                continue
            items.update(item._get_valid_subclasses())
        return items or set()
