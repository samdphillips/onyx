
from collections import namedtuple

from .base import Base
from .intrinsic import nil

class Object(namedtuple('Object', 'klass slots'), Base):
    @classmethod
    def new_instance(cls, klass, num_slots):
        return cls(klass, [nil] * num_slots)

    def onyx_class(self, vm):
        return self.klass
