
from collections import namedtuple

from .object import Object

lookup_result = namedtuple('lookup_result', 'is_success klass method')

def success(klass, method):
    return lookup_result(True, klass, method)

def failure():
    return lookup_result(False, None, None)


_class_fields = \
    'name super_class instance_vars class_vars trait method_dict class_method_dict'
class Class(namedtuple('Class', _class_fields)):
    is_class = True

    def onyx_class(self, vm):
        return self

    def merge_trait(self, trait):
        return self._replace(trait=trait)

    def all_instance_vars(self):
        if self.super_class:
            return self.super_class.all_instance_vars() + self.instance_vars
        else:
            return self.instance_vars

    def num_slots(self):
        return len(self.all_instance_vars())

    def new_instance(self):
        return Object(self, self.num_slots())

    def lookup_instance_method(self, selector):
        if selector in self.method_dict:
            return success(self, self.method_dict[selector])
        elif self.trait and selector in self.trait.method_dict:
            return success(self, self.trait.method_dict[selector])
        elif self.super_class:
            return self.super_class.lookup_instance_method(selector)
        else:
            return failure()

    def lookup_class_method(self, vm, selector):
        if selector in self.class_method_dict:
            return success(self, self.class_method_dict[selector])
        elif self.trait and selector in self.trait.class_method_dict:
            return success(self, self.trait.class_method_dict[selector])
        elif self.super_class:
            return self.super_class.lookup_class_method(vm, selector)
        else:
            return vm.globals.lookup('Class').value.lookup_instance_method(selector)

    def lookup_method(self, vm, selector, is_class):
        if is_class:
            return self.lookup_class_method(vm, selector)
        else:
            return self.lookup_instance_method(selector)
