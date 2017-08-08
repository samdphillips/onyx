
def raw_lex_string1(s):
    import io
    from onyx.syntax.lexer import Lexer
    s_inp = io.StringIO(s)
    lex = Lexer(s_inp)
    token = lex.raw_lex_token()
    assert lex.buffer_at_end()
    return token


def _test_raw_lex1(s, type, value=None):
    def _testit():
        tok = raw_lex_string1(s)
        assert tok.type == type
        if value is not None:
            assert tok.value == value
    return _testit

test_lex_whitespace = _test_raw_lex1('    \t\n', 'whitespace')
test_lex_identifier = _test_raw_lex1('id', 'id', 'id')
test_lex_identifier_prim = _test_raw_lex1('_new', 'id', '_new')
test_lex_keyword = _test_raw_lex1('if:', 'kw', 'if:')
test_lex_keyword_prim = _test_raw_lex1('_new:', 'kw', '_new:')
test_lex_binsel = _test_raw_lex1('+', 'binsel', '+')
test_lex_int = _test_raw_lex1('1234', 'int', 1234)
test_lex_negative = _test_raw_lex1('-1', 'int', -1)
test_lex_binsel_sub = _test_raw_lex1('-', 'binsel', '-')
test_lex_character = _test_raw_lex1('$a', 'character', ord('a'))
test_lex_caret = _test_raw_lex1('^', 'caret')
test_lex_comment = _test_raw_lex1('"comment"', 'comment', 'comment')
test_lex_blockarg = _test_raw_lex1(':a', 'blockarg', 'a')
test_lex_semi = _test_raw_lex1(';', 'semi', ';')
test_lex_lpar = _test_raw_lex1('(', 'lpar')
test_lex_rpar = _test_raw_lex1(')', 'rpar')
test_lex_lparray = _test_raw_lex1('#(', 'lparray')
test_lex_assign = _test_raw_lex1(':=', 'assign')
test_lex_lcurl = _test_raw_lex1('{', 'lcurl')
test_lex_rcurl = _test_raw_lex1('}', 'rcurl')
test_lex_lsq = _test_raw_lex1('[', 'lsq')
test_lex_rsq = _test_raw_lex1(']', 'rsq')
test_lex_dot = _test_raw_lex1('.', 'dot')

# symbols
test_lex_unary_symbol = _test_raw_lex1('#aUnarySymbol', 'symbol', 'aUnarySymbol')
test_lex_binary_symbol = _test_raw_lex1('#+', 'symbol', '+')
test_lex_keyword_symbol = _test_raw_lex1(
    '#aKeyword:symbol:', 'symbol', 'aKeyword:symbol:')
test_lex_space_symbol = _test_raw_lex1(
    "#'another symbol'", 'symbol', 'another symbol')

test_lex_string = _test_raw_lex1("'test string'", 'string', 'test string')
test_lex_quoted_string = _test_raw_lex1(
    "'test ''string'''", 'string', "test 'string'")

test_lex_eof = _test_raw_lex1('', 'eof')
