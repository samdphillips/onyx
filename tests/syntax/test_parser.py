
from contextlib import closing


class CheckSourceInfo:
    def __init__(self, node):
        self.success = []
        self.pending_node = [node]

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.pending_node) == 0:
            raise StopIteration
        node = self.pending_node.pop(0)
        return node.visit(self)

    def add(self, parent_node):
        for attr in parent_node.fields:
            node = getattr(parent_node, attr)
            if hasattr(node, 'visit'):
                self.pending_node.append(node)

    def __getattr__(self, name):
        if name.startswith('visit_'):
            return self.visit
        raise AttributeError(name)

    def visit(self, node):
        self.add(node)
        print(node)
        return node.source_info is not None


def parse_string(s, production, *args):
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO(s)
    lex = Lexer(s, s_inp)
    p = Parser(lex)
    t = getattr(p, 'parse_{}'.format(production))(*args)
    assert all(CheckSourceInfo(t))
    return t


def test_parse_primary_num():
    import onyx.syntax.ast as t
    assert parse_string('42', 'primary') == t.Const(None, 42)


def test_parse_primary_identifier():
    import onyx.syntax.ast as t
    assert parse_string('id', 'primary') == t.Ref(None, 'id')


def test_parse_primary_const_true():
    import onyx.objects as o
    import onyx.syntax.ast as t
    assert parse_string('true', 'primary') == t.Const(None, o.true)


def test_parse_primary_const_false():
    import onyx.objects as o
    import onyx.syntax.ast as t
    assert parse_string('false', 'primary') == t.Const(None, o.false)


def test_parse_primary_const_nil():
    import onyx.objects as o
    import onyx.syntax.ast as t
    assert parse_string('nil', 'primary') == t.Const(None, o.nil)


def test_parse_unary_send():
    import onyx.syntax.ast as t
    assert (parse_string('10 factorial', 'expr') ==
            t.Send(None, t.Const(None, 10), t.Message(None, 'factorial', [])))


def test_parse_unary_primitive_send():
    import onyx.syntax.ast as t
    assert (parse_string('Array _new', 'expr') ==
            t.Send(None,
                   t.Ref(None, 'Array'),
                   t.PrimitiveMessage(None, '_new', [])))


def test_parse_assignment():
    import onyx.syntax.ast as t
    assert (parse_string('life := 42', 'expr') ==
            t.Assign(None, 'life', t.Const(None, 42)))


def test_parse_binary_send():
    import onyx.syntax.ast as t
    assert (parse_string('3 + 4', 'expr') ==
            t.Send(None,
                   t.Const(None, 3),
                   t.Message(None, '+', [t.Const(None, 4)])))


def test_parse_keyword_send():
    import onyx.syntax.ast as t
    assert (parse_string('x at: 10', 'expr') ==
            t.Send(None,
                   t.Ref(None, 'x'),
                   t.Message(None, 'at:', [t.Const(None, 10)])))


def test_parse_primary_block():
    import onyx.objects as o
    import onyx.syntax.ast as t
    assert (parse_string('[ ^ false ]', 'primary') ==
            t.Block(None, [], [],
                    t.Seq(None, [t.Return(None, t.Const(None, o.false))])))


def test_parse_block_char():
    import onyx.objects as o
    import onyx.syntax.ast as t
    assert (parse_string('[ $a ]', 'block') ==
            t.Block(None, [], [],
                    t.Seq(None, [t.Const(None, o.Character(97))])))


def test_parse_module_name():
    import onyx.syntax.ast as t
    assert (parse_string('#{collections.stuff}', 'module_name') ==
            t.ModuleName(None, 'collections.stuff'))


def test_parse_import():
    import onyx.syntax.ast as t
    assert (parse_string('import: #{collections.stuff}', 'import') ==
            t.ModuleImport(None, t.ModuleName(None, 'collections.stuff')))

def test_parse_system():
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    for source in 'collection core exception number stream string'.split():
        with closing(Lexer.from_file('src/ost/boot/{}.ost'.format(source))) as lexer:
            parser = Parser(lexer)
            t = parser.parse_module()
        assert all(CheckSourceInfo(t))


def test_parse_test_system():
    from onyx.syntax.parser import Parser
    for source in 'tester stream toplevel_return'.split():
        t = Parser.parse_file('src/ost/tests/{}.ost'.format(source))
        assert all(CheckSourceInfo(t))
