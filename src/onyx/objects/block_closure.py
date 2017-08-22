
from collections import namedtuple

from .base import Base

class BlockClosure(namedtuple('BlockClosure', 'env receiver retp block'), Base):
    pass
