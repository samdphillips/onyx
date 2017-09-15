
import attr

from .base import Base

@attr.s(frozen=True)
class Trait(Base):
    name = attr.ib()
    method_dict = attr.ib()
    class_method_dict = attr.ib()

    def merge_trait(self, trait):
        for k,v in trait.method_dict.items():
            if k not in self.method_dict:
                self.method_dict[k] = v

        for k,v in trait.class_method_dict.items():
            if k not in self.class_method_dict:
                self.class_method_dict[k] = v
        return self
