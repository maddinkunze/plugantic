from __future__ import annotations

from typing_extensions import ClassVar, Iterable, Type, Union, Self, Literal, Any, Callable, Generic, TypeVar, TypeVarTuple, Unpack, TypeAliasType, TypedDict, get_type_hints, get_origin, get_args, TYPE_CHECKING
from random import randint
from pydantic import BaseModel, GetCoreSchemaHandler, Field, model_validator
from pydantic.fields import FieldInfo
from pydantic_core.core_schema import tagged_union_schema

from ._helpers import recursive_powerset, recursive_linear, RecursiveList
from ._types import _VanishBase

F = TypeVar("T")
Ts = TypeVarTuple("Ts")

if TYPE_CHECKING:
    _plugin_base = Generic[Unpack[Ts]]
    _feature_base = Generic[F]
else:
    _plugin_base = _VanishBase
    _feature_base = type

class PluginFeature(_feature_base):
    def __new__(cls, value: Any):
        return super().__new__(cls, f"{cls.__name__}[{value}]", (cls,), {})

    def __init__(self, value: Any):
        self._value = value

    def __class_getitem__(cls, value: Any):
        return cls(value)

    @staticmethod
    def _get_other(other: Any):
        if isinstance(other, PluginFeature):
            return other._value
        return other

    def __eq__(self, other: Any):
        return self._value == self._get_other(other)

    def __neq__(self, other: Any):
        return self._value != self._get_other(other)

    def __or__(self, other: PluginFeature):
        return Union[self, other]

    def __hash__(self):
        return hash(self._value)

class PluganticConfig(TypedDict):
    varname_type: str|None = None
    value: str|None = None
    supported_features: set[PluganticFeatureType]|tuple[PluganticFeatureType, ...]=()
    required_features: _RequiresFeatureSpec|None=None
    auto_downcast: bool = False
    auto_downcasts: PluginDowncastCallbacks|None=None

