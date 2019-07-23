
import attr

import onyx.objects as o


@attr.s(frozen=True)
class ImmutableBinding:
    value = attr.ib()


@attr.s
class MutableBinding:
    value = attr.ib()

    def assign(self, value):
        self.value = value


class GlobalEnv:
    def __init__(self):
        self.bindings = {}

    def add_binding(self, name, value):
        b = MutableBinding(value)
        self.bindings[name] = b
        return b

    def lookup(self, name):
        b = self.bindings.get(name)
        if b is None:
            b = self.add_binding(name, None)
        return b


class EmptyEnv:
    def extend(self, i_values, m_slots):
        slots = ([ImmutableBinding(v) for v in i_values] +
                 [MutableBinding(None) for _ in range(m_slots)])
        ribs = [slots]
        return Env(ribs, None)


@attr.s
class Env:
    ribs = attr.ib()
    method_env = attr.ib()

    @property
    def self_slot(self):
        return self.method_env.self_slot

    @property
    def super_slot(self):
        return self.method_env.super_slot

    def extend(self, i_values, m_slots):
        slots = ([ImmutableBinding(v) for v in i_values] +
                 [MutableBinding(None) for _ in range(m_slots)])
        ribs = [slots] + self.ribs
        return Env(ribs, self.method_env)


@attr.s(init=False)
class MethodEnv:
    def __init__(self, klass, receiver):
        self.super_slot = ImmutableBinding(o.Super(receiver, klass))
        self.self_slot = ImmutableBinding(receiver)

    def extend(self, i_values, m_slots):
        slots = ([ImmutableBinding(v) for v in i_values] +
                 [MutableBinding(None) for _ in range(m_slots)])
        ribs = [slots]
        return Env(ribs, self)
