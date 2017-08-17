
from collections import namedtuple

class Trait(namedtuple('Trait', 'name method_dict class_method_dict')):
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('Trait').value

    def merge_trait(self, trait):
        md = dict(self.method_dict)
        for k,v in trait.method_dict.items():
            if k not in md:
                md[k] = v

        clmd = dict(self.class_method_dict)
        for k,v in trait.class_method_dict.items():
            if k not in md:
                clmd[k] = v

        return self._replace(method_dict=md, class_method_dict=clmd)
