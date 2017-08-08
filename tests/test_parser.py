
def test_parse_primary_num():
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO('42')
    lex = Lexer(s_inp)
    p = Parser(lex)
    t = p.parse_primary()
    assert t.is_const
    assert t.value == 42


def test_parse_primary_identifier():
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO('id')
    lex = Lexer(s_inp)
    p = Parser(lex)
    t = p.parse_primary()
    assert t.is_ref
    assert t.name == 'id'


def test_parse_primary_const():
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO('true')
    lex = Lexer(s_inp)
    p = Parser(lex)
    t = p.parse_primary()
    assert t.is_const
    assert t.value == True

    s_inp = io.StringIO('false')
    lex = Lexer(s_inp)
    p = Parser(lex)
    t = p.parse_primary()
    assert t.is_const
    assert t.value == False

    s_inp = io.StringIO('nil')
    lex = Lexer(s_inp)
    p = Parser(lex)
    t = p.parse_primary()
    assert t.is_const
    assert t.value == None


def test_parse_unary_send():
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO('10 factorial')
    lex = Lexer(s_inp)
    p = Parser(lex)
    t = p.parse_expr()
    assert t.is_message_send
    assert t.receiver.is_const
    assert t.receiver.value == 10
    assert t.message.selector == 'factorial'
