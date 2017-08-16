
from collections import namedtuple

from .intrinsic import nil

class Object(namedtuple('Object', 'klass slots')):
    @classmethod
    def new_instance(cls, klass, num_slots):
        return cls(klass, [nil] * num_slots)
