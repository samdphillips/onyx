
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
    p = m.SendPattern()
    p.receiver_instanceof(t.Block)
    p.message_name(o.get_symbol('whileTrue:'))
    p.arg_instanceof(t.Block)
    return p


def test_match_wt_pat(wt_node, wt_pat):
    assert wt_pat.match(wt_node)


def test_fail_match_wt_pat(ift_node, wt_pat):
    assert not wt_pat.match(wt_node)


def test_expand_wt(wt_node):
    import onyx.objects as o
    import onyx.syntax.ast as t
    import onyx.syntax.macros as m
    new_node = m.while_true.expand(wt_node)
    print(new_node)
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
