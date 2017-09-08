
from collections import namedtuple

from .base import Base

class Trait(namedtuple('Trait', 'name method_dict class_method_dict'), Base):
    def merge_trait(self, trait):
        for k,v in trait.method_dict.items():
            if k not in self.method_dict:
                self.method_dict[k] = v

        for k,v in trait.class_method_dict.items():
            if k not in self.class_method_dict:
                self.class_method_dict[k] = v
        return self
