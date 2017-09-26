
import attr

import onyx.objects as o
import onyx.syntax.ast as t


class Expander:
    macros = []
    message_macros = {}

    @classmethod
    def add_macro(cls, pattern, key=None):
        def _make_macro(expand):
            m = Macro(pattern, expand)
            if key:
                symbol = o.get_symbol(key)
                cls.message_macros[symbol] = m
            else:
                cls.macros.append(m)
            return m
        return _make_macro

    def is_send_message(self, node):
        return isinstance(node, t.Send) and isinstance(node.message, t.Message)

    def expand_node(self, node):
        expand_again = True
        while expand_again:
            expand_again = False
            if self.is_send_message(node):
                m = self.message_macros.get(node.message.selector,
                                            lambda n: (n, False))
                node, expand_again = m(node)
            for m in self.macros:
                node, expand_again = m(node)
        return node

    def expand(self, node):
        return node.visit_static(self.visit_node)

    def visit_node(self, node):
        return self.expand_node(node).visit_children_static(self.visit_node)


@attr.s
class Pattern:
    match_func = attr.ib()

    def match(self, node):
        return all(self.match_func(node))

pattern = Pattern


@attr.s
class Macro:
    pattern = attr.ib()
    expander = attr.ib()

    def expand(self, node):
        if self.pattern.match(node):
            return self.expander(node)
        return None

    def __call__(self, node):
        new = self.expand(node)
        return new or node, new is not None


@pattern
def while_true_pat(node):
    yield isinstance(node.receiver, t.Block)
    yield isinstance(node.message.args[0], t.Block)


@Expander.add_macro(while_true_pat, key='whileTrue:')
def while_true(node):
    temps = node.receiver.temps + node.message.args[0].temps
    return t.WhileTrue(node.source_info,
                       temps,
                       node.receiver.statements,
                       node.message.args[0].statements)
