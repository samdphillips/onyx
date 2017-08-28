
from .base import Base

class UndefinedObject(Base):
    def __bool__(self):
        return False

    def lookup_instance_variable(self, name):
        pass

class _True(Base):
    def __bool__(self):
        return True

    def lookup_instance_variable(self, name):
        pass

class _False(Base):
    def __bool__(self):
        return False

    def lookup_instance_variable(self, name):
        pass

true = _True()
false = _False()
nil = UndefinedObject()


def onyx_bool(value):
    if value:
        return true
    return false
