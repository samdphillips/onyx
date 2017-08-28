
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

    def find_prompt(self, prompt_tag):
        i = self.top
        while i >= 0 and not self.frames[i].has_tag(prompt_tag):
            i -= 1
        return i

    def find_marks(self, mark, prompt_tag):
        i = self.top
        while i >= 0:
            if self.frames[i].has_mark(mark):
                yield self.frames[i].mark_value(mark)

            if self.frames[i].has_tag(prompt_tag):
                break
            i -= 1

    def find_first_mark(self, mark, prompt_tag):
        return next(self.find_marks(mark, prompt_tag))

    def get_frames_after(self, i):
        return self.frames[i+1:self.top+1]

    def trace(self):
        for frame in self.frames[0:self.top+1]:
            print("{}".format(frame))


class Frame:
    def do_continue(self, vm, value):
        name = "continue_" + self.__class__.__name__.lower()
        getattr(vm, name)(self, value)

    def has_tag(self, prompt_tag):
        return False

    def has_mark(self, mark):
        return mark in self.marks

    def mark_value(self, mark):
        return self.marks[mark]

    @property
    def extra_frame_info(self):
        return ''

    @property
    def format_marks(self):
        s = []
        for k, v in self.marks.items():
            s.append("{} -> {}".format(hex(id(k)), v))
        if len(s) > 0:
            s = "[\n" + '\n'.join([(" " * 4 + v) for v in s]) + "\n]"
        else:
            s = "[]"
        return s

    def __format__(self, fmt_args):
        return ("{0.__class__.__name__}{0.extra_frame_info}\n" +
                "{0.format_marks}\n" +
                "{0.ast.source_info}").format(self)


_common_frame_fields = 'env retk marks ast'
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

class KPrompt(frame_type('KPrompt', 'prompt_tag', 'abort_block')):
    def has_tag(self, prompt_tag):
        return self.prompt_tag == prompt_tag

    @property
    def extra_frame_info(self):
        return ' <<{}>>\nabort -> {}'.format(hex(id(self.prompt_tag)), self.abort_block.block.source_info)

KReceiver = frame_type('KReceiver', 'message')
KSeq = frame_type('KSeq', 'statements')
KTrait = frame_type('KTrait', 'declaration')
