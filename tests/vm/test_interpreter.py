
import onyx.objects as o

counter = 0
def _test_evaluation(expression, value):
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

_test_evaluation("1 + 2 + 3 + 4 + 5", 15)
_test_evaluation("1 < 1", o.false)
_test_evaluation("1 < 2", o.true)
_test_evaluation("1 < 3", o.true)
_test_evaluation("2 < 1", o.false)
_test_evaluation("2 < 2", o.false)
_test_evaluation("2 < 3", o.true)
_test_evaluation("3 < 1", o.false)
_test_evaluation("3 < 2", o.false)
_test_evaluation("3 < 3", o.false)
_test_evaluation("1 > 1", o.false)
_test_evaluation("1 > 2", o.false)
_test_evaluation("1 > 3", o.false)
_test_evaluation("2 > 1", o.true)
_test_evaluation("2 > 2", o.false)
_test_evaluation("2 > 3", o.false)
_test_evaluation("3 > 1", o.true)
_test_evaluation("3 > 2", o.true)
_test_evaluation("3 > 3", o.false)
_test_evaluation("1 <= 1", o.true)
_test_evaluation("1 <= 2", o.true)
_test_evaluation("1 <= 3", o.true)
_test_evaluation("2 <= 1", o.false)
_test_evaluation("2 <= 2", o.true)
_test_evaluation("2 <= 3", o.true)
_test_evaluation("3 <= 1", o.false)
_test_evaluation("3 <= 2", o.false)
_test_evaluation("3 <= 3", o.true)
_test_evaluation("1 >= 1", o.true)
_test_evaluation("1 >= 2", o.false)
_test_evaluation("1 >= 3", o.false)
_test_evaluation("2 >= 1", o.true)
_test_evaluation("2 >= 2", o.true)
_test_evaluation("2 >= 3", o.false)
_test_evaluation("3 >= 1", o.true)
_test_evaluation("3 >= 2", o.true)
_test_evaluation("3 >= 3", o.true)
_test_evaluation("nil isNil", o.true)


_test_evaluation("true  ifTrue: [ 10 ]", 10)
_test_evaluation("false ifTrue: [ 10 ]", o.nil)
_test_evaluation("true  ifTrue: [ 10 ] ifFalse: [ 11 ]", 10)
_test_evaluation("false ifTrue: [ 10 ] ifFalse: [ 11 ]", 11)
