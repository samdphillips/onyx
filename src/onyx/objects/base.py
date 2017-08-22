
from collections import namedtuple


class Base:
    is_class = False

    def onyx_class(self, vm):
        name = self.__class__.__name__.lstrip('_')
        return vm.globals.lookup(name).value

    def lookup_instance_var(self, name):
        pass


class SmallInt(int, Base):
    pass


class String(str, Base):
    pass


class Super(namedtuple('Super', 'receiver klass')):
    pass
