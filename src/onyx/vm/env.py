
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
    def __init__(self):
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
            self.add_binding(n, None)

    def lookup(self, name):
        return self.bindings.get(name)

class BlockEnv(Env):
    def __init__(self, parent):
        super(BlockEnv, self).__init__()
        self.parent = parent

    def lookup(self, name):
        return (super().lookup(name) or
                (self.parent and self.parent.lookup(name)))


class MethodEnv(Env):
    def __init__(self, klass, receiver):
        super(MethodEnv, self).__init__()
        self.klass = klass
        self.receiver = receiver
        self.self_slot = self.add_binding(o.get_symbol('self'),
                                          self.receiver,
                                          ImmutableBinding)
        self.super_slot = self.add_binding(o.get_symbol('super'),
                                           o.Super(receiver, klass),
                                           ImmutableBinding)

    def lookup(self, name):
        if name == 'self':
            return self.self_slot
        elif name == 'super':
            return self.super_slot
        elif name in self.bindings:
            return super().lookup(name)
        elif (isinstance(self.receiver, o.Object) and
              name in self.klass.all_instance_variables()):
            slot = self.klass.instance_variable_slot(name)
            return self.receiver.get_slot(slot)
        else:
            raise Exception('error finding variable: {}'.format(name))


class GlobalEnv(Env):
    def __init__(self):
        super(GlobalEnv, self).__init__()
        self.add_binding('nil', None, ImmutableBinding)

    def lookup(self, name):
        binding = super().lookup(name)
        if binding is None:
            binding = self.add_binding(name, None)
        return binding
