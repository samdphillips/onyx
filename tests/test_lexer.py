
def lex_string1(s):
    import io
    from onyx.syntax.lexer import Lexer
    s_inp = io.StringIO(s)
    lex = Lexer(s_inp)
    token = lex.lex_token()
    assert lex.buffer_at_end()
    return token


def _test_lex1(s, type, value=None):
    def _testit():
        tok = lex_string1(s)
        assert tok.type == type
        if value is not None:
            assert tok.value == value
    return _testit

test_lex_whitespace = _test_lex1('    \t\n', 'whitespace')
test_lex_identifier = _test_lex1('id', 'id', 'id')
test_lex_keyword = _test_lex1('if:', 'kw', 'if:')
