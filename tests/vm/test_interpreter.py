
import onyx.objects as o

counter = 0
def assert_eval(expression, value, name=None):
    global counter
    def _test_fun():
        from onyx.vm.interpreter import Interpreter
        vm = Interpreter.boot()
        assert vm.eval_string(expression) == value
    if name is None:
        name = 'test_evaluate_{:03d}'.format(counter)
    else:
        name = 'test_evaluate_{}'.format(name)
    _test_fun.__name__ = name
    globals()[name] = _test_fun
    counter += 1

def test_system_smoketest():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    assert vm.eval_string('3 + 4') == 7

def test_ordered_collections():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    vm.eval_string("c := OrderedCollection new")
    assert vm.eval_string("c size") ==  0
    assert vm.eval_string("c asArray") == []

    vm.eval_string("c add: 0")
    assert vm.eval_string("c size") == 1
    assert vm.eval_string("c asArray") == [0]

    vm.eval_string("c add: 1")
    assert vm.eval_string("c size") == 2
    assert vm.eval_string("c asArray") == [0, 1]

    vm.eval_string("c addFirst: 2")
    assert vm.eval_string("c size") == 3
    assert vm.eval_string("c asArray") == [2, 0, 1]


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

assert_eval("""
a := 19.
Object subclass: Foo [
    | a |
    bar [ a := 42 ]
]
Foo new bar.
a
""", 19, 'scope_1')

assert_eval("""
Object subclass: Foo [
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
