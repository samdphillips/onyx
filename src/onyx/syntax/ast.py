
from collections import namedtuple


class Node:
    is_assign = False
    is_block = False
    is_cascade = False
    is_class = False
    is_const = False
    is_message = False
    is_message_send = False
    is_meta = False
    is_method = False
    is_primitive_message = False
    is_ref = False
    is_return = False
    is_seq = False
    is_trait = False


class Assign(namedtuple('Assign', 'var expr'), Node):
    is_assign = True


class Block(namedtuple('Block', 'args temps statements'), Node):
    is_block = True


class Cascade(namedtuple('Cascade', 'receiver messages'), Node):
    is_cascade = True


_class_fields = \
    'name superclass_name instance_vars meta methods trait_expr'
class Class(namedtuple('Class', _class_fields), Node):
    is_class = True


# XXX: mark value immutable
class Const(namedtuple('Const', 'value'), Node):
    is_const = True

    named_values = {
        'true': True,
        'false': False,
        'nil': None
    }

    @classmethod
    def get(cls, name):
        return cls(cls.named_values[name])


class Meta(namedtuple('Meta', 'instance_vars methods'), Node):
    is_meta = True


class Method(namedtuple('Method', 'name args temps statements'), Node):
    is_method = True


class Message(namedtuple('Message', 'selector args'), Node):
    is_message = True


class PrimitiveMessage(Message):
    is_primitive_message = True


class Ref(namedtuple('Ref', 'name'), Node):
    is_ref = True


class Return(namedtuple('Return', 'expression'), Node):
    is_return = True

class Send(namedtuple('Send', 'receiver message'), Node):
    is_message_send = True


class Seq(namedtuple('Seq', 'statements'), Node):
    is_seq = True


class Trait(namedtuple('Trait', 'name methods trait_expr'), Node):
    is_trait = True
