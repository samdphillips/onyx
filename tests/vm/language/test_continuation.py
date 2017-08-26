
import pytest
import onyx.objects as o

t = []
def assert_eval(e, v, *_):
    global t
    t.append((e,v))


@pytest.mark.parametrize("expr,value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


assert_eval("p := PromptTag new. [ 2 + 5 ] withPrompt: p", 7)

assert_eval(
"""
[:p | 2 + ([:k | 5 ] withContinuation: p) ] withPrompt
""", 7)

assert_eval(
"""
[:p | 2 + ([:k | k value: 5 ] withContinuation: p) ] withPrompt
""", 9)

assert_eval(
"""
[:p | 2 + (p abort: 0) + 5 ] withPrompt
""", 0)

assert_eval(
"""
[:p | 2 + ([ 3 + ([:k | k value: 2 ] withContinuation: p) ] withPrompt: p) ] withPrompt
""", 10)

assert_eval(
"""
p := PromptTag new.
[ 2 + ([:k | p abort: k ] withContinuation: p) ]
    withPrompt: p
    abort: [:x | x value: 3 ]
""", 5)

assert_eval(
"""
a := PromptTag new.
b := PromptTag new.
[
    [ a abort: #foo ] withPrompt: b abort: [:x | 41 ]
] withPrompt: a abort: [:x | 42 ]
""", 42)
