
import attr

import onyx.objects as o
import onyx.syntax.ast as t


_sym = o.get_symbol

counter = 0
def gensym(name):
    global counter
    counter += 1
    return _sym('%s%05d' % (name, counter))

class Expander:
    macros = []
    message_macros = {}

    @classmethod
    def add_macro(cls, key=None):
        def _make_macro(macro_cls):
            m = macro_cls()
            if key:
                symbol = _sym(key)
                ms = cls.message_macros.get(symbol, [])
                ms.append(m)
                cls.message_macros[symbol] = ms
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
                for m in self.message_macros.get(node.message.selector, []):
                    node, expand_again = m(node)
                if expand_again:
                    continue
            for m in self.macros:
                node, expand_again = m(node)
        return node

    def expand(self, node):
        return node.visit_static(self.visit_node)

    def visit_node(self, node):
        return self.expand_node(node).visit_children_static(self.visit_node)


@attr.s
class Macro:
    def match(self, node):
        return all(self.match_conditions(node))

    def expand(self, node):
        if self.match(node):
            return self.expand_node(node)
        return None

    def __call__(self, node):
        new = self.expand(node)
        return new or node, new is not None


@Expander.add_macro(key='whileTrue:')
class WhileTrue(Macro):
    def match_conditions(self, node):
        yield isinstance(node.receiver, t.Block)

    def expand_node(self, node):
        si = node.source_info
        a = node.receiver
        b = node.message.args[0]
        exit = gensym('exit')
        a = t.Send(a.source_info, a,
                   t.Message(a.source_info, _sym('value'), []))
        c = t.Send(si, t.Ref(si, exit),
                   t.Message(si, _sym('value:'), [t.Const(si, None)]))
        c = t.Block(si, [], [], c)
        bl = t.Send(si, a, t.Message(si, _sym('ifTrue:ifFalse:'), [b, c]))
        bl = t.Block(si, [], [], bl)
        bl = t.Send(si, bl, t.Message(si, _sym('repeat'), []))
        bl = t.Block(si, [exit], [], bl)
        bl = t.Send(si, bl, t.Message(si, _sym('withEscape'), []))
        return bl


@Expander.add_macro(key='ifTrue:ifFalse:')
class IfTrueIfFalseCond(Macro):
    def match_conditions(self, node):
        yield True

    def send_value(self, node):
        m = t.Message(node.source_info, _sym('value'), [])
        return t.Send(node.source_info, node, m)

    def expand_node(self, node):
        test = node.receiver
        ift = self.send_value(node.message.args[0])
        iff = self.send_value(node.message.args[1])
        return t.Cond(node.source_info, test, ift, iff)


@Expander.add_macro(key='repeat')
class Repeat(Macro):
    def match_conditions(self, node):
        yield isinstance(node.receiver, t.Block)

    def expand_node(self, node):
        si = node.source_info
        block = node.receiver
        body = t.Send(block.source_info, block,
                      t.Message(si, _sym('value'), []))
        return t.Repeat(si, body)


@Expander.add_macro(key='value')
class Value(Macro):
    def match_conditions(self, node):
        yield isinstance(node.receiver, t.Block)

    def expand_node(self, node):
        si = node.source_info
        body = node.receiver.statements
        if len(node.receiver.temps) > 0:
            body = t.Scope(si, node.receiver.temps, body)
        return body


@Expander.add_macro()
class Seq1(Macro):
    def match_conditions(self, node):
        yield isinstance(node, t.Seq)
        yield len(node.statements) == 1

    def expand_node(self, node):
        return node.statements[0]
