
from weakref import WeakValueDictionary

from .base import Base

_symbols = WeakValueDictionary()
def get_symbol(name):
    s = _symbols.get(name)
    if not s:
        s = Symbol(name)
        _symbols[name] = s
    return s


class Symbol(str, Base):
    pass
