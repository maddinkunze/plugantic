from __future__ import annotations

from typing_extensions import TypeVar, Iterable, TypeGuard, TypeAliasType, Callable
from itertools import combinations, product

T = TypeVar("T")
RecursiveList = TypeAliasType("RecursiveList", Iterable["RecursiveListItem[T]"], type_params=(T,))
RecursiveListItem = TypeAliasType("RecursiveListItem", T | RecursiveList[T], type_params=(T,))

def recursive_linear(items: RecursiveList[T], typeguard: Callable[[RecursiveListItem[T]], TypeGuard[T]], join: Callable[[Iterable[T]], T]) -> Iterable[T]:
    result = []
    for item in items:
        if typeguard(item):
            result.append(item)
        else:
            result.extend(recursive_powerset(item, typeguard, join))
    return result

def recursive_powerset(items: RecursiveList[T], typeguard: Callable[[RecursiveListItem[T]], TypeGuard[T]], join: Callable[[Iterable[T]], T]) -> Iterable[T]:
    arbitrary_subset = []
    subsets = []
    for downcast in items:
        if typeguard(downcast):
            arbitrary_subset.append(downcast)
        else:
            linear_subset = recursive_linear(downcast, typeguard, join)
            linear_subset = ((), *((d,) for d in linear_subset))
            subsets.append(linear_subset)

    arbitrary_powerset = [()]
    for l in range(1, len(arbitrary_subset) + 1):
        arbitrary_powerset.extend(combinations(arbitrary_subset, l))
    subsets.append(arbitrary_powerset)

    powerset = []
    for subset in product(*subsets):
        callbacks = [c for s in subset for c in s]
        if not callbacks:
            continue
        powerset.append(join(callbacks))

    return powerset
