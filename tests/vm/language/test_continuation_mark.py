
import pytest
import onyx.objects as o

t = []
def assert_eval(e, v, *_):
    global t
    t.append((e,v))


@pytest.mark.parametrize("expr,value", t)
def test_evaluation(vm, expr, value):
    assert vm.eval_string(expr) == value


assert_eval("[ 3 + 4 ] withMark: #foo value: #bar", 7)
assert_eval(
"""
cmark := ContinuationMark new.
[:p | [ 3 + (cmark firstMark: p) ]
  withMark: cmark
  value: 4 ] withPrompt
""", 7)


assert_eval(
"""
cmark := ContinuationMark new.
[:p | [ [:p1 | 3 + (cmark firstMark: p) ] withPrompt ]
  withMark: cmark
  value: 4 ] withPrompt
""", 7)


assert_eval(
"""
m := ContinuationMark new.
[:p | foo := p.
    [
        [
            [ p abort: (m marks: p) ] withMark: m value: 1.
            #foo
        ] withMark: m value: 2.
        #foo
    ] withMark: m value: 3
] withPrompt
""", [1, 2, 3])

assert_eval(
"""
Object subclass: AbortsRestoreMarks [
    | mark prompt1 prompt2 |

    start [
        mark    := ContinuationMark new.
        prompt1 := PromptTag new.
        prompt2 := PromptTag new.
        [ self last ] withPrompt: prompt1
    ]

    last [
        [ self between ] withMark: mark value: 'last'
    ]

    between [
        [ self first ]
            withPrompt: prompt2
            abort: [:v | mark marks: prompt1 ]
    ]

    first [
        [ self finish ] withMark: mark value: 'first'
    ]

    finish [
        prompt2 abort.
    ]
]

AbortsRestoreMarks new start
""", ['last'])
