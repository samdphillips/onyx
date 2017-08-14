
from .character import Character
from .symbol import get_symbol

class SmallInt(int):
    def onyx_class(self, vm):
        return vm.globals.lookup('SmallInt').value
