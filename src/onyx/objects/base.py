
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


class SmallInt(int, Base):
    pass


class String(str, Base):
    pass


class Super(namedtuple('Super', 'receiver klass'), Base):
    @property
    def is_class(self):
        return self.receiver.is_class

    def onyx_class(self, vm):
        return self.klass.super_class

    def deref(self):
        return self.receiver
