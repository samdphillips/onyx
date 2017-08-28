
from .base import Base

class UndefinedObject(Base):
    def __bool__(self):
        return False

class _True(Base):
    def __bool__(self):
        return True

class _False(Base):
    def __bool__(self):
        return False

true = _True()
false = _False()
nil = UndefinedObject()


def onyx_bool(value):
    if value:
        return true
    return false
