
from collections import namedtuple

from .base import Base


class Method(namedtuple('Method', 'name args temps statements source_info'), Base):
    pass
