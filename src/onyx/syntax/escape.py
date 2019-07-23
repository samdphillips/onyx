
import attr

import onyx.syntax.ast as t

from onyx.syntax.macros import gensym, _sym


def traverse():
    def __inner(self, node, *args):
        return node.visit_children_static(self.visit, *args)
    return __inner


class EscapeCompile:
    def compile(self, module):
        return module.visit_static(self.visit)

    def visit(self, node):
        return node.visit(self)

    def visit_method(self, method):
        return MethodCompile().compile(method)

    def visit_return(self, block):
        raise Exception(block)

    visit_assign = traverse()
    visit_block = traverse()
    visit_cascade = traverse()
    visit_class = traverse()
    visit_const = traverse()
    visit_message = traverse()
    visit_meta = traverse()
    visit_module = traverse()
    visit_module_import = traverse()
    visit_primitive_message = traverse()
    visit_ref = traverse()
    visit_send = traverse()
    visit_seq = traverse()
    visit_trait = traverse()


@attr.s
class MethodCompile:
    uses_return = attr.ib(init=False, default=False)
    escape_name = attr.ib(init=False, default=None)

    def visit(self, node):
        return node.visit(self)

    def compile(self, method):
        body = method.statements
        body = body.visit_static(self.visit)
        if self.uses_return:
            body = self.rewrite_method_body(body)
            return method._replace(statements=body)
        return method

    def rewrite_method_body(self, body):
        si = body.source_info
        block = t.Block(si, [self.escape_name], [], body)
        msg = t.Message(si, _sym('withFullEscape'), [])
        return t.Send(si, block, msg)

    def visit_return(self, ret):
        si = ret.source_info
        self.uses_return = True
        self.escape_name = self.escape_name or gensym('escape')
        e = self.visit(ret.expression)
        m = t.Message(si, _sym('value:'), [e])
        r = t.Ref(si, self.escape_name)
        return t.Send(si, r, m)

    visit_assign = traverse()
    visit_block = traverse()
    visit_cascade = traverse()
    visit_const = traverse()
    visit_message = traverse()
    visit_primitive_message = traverse()
    visit_ref = traverse()
    visit_send = traverse()
    visit_seq = traverse()