class PluginModel(BaseModel, _plugin_base):
    __plugantic_varname_type__: ClassVar[str] = "type"
    __plugantic_supported_features__: ClassVar[set[_PFeatSpec]] = set()
    __plugantic_required_features__: ClassVar[_RequiresFeatureSpec|None] = None
    __plugantic_inherit_features__: ClassVar[bool] = True
    __plugantic_generic_supertype__: ClassVar[type|None] = None
    __plugantic_auto_downcast__: ClassVar[bool] = False # whether this class is an auto-downcast
    __plugantic_auto_downcasts__internal__: ClassVar[list[type]] # only there for temporarily saving all auto-downcasts as otherwise they would get optimized away by the interpreter/bytecode-compiler; NOTE: there are NO guarantees made about this variable at all and it should ONLY be used for reference storage of downcasts
    __plugantic_auto_downcast_callbacks__: ClassVar[PluginDowncastCallbacks|None] = None
    __plugantic_was_schema_created__: ClassVar[bool] = False
    __plugantic_check_schema_usage__: ClassVar[bool] = True
    __plugantic_internal_name__: ClassVar[str] = ""

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

        if cls.__plugantic_generic_supertype__:
            return cls._require_additional_features(*args)

        requires_features, supports_features = cls._unpack_features(*args)
        return type(cls.__name__, (cls,), {}, supported_features=supports_features, required_features=requires_features, _plugantic_generic_supertype=cls, _plugantic_internal_name=f"Getitem{randint(1000, 9999)}")

    def __init_subclass__(cls, *,
        varname_type: str|None=None,
        value: str|None=None,
        supported_features: set[_PAnyFeat]|tuple[_PAnyFeat, ...]=(),
        required_features: _RequiresFeatureSpec|None=None,
        auto_downcast: bool=False,
        auto_downcasts: PluginDowncastCallbacks|None=None,
        _plugantic_generic_supertype: type|None=None,
        _plugantic_downcast_callback: SimplePluginDowncastCallback|None=None,
        _plugantic_internal_name: str|None=None,
    **kwargs):
        skip_schema_check = (
            (_plugantic_generic_supertype is not None) or
            (_plugantic_downcast_callback is not None)
        )
        if not skip_schema_check and cls._check_plugantic_schema_usage():
            raise ValueError(f"Schema of {cls.__name__} has already been created. Creating new subclasses after the schema has been created will lead to undefined behaviour.")

        super().__init_subclass__(**kwargs)

        if cls.plugantic_config:
            varname_type = cls.plugantic_config.get("varname_type", None) or varname_type
            value = cls.plugantic_config.get("value", None) or value
            supported_features = cls.plugantic_config.get("supported_features", ()) or supported_features
            required_features = cls.plugantic_config.get("required_features", None) or required_features
            auto_downcast = cls.plugantic_config.get("auto_downcast", False) or auto_downcast
            auto_downcasts = cls.plugantic_config.pop("auto_downcasts", None) or auto_downcasts

        cls.__plugantic_was_schema_created__ = False

        cls.__plugantic_generic_supertype__ = _plugantic_generic_supertype
        cls.__plugantic_required_features__ = required_features
        cls.__plugantic_auto_downcast_callbacks__ = None
        cls.__plugantic_auto_downcasts__internal__ = []

        if _plugantic_internal_name:
            cls.__plugantic_internal_name__ = cls.__plugantic_internal_name__ + _plugantic_internal_name
        else:
            cls.__plugantic_internal_name__ = cls.__name__

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
            cls.__plugantic_auto_downcast__ = True
            _plugantic_downcast_callback(PluginDowncastHandler(cls))

        cls.__plugantic_auto_downcast_callbacks__ = auto_downcasts

    @classmethod
    def _require_additional_features(cls, *features: _PFeatSpec) -> Type[Self]:
        _base = cls.__plugantic_generic_supertype__ or cls
        required_features = cls.__plugantic_required_features__

        
        if required_features is None:
            required_features = _RequiresAllFeatures(all_of=features)
        elif isinstance(required_features, _RequiresAllFeatures):
            required_features = required_features._require_additional_features(*features)
        else:
            required_features = _RequiresAllFeatures(all_of={required_features, *features})

        supported_features = cls.__plugantic_supported_features__ | set(features)

        return type(_base.__name__, (_base,), {}, supported_features=supported_features, required_features=required_features, _plugantic_generic_supertype=_base, _plugantic_internal_name=f"Require{randint(1000, 9999)}")

    @classmethod
    def _ensure_downcasts(cls):
        if not cls.__plugantic_auto_downcast_callbacks__:
            return

        callbacks = cls.__plugantic_auto_downcast_callbacks__
        cls.__plugantic_auto_downcast_callbacks__ = None

        cls._create_downcasts(callbacks)

    @classmethod
    def _create_downcasts(cls, downcast_callbacks: PluginDowncastCallbacks):
        for callback in cls._create_powerset_downcast_callbacks(downcast_callbacks):
            subcls = type(cls.__name__, (cls,), {}, _plugantic_downcast_callback=callback, _plugantic_internal_name=f"Downcast{randint(1000, 9999)}")
            cls.__plugantic_auto_downcasts__internal__.append(subcls) # store auto-downcasts temporarily to avoid them getting optimized away by the interpreter/bytecode-compiler

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
    def _unpack_features(cls, *features: Any) -> tuple[_RequiresFeatureSpec, set[PluginFeature]]:
        requires_all_features = set[_PFeatSpec]()
        supports_features = set[PluginFeature]()

        for feature in features:
            if isinstance(feature, _RequiresFeatureSpec):
                requires_all_features.add(feature)
                continue
            
            _any_features = set[PluginFeature]()
            if get_origin(feature) is Union:
                for sub_feature in get_args(feature):
                    if not isinstance(sub_feature, PluginFeature):
                        continue
                    _any_features.add(sub_feature)
            
            if len(_any_features) == 1:
                feature = _any_features.pop()

            if _any_features:
                requires_all_features.add(_RequiresAnyFeature(any_of=_any_features))
                supports_features.update(_any_features)
                continue

            if not isinstance(feature, PluginFeature):
                continue

            requires_all_features.add(feature)
            supports_features.add(feature)

        return _RequiresAllFeatures(all_of=requires_all_features), supports_features

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
        return [subcls for subcls in cls.__subclasses__() if not subcls.__plugantic_auto_downcast__]

    @classmethod
    def _get_downcast_subclasses(cls):
        cls._ensure_downcasts()
        subclasses = set()
        for subcls in cls.__subclasses__():
            if not subcls.__plugantic_auto_downcast__:
                continue
            subclasses.add(subcls)
            subclasses.update(subcls._get_downcast_subclasses())
        return subclasses

    @classmethod
    def _get_valid_self_class(cls, filter: _PluginFeatureFilter) -> Type[Self]|None:
        if cls._is_valid_subclass(filter):
            return cls

        return cls._select_optimal_subclass(cls._get_valid_downcast_subclasses(filter), filter)

    @classmethod
    def _get_valid_downcast_subclasses(cls, filter: _PluginFeatureFilter) -> Iterable[Type[Self]]:
        return [subcls for subcls in cls._get_downcast_subclasses() if subcls._is_valid_subclass(filter)]

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

        # I dont know what the actual difference between `handler(...)` and `handler.generate_schema(...)` is
        # but somehow, any other constellation than this will cause errors (recursion depth exceeded, missing self-referential models, ...)
        # see commit #f785994 for details; before this commit, everything except basic usage worked, after it, everything worked again
        # everything is so weird :/
        choices = {
            subcls._get_declared_type(): 
            handler.generate_schema(subcls) if subcls.__plugantic_supported_features__
            else handler(subcls)
            for subcls in subclasses}
        return tagged_union_schema(choices, discriminator=cls.__plugantic_varname_type__)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        _required_features = None
        _base = cls

        if cls.__plugantic_generic_supertype__:
            _required_features = cls.__plugantic_required_features__
            _base = cls.__plugantic_generic_supertype__

        _filter = _PluginFeatureFilter(required_features=_required_features)
        _base._ensure_downcasts()
        _base.__plugantic_was_schema_created__ = True

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
    def applies_to(self, supported_features: set[_PFeatSpec]) -> bool:
        ...

    def _split_features(self, features: set[_PFeatSpec]) -> tuple[set[PluginFeature], set[Self]]:
        feats, specs = set(), set()
        for feature in features:
            if isinstance(feature, _RequiresFeatureSpec):
                specs.add(feature)
            else:
                feats.add(feature)
        return feats, specs

