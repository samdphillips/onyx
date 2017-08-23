
from collections import namedtuple

from .base import Base

class Continuation(namedtuple('Continuation', 'frames'), Base):
    pass
