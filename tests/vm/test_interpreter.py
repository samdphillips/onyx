
import onyx.objects as o

counter = 0
def assert_eval(expression, value):
    global counter
    def _test_fun():
        from onyx.vm.interpreter import Interpreter
        vm = Interpreter.boot()
        assert vm.eval_string(expression) == value
    name = 'test_evaluate_{:03d}'.format(counter)
    _test_fun.__name__ = name
    globals()[name] = _test_fun
    counter += 1

def test_system_smoketest():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    assert vm.eval_string('3 + 4') == 7

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

assert_eval("(Array new: 10) size", 10)
assert_eval("Array new size", 0)
assert_eval("a := Array new: 1. a at: 0 put: 10. a at: 0", 10)
assert_eval("a := Array with: 10. a at: 0", 10)

assert_eval("'abc', '123'", "abc123")
assert_eval("('abc' at: 0) codePoint", 97)
assert_eval("foo := 'abc'. (foo at: 0) == (foo at: 0)", o.true)
assert_eval('$a ~= 97', o.true)
assert_eval("#test ~= 'test'", o.true)
