
import attr

from .base import Base
from .intrinsic import nil

@attr.s
class Slot:
    value = attr.ib()

    def assign(self, value):
        self.value = value


@attr.s(frozen=True, slots=True, cmp=False, hash=False)
class Object(Base):
    cls = attr.ib()
    slots = attr.ib()

    @classmethod
    def new_instance(cls, onyx_class, num_slots):
        return cls(onyx_class, [Slot(nil) for _ in range(num_slots)])

    def onyx_class(self, vm):
        return self.cls

    def get_slot(self, i):
        return self.slots[i]
