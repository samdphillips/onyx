
from collections import namedtuple

import onyx.objects as o
import onyx.utils as u


class Node:
    def visit(self, visitor, *args):
        method_name = 'visit_' + u.camel_to_snake(self.__class__.__name__)
        return getattr(visitor, method_name)(self, *args)

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                all((getattr(self, x) == getattr(other, x)
                     for x in self.fields)))




_common_ast_node_fields = 'source_info'
def ast_node(name, _fields):
    all_fields = _common_ast_node_fields + " " + _fields
    nt = namedtuple(name, all_fields)
    class _node(Node, nt):
        fields = _fields.split()
    _node.__name__ = name
    return _node


Assign = ast_node('Assign', 'var expr')
Block = ast_node('Block', 'args temps statements')
Cascade = ast_node('Cascade', 'messages')
Class = ast_node('Class', 'name superclass_name instance_vars meta methods trait_expr')


# XXX: mark value immutable
class Const(Node, namedtuple('Const', 'source_info value')):
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


Meta = ast_node('Meta', 'instance_vars methods')
Method = ast_node('Method', 'name args temps statements')
Message = ast_node('Message', 'selector args')
ModuleImport = ast_node('ModuleImport', 'name')
ModuleName = ast_node('ModuleName', 'id')


class PrimitiveMessage(Message):
    pass


Ref = ast_node('Ref', 'name')
Return = ast_node('Return', 'expression')
Send = ast_node('Send', 'receiver message')
Seq = ast_node('Seq', 'statements')
Trait = ast_node('Trait', 'name meta methods trait_expr')
