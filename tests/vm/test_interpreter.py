
def test_system_smoketest():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    assert vm.eval_string('3 + 4') == 7
