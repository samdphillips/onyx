
from collections import namedtuple

import onyx.objects as o

class ImmutableBinding(namedtuple('ImmutableBinding', 'name value')):
    pass


class MutableBinding:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def assign(self, value):
        self.value = value


class Env:
    def __init__(self, parent=None):
        self.parent = parent
        self.bindings = {}

    def add_binding(self, name, value, binding=MutableBinding):
        b = binding(name, value)
        self.bindings[name] = b
        return b

    def add_args(self, names, values):
        for n, v in zip(names, values):
            self.add_binding(n, v, ImmutableBinding)

    def add_temps(self, names):
        for n in names:
            self.add_binding(n, o.nil)

    def lookup(self, name):
        return (self.bindings.get(name) or
                (self.parent and self.parent.lookup(name)))


class GlobalEnv(Env):
    def __init__(self):
        super().__init__()
        self.add_binding('nil', o.nil, ImmutableBinding)

    def lookup(self, name):
        binding = super().lookup(name)
        if binding is None:
            binding = self.add_binding(name, o.nil)
        return binding
