
import attr
from collections import namedtuple

import onyx.objects as o
import onyx.utils as u


@attr.s(cmp=False)
class Node:
    source_info = attr.ib()

    @property
    def fields(self):
        return [f.name for f in attr.fields(self.__class__)
                    if f.name != 'source_info']

    def _replace(self, *args, **kwargs):
        return attr.evolve(self, *args, **kwargs)

    def visit(self, visitor, *args):
        method_name = 'visit_' + u.camel_to_snake(self.__class__.__name__)
        return getattr(visitor, method_name)(self, *args)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                all((getattr(self, x) == getattr(other, x)
                     for x in self.fields)))


@attr.s(cmp=False)
class Assign(Node):
    var = attr.ib()
    expr = attr.ib()


@attr.s(cmp=False)
class Block(Node):
    args = attr.ib()
    temps = attr.ib()
    statements = attr.ib()


@attr.s(cmp=False)
class Cascade(Node):
    messages = attr.ib()


@attr.s(cmp=False)
class Class(Node):
    name = attr.ib()
    superclass_name = attr.ib()
    instance_vars = attr.ib()
    meta = attr.ib()
    methods = attr.ib()
    trait_expr = attr.ib()


# XXX: mark value immutable
@attr.s(cmp=False)
class Const(Node):
    value = attr.ib()
    is_const = True
    fields = ['value']

    named_values = {
        'true':  o.true,
        'false': o.false,
        'nil':   o.nil
    }

    @classmethod
    def get(cls, source_info, name):
        return cls(source_info, cls.named_values[name])


@attr.s(cmp=False)
class GlobalRef(Node):
    name = attr.ib()


@attr.s(cmp=False)
class Meta(Node):
    methods = attr.ib()


@attr.s(cmp=False)
class Method(Node):
    name = attr.ib()
    args = attr.ib()
    temps = attr.ib()
    statements = attr.ib()


@attr.s(cmp=False)
class Message(Node):
    selector = attr.ib()
    args = attr.ib()


@attr.s(cmp=False)
class ModuleImport(Node):
    name = attr.ib()


@attr.s(cmp=False)
class ModuleName(Node):
    id = attr.ib()


class PrimitiveMessage(Message):
    pass


@attr.s(cmp=False)
class Ref(Node):
    name = attr.ib()


@attr.s(cmp=False)
class Return(Node):
    expression = attr.ib()


@attr.s(cmp=False)
class Send(Node):
    receiver = attr.ib()
    message = attr.ib()


@attr.s(cmp=False)
class Seq(Node):
    statements = attr.ib()


@attr.s(cmp=False)
class Trait(Node):
    name = attr.ib()
    meta = attr.ib()
    methods = attr.ib()
    trait_expr = attr.ib()
