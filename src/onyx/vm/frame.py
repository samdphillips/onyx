
from collections import namedtuple


class Stack:
    def __init__(self):
        self.top = -1
        self.frames = []

    def grow(self):
        self.frames = self.frames + [None] * 16

    def is_empty(self):
        return self.top == -1

    def is_full(self):
        return self.top == len(self.frames) - 1

    def pop(self):
        v = self.frames[self.top]
        self.top -= 1
        return v

    def push(self, frame):
        if self.is_full():
            self.grow()
        self.top += 1
        self.frames[self.top] = frame

    def trace(self):
        for frame in self.frames[0:self.top]:
            print("{0.__class__.__name__} {0.ast.source_info}".format(frame))


class Frame:
    def do_continue(self, vm, value):
        name = "continue_" + self.__class__.__name__.lower()
        getattr(vm, name)(self, value)


_common_frame_fields = 'env receiver retk marks ast'
def frame_type(name, *fields):
    # XXX: just use fields as a string
    all_fields = _common_frame_fields + " " + ' '.join(fields)
    nt = namedtuple(name, all_fields)
    class _frame(nt, Frame):
        pass
    _frame.__name__ = name
    return _frame


KAssign = frame_type('KAssign', 'name')
KCascade = frame_type('KCascade', 'receiver_value messages')
KMessage = frame_type('KMessage',
                      'execute',
                      'selector',
                      'receiver_value',
                      'arg_values',
                      'arg_expressions')
KReceiver = frame_type('KReceiver', 'message')
KSeq = frame_type('KSeq', 'statements')
KTrait = frame_type('KTrait', 'declaration')
