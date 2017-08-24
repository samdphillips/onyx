
from collections import namedtuple

from .base import Base

class BlockClosure(namedtuple('BlockClosure', 'env receiver retp block'), Base):
    def lookup_instance_var(self, name):
        pass
