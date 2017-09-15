
import attr

from .base import Base
from .object import Object


@attr.s(slots=True, frozen=True)
class LookupResult:
    is_success = attr.ib()
    cls = attr.ib()
    method = attr.ib()

    @classmethod
    def success(cls, onyx_cls, method):
        return cls(True, onyx_cls, method)

    @classmethod
    def failure(cls):
        return cls(False, None, None)


@attr.s(slots=True, frozen=True)
class Class(Base):
    is_class = True

    name = attr.ib()
    super_class = attr.ib()
    instance_variables = attr.ib()
    class_variables = attr.ib()
    method_dict = attr.ib()
    class_method_dict = attr.ib()

    def onyx_class(self, vm):
        return self

    def merge_trait(self, trait):
        for k,v in trait.method_dict.items():
            if k not in self.method_dict:
                self.method_dict[k] = v

        for k,v in trait.class_method_dict.items():
            if k not in self.class_method_dict:
                self.class_method_dict[k] = v
        return self

    def all_instance_variables(self):
        if self.super_class:
            return self.super_class.all_instance_variables() + self.instance_variables
        else:
            return self.instance_variables

    def instance_variable_slot(self, name):
        return self.all_instance_variables().index(name)

    def num_slots(self):
        return len(self.all_instance_variables())

    def new_instance(self):
        return Object.new_instance(self, self.num_slots())

    def lookup_instance_method(self, selector):
        if selector in self.method_dict:
            return LookupResult.success(self, self.method_dict[selector])
        elif self.super_class:
            return self.super_class.lookup_instance_method(selector)
        else:
            return LookupResult.failure()

    def lookup_class_method(self, vm, selector):
        if selector in self.class_method_dict:
            return LookupResult.success(self, self.class_method_dict[selector])
        elif self.super_class:
            return self.super_class.lookup_class_method(vm, selector)
        else:
            return vm.core_lookup('Class').lookup_instance_method(selector)

    def lookup_method(self, vm, selector, is_class):
        if is_class:
            return self.lookup_class_method(vm, selector)
        else:
            return self.lookup_instance_method(selector)
