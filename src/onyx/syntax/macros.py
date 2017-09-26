
import attr

import onyx.objects as o
import onyx.syntax.ast as t


class Expander:
    macros = []

    @classmethod
    def add_macro(cls, pattern):
        def _inner(expand):
            m = Macro(pattern, expand)
            cls.macros.append(m)
            return m
        return _inner

    def expand_node(self, node):
        expand_again = True
        while expand_again:
            expand_again = False
            for m in self.macros:
                new = m.expand(node)
                if new:
                    node = new
                    expand_again = True
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


@pattern
def while_true_pat(node):
    yield isinstance(node, t.Send)
    yield isinstance(node.message, t.Message)
    yield node.message.selector == o.get_symbol('whileTrue:')
    yield isinstance(node.receiver, t.Block)
    yield isinstance(node.message.args[0], t.Block)


@Expander.add_macro(while_true_pat)
def while_true(node):
    temps = node.receiver.temps + node.message.args[0].temps
    return t.WhileTrue(node.source_info,
                       temps,
                       node.receiver.statements,
                       node.message.args[0].statements)
