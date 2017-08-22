
from collections import namedtuple

import onyx.objects as o
import onyx.utils as u

class Node:
    def visit(self, visitor, *args):
        method_name = 'visit_' + u.camel_to_snake(self.__class__.__name__)
        getattr(visitor, method_name)(self, *args)


_common_ast_node_fields = 'source_info'
def ast_node(name, fields):
    all_fields = _common_ast_node_fields + " " + fields
    nt = namedtuple(name, all_fields)
    class _frame(nt, Node):
        pass
    _frame.__name__ = name
    return _frame


Assign = ast_node('Assign', 'var expr')
Block = ast_node('Block', 'args temps statements')
Cascade = ast_node('Cascade', 'messages')
Class = ast_node('Class', 'name superclass_name instance_vars meta methods trait_expr')


# XXX: mark value immutable
class Const(namedtuple('Const', 'source_info value'), Node):
    is_const = True

    named_values = {
        'true':  o.true,
        'false': o.false,
        'nil':   o.nil
    }

    @classmethod
    def get(cls, source_info, name):
        return cls(source_info, cls.named_values[name])


Meta = ast_node('Meta', 'instance_vars methods')
Method = ast_node('Method', 'name args temps statements')
Message = ast_node('Message', 'selector args')


class PrimitiveMessage(Message):
    pass


Ref = ast_node('Ref', 'name')
Return = ast_node('Return', 'expression')
Send = ast_node('Send', 'receiver message')
Seq = ast_node('Seq', 'statements')
Trait = ast_node('Trait', 'name meta methods trait_expr')
