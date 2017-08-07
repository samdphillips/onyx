
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
