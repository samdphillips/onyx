
from collections import namedtuple
from weakref import WeakValueDictionary


from .base import Base
from .klass import Class
from .trait import Trait

onyx_class_map = {
    int: 'SmallInt',
    str: 'String',
    bytearray: 'ByteArray',
    list: 'Array'
}

def String(v):
    return str(v)

def ByteArray(v):
    return bytearray(v)

def Array(v):
    return list(v)

Symbol = type('Symbol', (str, Base), {})

BlockClosure = type(
    'BlockClosure',
    (namedtuple('BlockClosure', 'env retp block'), Base),
    {})

Character = type('Character', (int, Base), {})
Continuation = type(
    'Continuation',
    (namedtuple('Continuation', 'frames'), Base),
    {})
Method = type(
    'Method',
    (namedtuple('Method', 'name args temps statements source_info'), Base),
    {})


class Super(namedtuple('Super', 'receiver klass'), Base):
    @property
    def is_class(self):
        return getattr(self.receiver, 'is_class', False)

    def onyx_class(self, vm):
        return self.klass.super_class

    def deref(self):
        return self.receiver


class UndefinedObject(Base):
    def __bool__(self):
        return False


class _True(Base):
    def __bool__(self):
        return True


class _False(Base):
    def __bool__(self):
        return False


true = _True()
false = _False()
nil = UndefinedObject()


def onyx_bool(value):
    if value:
        return true
    return false


_symbols = WeakValueDictionary()
def get_symbol(name):
    s = _symbols.get(name)
    if not s:
        s = Symbol(name)
        _symbols[name] = s
    return s
