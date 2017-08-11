
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
    assert parse_string('42', 'primary') == t.Const(42)


def test_parse_primary_identifier():
    import onyx.syntax.ast as t
    assert parse_string('id', 'primary') == t.Ref('id')


def test_parse_primary_const_true():
    import onyx.syntax.ast as t
    assert parse_string('true', 'primary') == t.Const(True)


def test_parse_primary_const_false():
    import onyx.syntax.ast as t
    assert parse_string('false', 'primary') == t.Const(False)


def test_parse_primary_const_nil():
    import onyx.syntax.ast as t
    assert parse_string('nil', 'primary') == t.Const(None)


def test_parse_unary_send():
    import onyx.syntax.ast as t
    assert (parse_string('10 factorial', 'expr') ==
            t.Send(t.Const(10), t.Message('factorial', [])))


def test_parse_unary_primitive_send():
    import onyx.syntax.ast as t
    assert (parse_string('Array _new', 'expr') ==
            t.Send(t.Ref('Array'), t.PrimitiveMessage('_new', [])))


def test_parse_assignment():
    import onyx.syntax.ast as t
    assert (parse_string('life := 42', 'expr') ==
            t.Assign('life', t.Const(42)))


def test_parse_binary_send():
    import onyx.syntax.ast as t
    assert (parse_string('3 + 4', 'expr') ==
            t.Send(t.Const(3), t.Message('+', [t.Const(4)])))


def test_parse_keyword_send():
    import onyx.syntax.ast as t
    assert (parse_string('x at: 10', 'expr') ==
            t.Send(t.Ref('x'), t.Message('at:', [t.Const(10)])))


def test_parse_primary_block():
    import onyx.syntax.ast as t
    assert (parse_string('[ ^ false ]', 'primary') ==
            t.Block([], [], t.Seq([t.Return(t.Const(value=False))])))


def test_parse_system():
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    with open('src/ost/boot/core.ost', 'r') as f:
        lexer = Lexer(f)
        parser = Parser(lexer)
        parser.parse_module()
