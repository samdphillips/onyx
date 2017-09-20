
import attr
from collections import namedtuple

import onyx.objects as o
import onyx.utils as u


@attr.s(cmp=False)
class Node:
    source_info = attr.ib()
    visit_name = None

    @property
    def fields(self):
        return [f.name for f in attr.fields(self.__class__)
                    if f.name != 'source_info']

    def _replace(self, *args, **kwargs):
        return attr.evolve(self, *args, **kwargs)

    def visit(self, visitor, *args):
        return getattr(visitor, self.visit_name)(self, *args)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                all((getattr(self, x) == getattr(other, x)
                     for x in self.fields)))


def visitee(cls):
    cls.visit_name = 'visit_' + u.camel_to_snake(cls.__name__)
    return cls


@visitee
@attr.s(cmp=False)
class Assign(Node):
    var = attr.ib()
    expr = attr.ib()


@visitee
@attr.s(cmp=False)
class Block(Node):
    args = attr.ib()
    temps = attr.ib()
    statements = attr.ib()


@visitee
@attr.s(cmp=False)
class Cascade(Node):
    messages = attr.ib()


@visitee
@attr.s(cmp=False)
class Class(Node):
    name = attr.ib()
    superclass_name = attr.ib()
    instance_vars = attr.ib()
    meta = attr.ib()
    methods = attr.ib()
    trait_expr = attr.ib()


# XXX: mark value immutable
@visitee
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


@visitee
@attr.s(cmp=False)
class GlobalRef(Node):
    name = attr.ib()


@visitee
@attr.s(cmp=False)
class Meta(Node):
    methods = attr.ib()


@visitee
@attr.s(cmp=False)
class Method(Node):
    name = attr.ib()
    args = attr.ib()
    temps = attr.ib()
    statements = attr.ib()


@visitee
@attr.s(cmp=False)
class Message(Node):
    selector = attr.ib()
    args = attr.ib()


@visitee
@attr.s(cmp=False)
class ModuleImport(Node):
    name = attr.ib()


@visitee
@attr.s(cmp=False)
class ModuleName(Node):
    id = attr.ib()


@visitee
@attr.s(cmp=False)
class PrimitiveMessage(Message):
    primitive = None


@visitee
@attr.s(cmp=False)
class Ref(Node):
    name = attr.ib()


@visitee
@attr.s(cmp=False)
class Return(Node):
    expression = attr.ib()


@visitee
@attr.s(cmp=False)
class Send(Node):
    receiver = attr.ib()
    message = attr.ib()


@visitee
@attr.s(cmp=False)
class Seq(Node):
    statements = attr.ib()


@visitee
@attr.s(cmp=False)
class Trait(Node):
    name = attr.ib()
    meta = attr.ib()
    methods = attr.ib()
    trait_expr = attr.ib()
