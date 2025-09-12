class _InjectBase:
    def __init__(self, *bases: type):
        self._bases = bases
    def __mro_entries__(self, bases):
        return tuple(base for base in self._bases if base not in bases)
_VanishBase = _InjectBase()
