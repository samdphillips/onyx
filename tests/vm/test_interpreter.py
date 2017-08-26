
import onyx.objects as o

def test_system_smoketest():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    assert vm.eval_string('3 + 4') == 7

def test_object_equivalence():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    assert vm.eval_string('Object new = Object new') == o.false
