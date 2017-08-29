
from collections import namedtuple


class Base:
    is_class = False

    def onyx_class(self, vm):
        name = self.__class__.__name__.lstrip('_')
        return vm.globals.lookup(name).value

    def deref(self):
        return self

    def debug(self):
        print(self.__class__.__name__)
