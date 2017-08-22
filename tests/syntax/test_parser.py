
def parse_string(s, production, *args):
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO(s)
    lex = Lexer(s_inp)
    p = Parser(lex)
    return getattr(p, 'parse_{}'.format(production))(*args)


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


def test_parse_system():
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    for source in 'collection core exception number stream string'.split():
        with open('src/ost/boot/{}.ost'.format(source), 'r') as f:
            lexer = Lexer(f)
            parser = Parser(lexer)
            parser.parse_module()


def test_parse_test_system():
    from onyx.syntax.parser import Parser
    for source in 'tester ordered_collection stream toplevel_return'.split():
        with open('src/ost/tests/{}.ost'.format(source), 'r') as f:
            parser = Parser.parse_file(f)
