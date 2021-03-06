
from operator import methodcaller

import onyx.objects as o


def lex_string(s, lex_func):
    import io
    from onyx.syntax.lexer import Lexer
    s_inp = io.StringIO(s)
    lex = Lexer(s, s_inp)
    while True:
        token = lex_func(lex)
        yield token
        if token.type == 'eof':
            return


def _test_raw_lex1(s, type, value=None):
    def _testit():
        tokens = lex_string(s, methodcaller('raw_lex_token'))
        token = tokens.__next__()
        assert token.type == type
        if value is not None:
            assert token.value == value
        assert tokens.__next__().type == 'eof'
    return _testit

test_lex_whitespace = _test_raw_lex1('    \t\n', 'whitespace')
test_lex_identifier = _test_raw_lex1('id', 'id', 'id')
test_lex_identifier_prim = _test_raw_lex1('_new', 'id', '_new')
test_lex_keyword = _test_raw_lex1('if:', 'kw', 'if:')
test_lex_keyword_prim = _test_raw_lex1('_new:', 'kw', '_new:')
test_lex_binsel = _test_raw_lex1('+', 'binsel', '+')
test_lex_int = _test_raw_lex1('1234', 'int', 1234)
test_lex_int_delim = _test_raw_lex1('1_234_567', 'int', 1234567)
test_lex_int_b16 = _test_raw_lex1('16rFF', 'int', 255)
test_lex_int_b2 = _test_raw_lex1('2r100', 'int', 4)
test_lex_int_b2_delim = _test_raw_lex1('2r1000_0100', 'int', 0x84)
test_lex_int_b8 = _test_raw_lex1('8r400', 'int', 256)
test_lex_negative = _test_raw_lex1('-1', 'int', -1)
test_lex_binsel_sub = _test_raw_lex1('-', 'binsel', '-')
test_lex_character = _test_raw_lex1('$a', 'character',
                                    o.get_character(ord('a')))
test_lex_caret = _test_raw_lex1('^', 'caret')
test_lex_comment = _test_raw_lex1('"comment"', 'comment', 'comment')
test_lex_comment_long = _test_raw_lex1('"' + 'Aa' * 2500 + '"', 'comment')
test_lex_blockarg = _test_raw_lex1(':a', 'blockarg', 'a')
test_lex_semi = _test_raw_lex1(';', 'semi', ';')
test_lex_lpar = _test_raw_lex1('(', 'lpar')
test_lex_rpar = _test_raw_lex1(')', 'rpar')
test_lex_lparray = _test_raw_lex1('#(', 'lparray')
test_lex_lpmod = _test_raw_lex1('#{', 'lpmod')
test_lex_assign = _test_raw_lex1(':=', 'assign')
test_lex_lcurl = _test_raw_lex1('{', 'lcurl')
test_lex_rcurl = _test_raw_lex1('}', 'rcurl')
test_lex_lsq = _test_raw_lex1('[', 'lsq')
test_lex_rsq = _test_raw_lex1(']', 'rsq')
test_lex_dot = _test_raw_lex1('.', 'dot')

# symbols
test_lex_unary_symbol = _test_raw_lex1(
    '#aUnarySymbol', 'symbol', 'aUnarySymbol')
test_lex_binary_symbol = _test_raw_lex1('#+', 'symbol', '+')
test_lex_keyword_symbol = _test_raw_lex1(
    '#aKeyword:symbol:', 'symbol', 'aKeyword:symbol:')
test_lex_space_symbol = _test_raw_lex1(
    "#'another symbol'", 'symbol', 'another symbol')

test_lex_string = _test_raw_lex1("'test string'", 'string', 'test string')
test_lex_quoted_string = _test_raw_lex1(
    "'test ''string'''", 'string', "test 'string'")


def test_lex_eof():
    token = lex_string('', methodcaller('raw_lex_token'))
    assert token.__next__().type == 'eof'


def test_lex_skip_tokens():
    token = lex_string('    "should not see this"    ',
                       methodcaller('lex_token'))
    assert token.__next__().type == 'eof'
