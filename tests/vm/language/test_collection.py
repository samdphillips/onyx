
import pytest
import onyx.objects as o

t = []


def assert_eval(e, v, *_):
    global t
    t.append((e, v))


@pytest.mark.parametrize("expr, value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


def test_ordered_collections(vm):
    name = object()
    vm.eval_string("c := OrderedCollection new", name)
    assert vm.eval_string("c size", require=[name]) == 0
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

assert_eval("""
c := OrderedCollection new.
1 to: 20 do: [:i | c add: i ].
c asArray""", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
               17, 18, 19, 20])

assert_eval("""
c := OrderedCollection new.
1 to: 20 do: [:i | c addFirst: i ].
c asArray
""", [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
