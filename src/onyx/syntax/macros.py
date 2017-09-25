
import attr

import onyx.objects as o
import onyx.syntax.ast as t


@attr.s
class InstanceOfPattern:
    cls = attr.ib()

    def match(self, v):
        return isinstance(v, self.cls)


@attr.s
class SymbolPattern:
    selector = attr.ib()

    def match(self, v):
        return self.selector == v

class AnyPattern:
    def match(self, v):
        return True


@attr.s
class SendMessagePattern:
    receiver_pattern = attr.ib(default=attr.Factory(AnyPattern))
    message = attr.ib(default=attr.Factory(AnyPattern))
    argument_patterns = attr.ib(default=attr.Factory(list))

    def receiver_instanceof(self, cls):
        self.receiver_pattern = InstanceOfPattern(cls)

    def message_name(self, selector):
        self.message = SymbolPattern(selector)

    def arg_instanceof(self, cls):
        self.argument_patterns.append(InstanceOfPattern(cls))

    def conditions(self, node):
        yield isinstance(node, t.Send)
        yield isinstance(node.message, t.Message)
        yield self.message.match(node.message.selector)
        self.receiver_pattern.match(node.receiver)
        for a, n in zip(self.argument_patterns, node.message.args):
            yield a.match(n)

    def match(self, node):
        return all(self.conditions(node))


class Expander:
    macros = []

    @classmethod
    def add_macro(cls, m):
        cls.macros.append(m)

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
class Macro:
    pattern = attr.ib()
    expander = attr.ib()

    def expand(self, node):
        if self.pattern.match(node):
            return self.expander(node)
        return None


def pattern(builder):
    p = SendMessagePattern()
    builder(p)
    return p


def macro(pattern):
    def _inner(expander):
        m = Macro(pattern, expander)
        Expander.add_macro(m)
        return m
    return _inner


@pattern
def while_true_pat(p):
    p.receiver_instanceof(t.Block)
    p.message_name(o.get_symbol('whileTrue:'))
    p.arg_instanceof(t.Block)


@macro(while_true_pat)
def while_true(node):
    temps = node.receiver.temps + node.message.args[0].temps
    return t.WhileTrue(node.source_info,
                       temps,
                       node.receiver.statements,
                       node.message.args[0].statements)
