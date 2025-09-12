from __future__ import annotations

from typing_extensions import ClassVar, Iterable, Type, Union, Self, Literal, Any, Callable, Generic, TypeVar, TypeVarTuple, Unpack, TypeAliasType, TypedDict, get_origin, get_args, TYPE_CHECKING
from pydantic import BaseModel, GetCoreSchemaHandler, model_validator
from pydantic_core.core_schema import tagged_union_schema

from ._helpers import recursive_powerset, recursive_linear, RecursiveList
from ._types import _VanishBase

Ts = TypeVarTuple("Ts")

if TYPE_CHECKING:
    _plugin_base = Generic[Unpack[Ts]]
else:
    _plugin_base = _VanishBase

class PluganticConfig(TypedDict):
    varname_type: str|None = None
    value: str|None = None
    supported_features: set[Any]|tuple[Any, ...]=()
    required_features: _RequiresFeatureSpec|None=None
    auto_downcasts: PluginDowncastCallbacks|None=None

class PluginModel(BaseModel, _plugin_base):
    __plugantic_varname_type__: ClassVar[str] = "type"
    __plugantic_supported_features__: ClassVar[set[Any]] = set()
    __plugantic_required_features__: ClassVar[_RequiresFeatureSpec|None] = None
    __plugantic_inherit_features__: ClassVar[bool] = True
    __plugantic_generic_supertype__: ClassVar[type|None] = None
    __plugantic_auto_downcasts__: ClassVar[set[Self]|None] = None
    __plugantic_auto_downcast_callbacks__: ClassVar[PluginDowncastCallbacks|None] = None
    __plugantic_was_schema_created__: ClassVar[bool] = False
    __plugantic_check_schema_usage__: ClassVar[bool] = True

    plugantic_config: ClassVar[PluganticConfig|None] = None

    def __init__(self, *args, **kwargs):
        declared_type = self._get_declared_type()
        if declared_type:
            kwargs = {
                self.__plugantic_varname_type__: declared_type,
                **kwargs
            }
        super().__init__(*args, **kwargs)

    def __class_getitem__(cls, args):
        if not isinstance(args, tuple):
            args = (args,)
        requires_features, supports_features = cls._unpack_features(*args)
        return type(cls.__name__, (cls,), {}, supported_features=supports_features, required_features=requires_features, _plugantic_generic_supertype=cls)

    def __init_subclass__(cls, *,
        varname_type: str|None=None,
        value: str|None=None,
        supported_features: set[Any]|tuple[Any, ...]=(),
        required_features: _RequiresFeatureSpec|None=None,
        auto_downcasts: PluginDowncastCallbacks|None=None,
        _plugantic_generic_supertype: type|None=None,
        _plugantic_downcast_callback: SimplePluginDowncastCallback|None=None,
    **kwargs):
        if cls._check_plugantic_schema_usage():
            raise ValueError(f"Schema of {cls.__name__} has already been created. Creating new subclasses after the schema has been created will lead to undefined behaviour.")

        super().__init_subclass__(**kwargs)

        if cls.plugantic_config:
            varname_type = cls.plugantic_config.get("varname_type", None) or varname_type
            value = cls.plugantic_config.get("value", None) or value
            supported_features = cls.plugantic_config.get("supported_features", ()) or supported_features
            required_features = cls.plugantic_config.get("required_features", None) or required_features
            auto_downcasts = cls.plugantic_config.get("auto_downcasts", None) or auto_downcasts

        cls.__plugantic_was_schema_created__ = False

        cls.__plugantic_generic_supertype__ = _plugantic_generic_supertype
        cls.__plugantic_required_features__ = required_features
        cls.__plugantic_auto_downcasts__ = None

        supported_features = set(supported_features)
        if cls.__plugantic_inherit_features__:
            supported_features = cls.__plugantic_supported_features__ | supported_features

        cls.__plugantic_supported_features__ = supported_features

        if varname_type is not None:
            cls.__plugantic_varname_type__ = varname_type

        if value is not None:
            cls._create_annotation(cls.__plugantic_varname_type__, Literal[value])
        
        cls._ensure_varname_default()

        if _plugantic_downcast_callback:
            _plugantic_downcast_callback(PluginDowncastHandler(cls))

        cls.__plugantic_auto_downcast_callbacks__ = auto_downcasts

    @classmethod
    def _ensure_downcasts(cls):
        if not cls.__plugantic_auto_downcast_callbacks__:
            return

        callbacks = cls.__plugantic_auto_downcast_callbacks__
        cls.__plugantic_auto_downcast_callbacks__ = None

        cls.__plugantic_auto_downcasts__ = cls._create_downcasts(callbacks)

    @classmethod
    def _create_downcasts(cls, downcast_callbacks: PluginDowncastCallbacks):
        downcasts = set()
        for callback in cls._create_powerset_downcast_callbacks(downcast_callbacks):
            subcls = type(cls.__name__, (cls,), {}, _plugantic_downcast_callback=callback)
            downcasts.add(subcls)
        return downcasts

    @classmethod
    def _create_linear_downcast_callbacks(cls, downcasts: PluginDowncastCallbacks):
        return recursive_linear(downcasts, callable, cls._create_joined_downcast_callback)

    @classmethod
    def _create_powerset_downcast_callbacks(cls, downcasts: PluginDowncastCallbacks):
        return recursive_powerset(downcasts, callable, cls._create_joined_downcast_callback)

    @classmethod
    def _create_joined_downcast_callback(cls, downcasts: PluginDowncastCallbacks) -> SimplePluginDowncastCallback:
        def callback(handler: PluginDowncastHandler):
            for downcast in downcasts:
                downcast(handler)

        return callback

    @classmethod
    def _unpack_features(cls, *features: Any) -> tuple[_RequiresFeatureSpec, set[Any]]:
        requires_all_features = set()
        supports_features = set()

        for feature in features:
            if isinstance(feature, _RequiresFeatureSpec):
                requires_all_features.add(feature)
                continue
            
            _any_features = set()
            if get_origin(feature) is Union:
                for sub_feature in get_args(feature):
                    _any_features.update(cls._unwrap_feature(sub_feature))
            if get_origin(feature) is Literal:
                _any_features.update(get_args(feature))
            
            if len(_any_features) == 1:
                feature = _any_features.pop()

            if _any_features:
                requires_all_features.add(_RequiresAnyFeature(any_of=_any_features))
                supports_features.update(_any_features)
                continue

            requires_all_features.add(feature)
            supports_features.add(feature)

        return _RequiresAllFeatures(all_of=requires_all_features), supports_features

    @classmethod
    def _unwrap_feature(cls, feature: Any) -> tuple[Any]:
        if get_origin(feature) is Literal:
            return get_args(feature)
        return (feature,)

    @classmethod
    def _create_subclass(cls):
        return type(cls.__name__, (cls,), {})

    @classmethod
    def _create_annotation(cls, name: str, value: Any):
        """
        Create an annotation of value for the given name as a member variable of the class
        e.g. name="type" value=Literal["test"] -> `type: Literal["test"]`
        """
        if not hasattr(cls, "__annotations__"):
            cls.__annotations__ = {}
        if not cls.__annotations__.get(name, None):
            cls.__annotations__[name] = value

    _NoValue = object()
    @classmethod
    def _create_field_default(cls, name: str, value: Any):
        actual_value = getattr(cls, name, cls._NoValue)
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
    def _get_declared_type(cls) -> str|None:
        """Get the value declared for the discriminator name (e.g. `type: Literal["something"]` -> "something")"""
        field = getattr(cls, "__annotations__", {}).get(cls.__plugantic_varname_type__, None)

        if (not field) and hasattr(cls, "model_fields"):
            field = cls.model_fields.get(cls.__plugantic_varname_type__, None)
            if field:
                field = field.annotation

        if get_origin(field) is Literal:
            return get_args(field)[0]

        return None

    @classmethod
    def _supports_features(cls, features: _RequiresFeatureSpec|None) -> bool:
        if features is None:
            return True

        return features.applies_to(cls.__plugantic_supported_features__)

    @classmethod
    def _is_valid_subclass(cls, filter: _PluginFeatureFilter) -> bool:
        if cls.__plugantic_generic_supertype__:
            return False

        if not cls._supports_features(filter.required_features):
            return False

        if cls._get_declared_type():
            return True

        return False

    @classmethod
    def _select_optimal_subclass(cls, subclasses: Iterable[Self], filter: _PluginFeatureFilter) -> Self|None:
        """
        Select the optimal subclass from a list of subclasses given a feature filter

        This is primarily used to select the least restrictive subclass for automatic downcasting
        We assume that the subclass with the fewest changes (i.e. with the fewest added features) is the least restrictive.
        Thus, the optimal subclass is the one that has the fewest overall features. 
        In the future this might be changed to the subclass with the fewest differences between the subclass and the base class.
        """
        optimal = None
        for subcls in subclasses:
            if optimal is None:
                optimal = subcls
            
            if len(subcls.__plugantic_supported_features__) < len(optimal.__plugantic_supported_features__):
                optimal = subcls

        return optimal

    @classmethod
    def _get_all_subclasses(cls):
        cls._ensure_downcasts()
        if not cls.__plugantic_auto_downcasts__:
            return cls.__subclasses__()

        return [subcls for subcls in cls.__subclasses__() if not subcls in cls.__plugantic_auto_downcasts__]

    @classmethod
    def _get_valid_self_class(cls, filter: _PluginFeatureFilter) -> Type[Self]|None:
        if cls._is_valid_subclass(filter):
            return cls

        cls._ensure_downcasts()
        if not cls.__plugantic_auto_downcasts__:
            return None

        return cls._select_optimal_subclass(cls._get_valid_downcast_subclasses(filter), filter)

    @classmethod
    def _get_valid_downcast_subclasses(cls, filter: _PluginFeatureFilter) -> Iterable[Type[Self]]:
        return [subcls for subcls in cls.__plugantic_auto_downcasts__ if subcls._is_valid_subclass(filter)]

    @classmethod
    def _get_valid_subclasses(cls, filter: _PluginFeatureFilter) -> Iterable[Type[Self]]:
        valid = []

        valid_self_class = cls._get_valid_self_class(filter)
        if valid_self_class:
            valid.append(valid_self_class)

        for subcls in cls._get_all_subclasses():
            valid.extend(subcls._get_valid_subclasses(filter))

        return valid

    @classmethod
    def _as_tagged_union(cls, handler: GetCoreSchemaHandler, filter: _PluginFeatureFilter):
        subclasses = set(cls._get_valid_subclasses(filter))
        if len(subclasses) == 1:
            return handler(subclasses.pop())

        choices = {subcls._get_declared_type(): handler(subcls) for subcls in subclasses}
        return tagged_union_schema(choices, discriminator=cls.__plugantic_varname_type__)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        _required_features = None
        _base = cls

        if cls.__plugantic_generic_supertype__:
            _required_features = cls.__plugantic_required_features__
            _base = cls.__plugantic_generic_supertype__

        _filter = _PluginFeatureFilter(required_features=_required_features)

        cls.__plugantic_was_schema_created__ = True

        return _base._as_tagged_union(handler, _filter)

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
        elif cls.__plugantic_generic_supertype__ and isinstance(data, cls.__plugantic_generic_supertype__):
            try:
                data = cls(**data.model_dump())
            except Exception as e:
                raise ValueError(f"Failed to downcast given {repr(data)} to required {cls.__name__}; please provide the required config directly") from e
        return handler(data)
    
    model_config = {"defer_build": True}

