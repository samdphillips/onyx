
from collections import namedtuple

from .base import Base

class BlockClosure(namedtuple('BlockClosure', 'env retp block'), Base):
    pass
