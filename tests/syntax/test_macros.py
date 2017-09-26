
import pytest


def parse_expr(s):
    import io
    from onyx.syntax.lexer import Lexer
    from onyx.syntax.parser import Parser
    s_inp = io.StringIO(s)
    lex = Lexer(s, s_inp)
    p = Parser(lex)
    return p.parse_expr()


@pytest.fixture
def wt_node():
    return parse_expr('[ t < 100 ] whileTrue: [ t := t + 1 ]')


@pytest.fixture
def ift_node():
    return parse_expr('testValue ifTrue: [ 42 ]')


@pytest.fixture
def wt_pat():
    import onyx.objects as o
    import onyx.syntax.ast as t
    import onyx.syntax.macros as m
    @m.pattern
    def _pattern(n):
        yield isinstance(n, t.Send)
        yield isinstance(n.message, t.Message)
        yield isinstance(n.receiver, t.Block)
        yield n.message.selector == o.get_symbol('whileTrue:')
        yield isinstance(n.message.args[0], t.Block)
    return _pattern


def test_match_wt_pat(wt_node, wt_pat):
    assert wt_pat.match(wt_node)


def test_fail_match_wt_pat(ift_node, wt_pat):
    assert not wt_pat.match(wt_node)


def test_expand_wt(wt_node):
    import onyx.objects as o
    import onyx.syntax.ast as t
    import onyx.syntax.macros as m
    new_node = m.while_true.expand(wt_node)
    assert (new_node ==
        t.WhileTrue(None, [],
                    t.Seq(None,
                          [t.Send(None, t.Ref(None, o.get_symbol('t')),
                                        t.Message(None,
                                                  o.get_symbol('<'),
                                                  [t.Const(None, 100)]))]),
                    t.Seq(None,
                          [t.Assign(None,
                                    o.get_symbol('t'),
                                    t.Send(None, t.Ref(None, o.get_symbol('t')),
                                                 t.Message(None,
                                                           o.get_symbol('+'),
                                                           [t.Const(None, 1)])))])))
