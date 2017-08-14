
from collections import namedtuple

_class_fields = \
    'name super_class instance_vars class_vars method_dict class_method_dict'
class Class(namedtuple('Class', _class_fields)):
    is_class = True

    def lookup_method(self, vm, selector, is_class):
        if is_class:
            return self.lookup_class_method(vm, selector)
        else:
            return self.lookup_instance_method(selector)
