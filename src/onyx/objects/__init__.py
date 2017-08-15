
from collections import namedtuple

from .character import Character
from .klass import Class
from .method import Method
from .symbol import get_symbol

class SmallInt(int):
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('SmallInt').value


class Super(namedtuple('Super', 'receiver klass')):
    pass


class _True:
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('True').value


class _False:
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('False').value

true = _True()
false = _False()


def onyx_bool(value):
    if value:
        return true
    return false