class _RequiresAnyFeature(_RequiresFeatureSpec):
    def __init__(self, *, any_of: set[_PFeatSpec]):
        self.any_of_features, self.any_of_specs = self._split_features(any_of)
    
    def applies_to(self, supported_features) -> bool:
        return (not self.any_of_features.isdisjoint(supported_features)) or any(spec.applies_to(supported_features) for spec in self.any_of_specs)

class _RequiresAllFeatures(_RequiresFeatureSpec):
    def __init__(self, *, all_of: set[_PFeatSpec]):
        self.all_of_features, self.all_of_specs = self._split_features(all_of)
    
    def _require_additional_features(self, *features: _PFeatSpec) -> Self:
        return type(self)(all_of=self.all_of_features | self.all_of_specs | set(features))

    def applies_to(self, supported_features) -> bool:
        return self.all_of_features.issubset(supported_features) and all(spec.applies_to(supported_features) for spec in self.all_of_specs)

class _PluginFeatureFilter:
    def __init__(self, *, required_features: _RequiresFeatureSpec|None=None):
        self.required_features = required_features

PluganticFeatureType = PluginFeature|Type[PluginFeature]
_PFeatSpec = _RequiresFeatureSpec|PluginFeature
_PAnyFeat = PluganticFeatureType|_RequiresFeatureSpec

T = TypeVar("T", bound=PluginModel)

class PluginDowncastHandler(Generic[T]):
    def __init__(self, wraps: Type[T]):
        self.wraps = wraps

    def get_raw_type(self) -> Type[T]:
        return self.wraps

    def enable_feature(self, feature: PluganticFeatureType):
        self.wraps.__plugantic_supported_features__.add(feature)
    
    def disable_feature(self, feature: PluganticFeatureType):
        self.wraps.__plugantic_supported_features__.discard(feature)

    def copy_and_update_field(self, name: str, other: FieldInfo):
        """Copy the field from the parent class and update it with the given kwargs"""
        field = self.wraps.model_fields.get(name, None)
        if field:
            field = FieldInfo.merge_field_infos(field, other)
        else:
            field = other
        setattr(self.wraps, name, field)

    def set_field_annotation(self, name: str, annotation: Type, *, merge_with_existing: bool=False):
        """Change the annotation of the given field (this will reset every other piece of info attached to the field such as the default value, description, ... unless `merge_with_existing` is set to True)"""
        if merge_with_existing:
            self.copy_and_update_field(name, FieldInfo(anotation=annotation))
        else:
            self.wraps._create_annotation(name, annotation)
            
    def set_field_default(self, name: str, value: Any, *, merge_with_existing: bool=False):
        """Change the default value of the given field (this will reset every other piece of info attached to the field such as the annotation, description, ... unless `merge_with_existing` is set to True)"""
        if merge_with_existing:
            self.copy_and_update_field(name, FieldInfo(default=value))
        else:
            self.wraps._create_field_default(name, value)

    def remove_field_default(self, name: str):
        self.set_field_default(name, ...)

    def set_class_var(self, name: str, value: Any, *, set_annotation: bool=False):
        if set_annotation:
            self.wraps._create_annotation(name, ClassVar, only_set_if_not_exists=True)
        setattr(self.wraps, name, value)

    def require_recursive_features(self, name: str, *features: Any, merge_with_existing: bool=False):
        annotation = self.wraps._get_declared_annotation(name)
        if not annotation:
            raise ValueError(f"Field {name} does not exist in {self.wraps}")
        if not issubclass(annotation, PluginModel):
            raise ValueError(f"Field {name} in {self.wraps} is not a PluginModel")

        annotation = annotation._require_additional_features(*features)
        self.set_field_annotation(name, annotation, merge_with_existing=merge_with_existing)

SimplePluginDowncastCallback = TypeAliasType("SimplePluginDowncastCallback", Callable[[PluginDowncastHandler[T]], None], type_params=(T,))
PluginDowncastCallbacks = TypeAliasType("PluginDowncastCallbacks", RecursiveList[SimplePluginDowncastCallback[T]], type_params=(T,))
