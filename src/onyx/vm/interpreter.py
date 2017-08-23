
import io
import os.path

from collections import namedtuple

import onyx.objects as o
import onyx.utils as u
import onyx.vm.frame as k

from onyx.syntax import ast
from onyx.syntax.lexer import Lexer
from onyx.syntax.parser import Parser
from onyx.vm.env import Env, GlobalEnv


ONYX_BOOT_SOURCES = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                  '..', 'ost', 'boot'))


def pusher(cls):
    def _method(self, *args):
        self.pushk(cls, *args)
    return _method


class Doing(namedtuple('Doing', 'node')):
    is_done = False
    is_doing = True

    def step(self, vm):
        self.node.visit(vm)


class Done(namedtuple('Done', 'value')):
    is_done = True
    is_doing = False

    def step(self, vm):
        vm.do_continue(self.value)


class Interpreter:
    boot_sources = 'core exception number collection string stream'.split()

    @classmethod
    def boot(cls):
        mods = []
        for root_name in cls.boot_sources:
            src = os.path.join(ONYX_BOOT_SOURCES, '{}.ost'.format(root_name))
            mods.append(Parser.parse_file(src))
        vm = cls()
        vm.eval(ast.Seq(None, mods))
        return vm

    def __init__(self):
        self.stack = k.Stack()
        self.env = Env()
        self.receiver = None
        self.retp = None
        self.marks = {}
        self.globals = GlobalEnv()
        self.receiver = None
        self.halted = True

    def doing(self, node):
        self.state = Doing(node)

    def done(self, value):
        self.state = Done(value)

    def is_running(self):
        return not (self.state.is_done and self.stack.is_empty())

    def step(self):
        self.state.step(self)

    def run(self):
        self.halted = False
        while self.is_running() and not self.halted:
            self.step()
        return self.state.value

    def eval(self, node):
        self.doing(node)
        return self.run()

    def eval_string(self, s):
        inp = io.StringIO(s)
        p = Parser(Lexer(s, inp))
        return self.eval(p.parse_module())

    def do_continue(self, value):
        frame = self.stack.pop()
        self.env = frame.env
        self.receiver = frame.receiver
        self.retp = frame.retk
        self.marks = frame.marks
        frame.do_continue(self, value)

    def lookup_variable(self, name):
        return (self.env.lookup(name) or
                (self.receiver and
                 self.receiver.lookup_instance_variable(name)) or
                self.globals.lookup(name))

    def make_continuation(self, prompt_tag):
        # XXX: check for invalid frame index
        prompt_frame_i = self.stack.find_prompt(prompt_tag)
        frames = self.stack.get_frames_after(prompt_frame_i)
        return o.Continuation(frames)

    def make_method_dict(self, methods):
        method_dict = {}
        for m in methods:
            method_dict[m.name] = o.Method(**m._asdict())
        return method_dict

    def make_block_env(self, block_closure, args):
        env = Env(block_closure.env)
        env.add_args(block_closure.block.args, args)
        env.add_temps(block_closure.block.temps)
        return env

    def make_method_env(self, method, args, receiver, klass):
        env = Env()
        env.add_args(method.args, args)
        env.add_temps(method.temps)
        env.add_binding(o.get_symbol('self'), receiver)
        env.add_binding(o.get_symbol('super'), o.Super(receiver, klass))
        return env

    def do_block(self, block_closure, args):
        self.env = self.make_block_env(block_closure, args)
        self.receiver = block_closure.receiver
        self.retp = block_closure.retp
        self.doing(block_closure.block.statements)

    def do_message_dispatch(self, execute, message, value):
        if len(message.args) > 0:
            self.push_kmessage(message.args[0], execute, message.selector,
                               value, [], message.args[1:])
            self.doing(message.args[0])
        else:
            execute(message.selector, value, [])

    def do_message_send(self, selector, receiver, args):
        receiver_class = receiver.onyx_class(self)
        result = receiver_class.lookup_method(self, selector, receiver.is_class)
        if not result.is_success:
            raise Exception('write dnu code')

        receiver = receiver.deref()
        args = [a.deref() for a in args]
        self.env = self.make_method_env(result.method, args, receiver, result.klass)
        self.receiver = receiver
        self.retp = self.stack.top
        self.doing(result.method.statements)

    def do_primitive(self, selector, receiver, args):
        name = 'primitive_' + u.camel_to_snake(selector[1:])
        primitive = getattr(self, name)
        primitive(receiver, *args)

    def pushk(self, kcls, ast, *args):
        frame = kcls(self.env, self.receiver, self.retp, self.marks, ast, *args)
        self.stack.push(frame)

    push_kassign = pusher(k.KAssign)
    push_kcascade = pusher(k.KCascade)
    push_kmessage = pusher(k.KMessage)
    push_kprompt = pusher(k.KPrompt)
    push_kreceiver = pusher(k.KReceiver)
    push_kseq = pusher(k.KSeq)
    push_ktrait = pusher(k.KTrait)

    def visit_assign(self, assignment):
        self.push_kassign(assignment, assignment.var)
        self.doing(assignment.expr)

    def visit_block(self, block):
        closure = o.BlockClosure(self.env, self.receiver, self.retp, block)
        self.done(closure)

    def visit_cascade(self, cascade, value):
        if len(cascade.messages) > 1:
            self.push_kcascade(cascade, value, cascade.messages[1:])
        cascade.messages[0].visit(self, value)

    def visit_class(self, klass):
        self.push_kassign(klass, klass.name)
        super_class = self.lookup_variable(klass.superclass_name).value
        method_dict  = self.make_method_dict(klass.methods)
        if klass.meta:
            class_method_dict = self.make_method_dict(klass.meta.methods)
        else:
            class_method_dict = {}
        cls = o.Class(klass.name, super_class, klass.instance_vars,
                      klass.meta.instance_vars, None, method_dict,
                      class_method_dict)
        if klass.trait_expr is None:
            self.done(cls)
        else:
            self.push_ktrait(klass.trait_expr, cls)
            self.doing(klass.trait_expr)

    def visit_const(self, const):
        self.done(const.value)

    def visit_message(self, message, value):
        self.do_message_dispatch(self.do_message_send, message, value)

    def visit_primitive_message(self, message, value):
        self.do_message_dispatch(self.do_primitive, message, value)

    def visit_ref(self, ref):
        self.done(self.lookup_variable(ref.name).value)

    def visit_return(self, ret):
        if self.retp is None:
            raise TopReturnError()
        self.stack.top = self.retp
        self.doing(ret.expression)

    def visit_send(self, send):
        self.push_kreceiver(send, send.message)
        self.doing(send.receiver)

    def visit_seq(self, seq):
        if len(seq.statements) == 0:
            self.done(None)
        elif len(seq.statements) == 1:
            self.doing(seq.statements[0])
        else:
            self.doing(seq.statements[0])
            self.push_kseq(seq, seq.statements[1:])

    def visit_trait(self, trait):
        name = trait.name
        self.push_kassign(trait, name)
        method_dict = self.make_method_dict(trait.methods)
        if trait.meta:
            class_method_dict = self.make_method_dict(trait.meta.methods)
        else:
            class_method_dict = {}
        trait_value = o.Trait(name, method_dict, class_method_dict)
        if trait.trait_expr is None:
            self.done(trait_value)
        else:
            self.push_ktrait(trait.trait_expr, trait_value)
            self.doing(trait.trait_expr)

    def continue_kassign(self, k, value):
        var = self.lookup_variable(k.name)
        var.assign(value)

    def continue_kcascade(self, k, value):
        if len(k.messages) > 1:
            self.push_kcascade(k.ast, k.receiver_value, k.messages[1:])
        k.messages[0].visit(self, k.receiver_value)

    def continue_kmessage(self, k, value):
        arg_values = k.arg_values + [value]
        if len(k.arg_expressions) > 0:
            expression = k.arg_expressions[0]
            arg_expressions = k.arg_expressions[1:]
            self.pushk(k.__class__, expression, k.execute, k.selector,
                       k.receiver_value, arg_values, arg_expressions)
            self.doing(expression)
        else:
            k.execute(k.selector, k.receiver_value, arg_values)

    def continue_kprompt(self, k, value):
        pass

    def continue_kreceiver(self, k, value):
        k.message.visit(self, value)

    def continue_kseq(self, k, value):
        if len(k.statements) > 1:
            self.push_kseq(k.statements[0], k.statements[1:])
        self.doing(k.statements[0])

    def continue_ktrait(self, k, value):
        decl = k.declaration
        decl = decl.merge_trait(value)
        self.done(decl)

    def primitive_array_at_(self, array, index):
        self.done(array[index])

    def primitive_array_at_put_(self, array, index, value):
        array[index] = value
        self.done(value)

    def primitive_array_new_(self, klass, size):
        self.done(o.Array([o.nil] * size))

    def primitive_array_size(self, array):
        self.done(o.SmallInt(len(array)))

    def primitive_block_with_continuation_(self, block, prompt_tag):
        k = self.make_continuation(prompt_tag)
        self.do_block(block, [k])

    def primitive_block_with_prompt_abort_(self, block, prompt_tag, abort_block):
        self.push_kprompt(block.block, prompt_tag, abort_block)
        self.do_block(block, [])

    def primitive_block_with_values_(self, block, array):
        self.do_block(block, array)

    def primitive_character_as_lowercase(self, c):
        self.done(o.Character(ord(chr(c).lower())))

    def primitive_character_as_string(self, c):
        self.done(o.String(chr(c)))

    def primitive_character_code_point(self, c):
        self.done(o.SmallInt(c))

    def primitive_character_code_point_(self, _, i):
        self.done(o.Character(i))

    def primitive_class_new(self, klass):
        self.done(klass.new_instance())

    def primitive_continuation_do_(self, continuation, block):
        for f in continuation.frames:
            self.stack.push(f)
        self.do_block(block, [])

    def primitive_object_class(self, obj):
        self.done(obj.onyx_class(self))

    def primitive_object_debug(self, obj):
        obj.debug()
        self.done(obj)

    def primitive_object_equal_(self, a, b):
        self.done(o.onyx_bool(a == b and a.__class__ == b.__class__))

    def primitive_object_halt(self, o):
        self.halted = True
        raise Exception('halting')

    def primitive_prompt_abort_(self, prompt_tag, value):
        # XXX: check for invalid frame index
        self.stack.trace()
        prompt_frame_i = self.stack.find_prompt(prompt_tag)
        print(prompt_frame_i)
        abort_block = self.stack.frames[prompt_frame_i].abort_block
        self.stack.top = prompt_frame_i
        self.do_continue(None)
        self.do_block(abort_block, [value])

    def primitive_small_int_add_(self, a, b):
        self.done(o.SmallInt(a + b))

    def primitive_small_int_lt_(self, a, b):
        self.done(o.onyx_bool(a < b))

    def primitive_small_int_mul_(self, a, b):
        self.done(o.SmallInt(a * b))

    def primitive_small_int_quo_(self, a, b):
        self.done(o.SmallInt(a // b))

    def primitive_small_int_sub_(self, a, b):
        self.done(o.SmallInt(a - b))

    def primitive_string_at_(self, s, i):
        c = ord(s[i])
        self.done(o.Character(c))

    def primitive_string_concat_(self, a, b):
        self.done(o.String(a + b))

    def primitive_string_size(self, s):
        self.done(o.SmallInt(len(s)))

    def primitive_trait_merge_(self, a, b):
        self.done(a.merge_trait(b))

    def primitive_trait_new(self, trait):
        self.done(o.Trait(None, {}, {}))
