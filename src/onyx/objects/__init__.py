
from collections import namedtuple

from .block_closure import BlockClosure
from .character import Character
from .klass import Class
from .method import Method
from .symbol import get_symbol

class SmallInt(int):
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('SmallInt').value

    def lookup_instance_var(self, name):
        pass


class Super(namedtuple('Super', 'receiver klass')):
    pass


class _Nil:
    is_class = False

    def __bool__(self):
        return False

    def onyx_class(self, vm):
        return vm.globals.lookup('UndefinedObject').value


class _True:
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('True').value

    def __bool__(self):
        return True


class _False:
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('False').value

    def __bool__(self):
        return False

true = _True()
false = _False()
nil = _Nil()


def onyx_bool(value):
    if value:
        return true
    return false
