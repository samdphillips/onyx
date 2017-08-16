
from collections import namedtuple

from .intrinsic import nil, true, false, onyx_bool
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
