
import pytest
import onyx.objects as o

t = []
def assert_eval(e, v, *_):
    global t
    t.append((e,v))


@pytest.mark.parametrize("expr,value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


def test_ordered_collections(vm):
    name = object()
    vm.eval_string("c := OrderedCollection new", name)
    assert vm.eval_string("c size", require=[name]) ==  0
    assert vm.eval_string("c asArray", require=[name]) == []

    vm.eval_string("c add: 0", require=[name])
    assert vm.eval_string("c size", require=[name]) == 1
    assert vm.eval_string("c asArray", require=[name]) == [0]

    vm.eval_string("c add: 1", require=[name])
    assert vm.eval_string("c size", require=[name]) == 2
    assert vm.eval_string("c asArray", require=[name]) == [0, 1]

    vm.eval_string("c addFirst: 2", require=[name])
    assert vm.eval_string("c size", require=[name]) == 3
    assert vm.eval_string("c asArray", require=[name]) == [2, 0, 1]


assert_eval("(Array new: 10) size", 10)
assert_eval("Array new size", 0)
assert_eval("a := Array new: 1. a at: 0 put: 10. a at: 0", 10)
assert_eval("a := Array with: 10. a at: 0", 10)
