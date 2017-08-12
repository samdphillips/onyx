
from collections import namedtuple

lookup_result = namedtuple('lookup_result', 'is_success klass method')

def success(klass, method):
    return lookup_result(True, klass, method)

def failure():
    return lookup_result(False, None, None)


_class_fields = \
    'name super_class instance_vars class_vars trait method_dict class_method_dict'
class Class(namedtuple('Class', _class_fields)):
    is_class = True

    def lookup_instance_method(self, selector):
        if selector in self.method_dict:
            return success(self, self.method_dict[selector])
        elif self.trait is not None and selector in self.trait:
            return success(self, self.trait[selector])
        elif self.super_class is None:
            return failure()
        else:
            return self.super_class.lookup_instance_method(selector)

    def lookup_method(self, vm, selector, is_class):
        if is_class:
            return self.lookup_class_method(vm, selector)
        else:
            return self.lookup_instance_method(selector)
