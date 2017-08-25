
import pytest

@pytest.fixture
def vm():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    return vm
