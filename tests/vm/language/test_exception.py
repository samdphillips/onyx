
import pytest
import onyx.objects as o

t = []
def assert_eval(e, v, *_):
    global t
    t.append((e,v))


@pytest.mark.parametrize("expr,value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


assert_eval('[ 42 ] on: Exception do: [:exc | 43 ]', 42)
assert_eval('[ Exception signal. 42 ] on: Exception do: [:exc | 43 ]', 43)

assert_eval(
"""
Object subclass: ExcPass [
    start [
        [ self next ]
            on: Exception
            do: [:exc | 42 ]
    ]

    next [
        [ Exception signal. 40 ]
            on: Exception
            do: [:exc | exc pass. 41 ]
    ]
]

ExcPass new start
""", 42)

assert_eval(
"""
Object subclass: TestResume [
    start [
        [ self foo + 40 ] on: Exception do: [:e | e resume: 2 ]
    ]

    foo [
        Exception signal
    ]
]

TestResume new start
""", 42)

assert_eval(
"""
Object subclass: TestMNU [
    start [
        [ self foo ]
            on: MessageNotUnderstood
            do: [:exc | true ]
    ]

    doesNotUnderstand: aMessage [
        super doesNotUnderstand: aMessage
    ]
]

TestMNU new start
""", o.true)

assert_eval(
"""
Object subclass: Foo [
    | record |

    record [
        record asArray
    ]

    start [
        record := OrderedCollection new.

        [ self a ]
            on: Exception
            do: [ :e | record add: e isNested ].
        self
    ]

    a [
        [ self b ]
            on: Exception
            do: [ :e | record add: e isNested.
                       e pass ]
    ]

    b [
        Exception signal
    ]
]

Foo new start record
""", [o.true, o.false])

assert_eval(
"""
CheckedValue := 41.

Object subclass: TestCurtailed [
    foo [
        [ self bar ]
            ifCurtailed: [ CheckedValue := 42 ]
    ]

    bar [
        Exception signal
    ]
]

[ TestCurtailed new foo ]
    on: Exception
    do: [:ex | nil ].
CheckedValue
""", 42)

assert_eval(
"""
CheckedValue := 41.

Object subclass: TestCurtailed [
    foo [
        [ self bar ] ifCurtailed: [ CheckedValue := CheckedValue + 1 ]
    ]

    bar [
        [ Exception signal ] ifCurtailed: [ CheckedValue := CheckedValue + 1 ]
    ]
]

[ TestCurtailed new foo ] on: Exception do: [:ex | nil ].
CheckedValue
""", 43)
