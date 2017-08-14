
from .character import Character
from .symbol import get_symbol

class SmallInt(int):
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('SmallInt').value
