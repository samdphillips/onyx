
def parse_string(s, production):
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO(s)
    lex = Lexer(s_inp)
    p = Parser(lex)
    return getattr(p, 'parse_{}'.format(production))()


def test_parse_primary_num():
    t = parse_string('42', 'primary')
    assert t.is_const
    assert t.value == 42


def test_parse_primary_identifier():
    t = parse_string('id', 'primary')
    assert t.is_ref
    assert t.name == 'id'


def test_parse_primary_const_true():
    t = parse_string('true', 'primary')
    assert t.is_const
    assert t.value == True


def test_parse_primary_const_false():
    t = parse_string('false', 'primary')
    assert t.is_const
    assert t.value == False


def test_parse_primary_const_nil():
    t = parse_string('nil', 'primary')
    assert t.is_const
    assert t.value == None


def test_parse_unary_send():
    t = parse_string('10 factorial', 'expr')
    assert t.is_message_send
    assert t.receiver.is_const
    assert t.receiver.value == 10
    assert t.message.selector == 'factorial'


def test_parse_unary_primitive_send():
    t = parse_string('Array _new', 'expr')
    assert t.is_message_send
    assert t.receiver.is_ref
    assert t.receiver.name == 'Array'
    assert t.message.is_primitive_message
    assert t.message.selector == '_new'


def test_parse_binary_send():
    t = parse_string('3 + 4', 'expr')
    assert t.is_message_send
    assert t.receiver.is_const
    assert t.receiver.value == 3
    assert t.message.selector == '+'
    assert t.message.args[0].is_const
    assert t.message.args[0].value == 4
