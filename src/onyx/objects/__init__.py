
import attr
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


Symbol = type('Symbol', (str, Base), {})


@attr.s(frozen=True)
class BlockClosure(Base):
    env = attr.ib()
    retp = attr.ib(
        validator=attr.validators.optional(attr.validators.instance_of(int))
    )
    block = attr.ib()


Continuation = type(
    'Continuation',
    (namedtuple('Continuation', 'frames'), Base),
    {})
Method = type(
    'Method',
    (namedtuple('Method', 'name args temps statements source_info'), Base),
    {})


@attr.s(frozen=True)
class Character(Base):
    codepoint = attr.ib(validator=attr.validators.instance_of(int))


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

_chars = WeakValueDictionary()
def get_character(codepoint):
    c = _chars.get(codepoint)
    if not c:
        c = Character(codepoint)
        _chars[codepoint] = c
    return c
