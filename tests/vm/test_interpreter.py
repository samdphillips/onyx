
import pytest
import onyx.objects as o


@pytest.fixture
def vm():
    from onyx.vm.interpreter import Interpreter
    return Interpreter()


def test_system_smoketest(vm):
    assert vm.eval_string('3 + 4') == 7


@pytest.mark.skip('no such thing as Object anymore')
def test_object_equivalence(vm):
    assert vm.eval_string('Object new = Object new') is False


@pytest.mark.skip('no such thing as structural inheritance anymore')
def test_module_subclass_vars_in_scope(vm):
    vm.eval_string("""
Object subclass: A [
    | foo |
]

A subclass: B [
    foo [ foo ]
]
""")
