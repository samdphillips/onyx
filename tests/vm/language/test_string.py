
import pytest
import onyx.objects as o

t = []
def assert_eval(e, v):
    global t
    t.append((e,v))


@pytest.mark.parametrize("expr,value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


assert_eval("'abc', '123'", "abc123")
assert_eval("('abc' at: 0) codePoint", 97)
assert_eval("foo := 'abc'. (foo at: 0) == (foo at: 0)", o.true)
assert_eval('$a ~= 97', o.true)
assert_eval("#test ~= 'test'", o.true)

assert_eval("a := Character codePoint: 97. b := Character codePoint: 97. a == b", o.true)
assert_eval("$a == (Character codePoint: 97)", o.true)
assert_eval("('a' at: 0) == (Character codePoint: 97)", o.true)
assert_eval("(#($a) at: 0) == (Character codePoint: 97)", o.true)
assert_eval("$a == $b", o.false)
assert_eval("$  codePoint", o.SmallInt(32))
assert_eval("$a asLowercase == $a", o.true)
assert_eval("$A asLowercase == $a", o.true)
assert_eval("$  asLowercase == $ ", o.true)
assert_eval("$A asString", o.String('A'))
