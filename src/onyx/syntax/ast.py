
from collections import namedtuple


class Node:
    is_const = False
    is_message = False
    is_message_send = False
    is_primitive_message = False
    is_ref = False

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


class Ref(namedtuple('Ref', 'name'), Node):
    is_ref = True


class Send(namedtuple('Send', 'receiver message'), Node):
    is_message_send = True

class Message(namedtuple('Message', 'selector args'), Node):
    is_message = True

class PrimitiveMessage(Message):
    is_primitive_message = True