class _RequiresFeatureSpec:
    def applies_to(self, supported_features: set[Any]) -> bool:
        ...

    def _split_features(self, features: set[Any]) -> tuple[set[Any], set[Self]]:
        feats, specs = set(), set()
        for feature in features:
            if isinstance(feature, _RequiresFeatureSpec):
                specs.add(feature)
            else:
                feats.add(feature)
        return feats, specs

class _RequiresAnyFeature(_RequiresFeatureSpec):
    def __init__(self, *, any_of: set[Any]):
        self.any_of_features, self.any_of_specs = self._split_features(any_of)
    
    def applies_to(self, supported_features) -> bool:
        return (not self.any_of_features.isdisjoint(supported_features)) or any(spec.applies_to(supported_features) for spec in self.any_of_specs)

class _RequiresAllFeatures(_RequiresFeatureSpec):
    def __init__(self, *, all_of: set[Any]):
        self.all_of_features, self.all_of_specs = self._split_features(all_of)
    
    def applies_to(self, supported_features) -> bool:
        return self.all_of_features.issubset(supported_features) and all(spec.applies_to(supported_features) for spec in self.all_of_specs)

class _PluginFeatureFilter:
    def __init__(self, *, required_features: _RequiresFeatureSpec|None=None):
        self.required_features = required_features

T = TypeVar("T", bound=PluginModel)

class PluginDowncastHandler(Generic[T]):
    def __init__(self, wraps: Type[T]):
        self.wraps = wraps

    def get_raw_type(self) -> Type[T]:
        return self.wraps

    def enable_feature(self, feature: Any):
        features = self.wraps._unwrap_feature(feature)
        self.wraps.__plugantic_supported_features__.update(features)
    
    def disable_feature(self, feature: Any):
        for item in self.wraps._unwrap_feature(feature):
            self.wraps.__plugantic_supported_features__.discard(item)

    def set_field_annotation(self, name: str, annotation: Type):
        self.wraps._create_annotation(name, annotation)

    def set_field_default(self, name: str, value: Any):
        self.wraps._create_field_default(name, value)

    def remove_field_default(self, name: str):
        self.set_field_default(name, ...)

SimplePluginDowncastCallback = TypeAliasType("SimplePluginDowncastCallback", Callable[[PluginDowncastHandler[T]], None], type_params=(T,))
PluginDowncastCallbacks = TypeAliasType("PluginDowncastCallbacks", RecursiveList[SimplePluginDowncastCallback[T]], type_params=(T,))
