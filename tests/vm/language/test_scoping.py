
import pytest
import onyx.objects as o

t = []


def assert_eval(e, v, *_):
    global t
    t.append((e, v))


@pytest.mark.parametrize("expr, value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


assert_eval("""
a := 19.
nil subclass: Foo [
    | a |
    bar [ a := 42 ]
]
Foo new bar.
a
""", 19, 'scope_1')

assert_eval("""
nil subclass: Foo [
    bar [| a | a := 19 ]
]
a := 42.
Foo new bar.
a
""", 42, 'scope_2')

assert_eval("""
a := 42.
[| a | a := 19 ] value.
a
""", 42, 'scope_3')

assert_eval("""
[| x | x ] value
""", None, 'init vars nil')
