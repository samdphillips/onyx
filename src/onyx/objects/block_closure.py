
from collections import namedtuple

class BlockClosure(namedtuple('BlockClosure', 'env receiver retp block')):
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('BlockClosure').value
