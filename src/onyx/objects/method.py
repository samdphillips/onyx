
from collections import namedtuple

class Method(namedtuple('Method', 'name args temps statements')):
    is_class = False
