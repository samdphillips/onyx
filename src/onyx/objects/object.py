
from collections import namedtuple

from .base import Base
from .intrinsic import nil

class Slot:
    def __init__(self, value):
        self.value = value

    def assign(self, value):
        self.value = value

class Object(namedtuple('Object', 'klass slots'), Base):
    @classmethod
    def new_instance(cls, klass, num_slots):
        return cls(klass, [Slot(nil) for _ in range(num_slots)])

    def onyx_class(self, vm):
        return self.klass

    def lookup_instance_variable(self, name):
        i = self.klass.instance_variable_index(name)
        if i < 0:
            return
        return self.slots[i]
