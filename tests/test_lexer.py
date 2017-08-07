
def lex_string1(s):
    import io
    from onyx.syntax.lexer import Lexer
    s_inp = io.StringIO(s)
    lex = Lexer(s_inp)
    return lex.lex_token()

def test_lex_whitespace():
    s = "      "
    tok = lex_string1(s)
    assert tok.type == 'whitespace'

def test_lex_identifier():
    s = "id"
    tok = lex_string1(s)
    assert tok.type == 'id'
    assert tok.value == 'id'

def test_lex_keyword():
    s = "ifTrue:"
    tok = lex_string1(s)
    assert tok.type == 'kw'
    assert tok.value == 'ifTrue:'
