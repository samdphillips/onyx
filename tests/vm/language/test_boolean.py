
import pytest
import onyx.objects as o

t = []
def assert_eval(e, v, *_):
    global t
    t.append((e,v))


@pytest.mark.parametrize("expr,value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


assert_eval("1 + 2 + 3 + 4 + 5", 15)
assert_eval("1 < 1", o.false)
assert_eval("1 < 2", o.true)
assert_eval("1 < 3", o.true)
assert_eval("2 < 1", o.false)
assert_eval("2 < 2", o.false)
assert_eval("2 < 3", o.true)
assert_eval("3 < 1", o.false)
assert_eval("3 < 2", o.false)
assert_eval("3 < 3", o.false)
assert_eval("1 > 1", o.false)
assert_eval("1 > 2", o.false)
assert_eval("1 > 3", o.false)
assert_eval("2 > 1", o.true)
assert_eval("2 > 2", o.false)
assert_eval("2 > 3", o.false)
assert_eval("3 > 1", o.true)
assert_eval("3 > 2", o.true)
assert_eval("3 > 3", o.false)
assert_eval("1 <= 1", o.true)
assert_eval("1 <= 2", o.true)
assert_eval("1 <= 3", o.true)
assert_eval("2 <= 1", o.false)
assert_eval("2 <= 2", o.true)
assert_eval("2 <= 3", o.true)
assert_eval("3 <= 1", o.false)
assert_eval("3 <= 2", o.false)
assert_eval("3 <= 3", o.true)
assert_eval("1 >= 1", o.true)
assert_eval("1 >= 2", o.false)
assert_eval("1 >= 3", o.false)
assert_eval("2 >= 1", o.true)
assert_eval("2 >= 2", o.true)
assert_eval("2 >= 3", o.false)
assert_eval("3 >= 1", o.true)
assert_eval("3 >= 2", o.true)
assert_eval("3 >= 3", o.true)
assert_eval("nil isNil", o.true)

assert_eval("true  ifTrue: [ 10 ]", 10)
assert_eval("false ifTrue: [ 10 ]", o.nil)
assert_eval("true  ifTrue: [ 10 ] ifFalse: [ 11 ]", 10)
assert_eval("false ifTrue: [ 10 ] ifFalse: [ 11 ]", 11)

assert_eval("n := 0. [ n < 10 ] whileTrue: [ n := n + 1 ]", o.nil)
assert_eval("n := 0. [ n < 10 ] whileTrue: [ n := n + 1 ]. n", 10)
assert_eval("n := 0. [ n = 10 ] whileFalse: [ n := n + 1 ]. n", 10)
