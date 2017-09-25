
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

    def children(self):
        for f in attr.fields(self.__class__):
            if f.metadata.get('child', False):
                value = getattr(self, f.name)
                if value:
                    yield f.name, value

    def visit(self, visitor, *args):
        return self.visit_static(getattr(visitor, self.visit_name), *args)

    def visit_static(self, visitor_func, *args):
        return visitor_func(self, *args)

    def visit_children_static(self, visitor_func, *args):
        new_nodes = {}
        for name, node in self.children():
            if type(node) is list:
                new_nodes[name] = [visitor_func(x, *args) for x in node]
            else:
                new_nodes[name] = visitor_func(node, *args)
        return self._replace(**new_nodes)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                all((getattr(self, x) == getattr(other, x)
                     for x in self.fields)))


def visitee(cls):
    cls.visit_name = 'visit_' + u.camel_to_snake(cls.__name__)
    return cls


def child_attr(ctype=None, optional=False):
    validator = attr.validators.instance_of(ctype or Node)
    if optional:
        validator = attr.validators.optional(validator)
    return attr.ib(metadata={'child': True},
                   validator=validator)


@visitee
@attr.s(cmp=False)
class Assign(Node):
    var = attr.ib()
    expr = child_attr()


@visitee
@attr.s(cmp=False)
class Block(Node):
    args = attr.ib()
    temps = attr.ib()
    statements = child_attr()


@visitee
@attr.s(cmp=False)
class Cascade(Node):
    messages = child_attr(list)


@visitee
@attr.s(cmp=False)
class Class(Node):
    name = attr.ib()
    superclass_name = attr.ib()
    instance_vars = attr.ib()
    meta = child_attr(optional=True)
    methods = child_attr(list)
    trait_expr = child_attr(optional=True)


# XXX: mark value immutable
@visitee
@attr.s(cmp=False)
class Const(Node):
    value = attr.ib()
    is_const = True

    named_values = {
        'true':  True,
        'false': False,
        'nil':   None
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
    methods = child_attr(list)


@visitee
@attr.s(cmp=False)
class Method(Node):
    name = attr.ib()
    args = attr.ib()
    temps = attr.ib()
    statements = child_attr()


@visitee
@attr.s(cmp=False)
class Message(Node):
    selector = attr.ib()
    args = child_attr(list)
    method_cache = attr.ib(init=False, default=attr.Factory(dict))


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
    expression = child_attr()


@visitee
@attr.s(cmp=False)
class Send(Node):
    receiver = child_attr()
    message = child_attr()


@visitee
@attr.s(cmp=False)
class Seq(Node):
    statements = child_attr(list)


@visitee
@attr.s(cmp=False)
class Trait(Node):
    name = attr.ib()
    meta = child_attr(optional=True)
    methods = child_attr(list)
    trait_expr = child_attr(optional=True)


@visitee
@attr.s(cmp=False)
class WhileTrue(Node):
    temps = attr.ib()
    test = child_attr()
    body = child_attr()
