
import attr
import heapq
import io
import os.path

import onyx.objects as o
import onyx.utils as u
import onyx.vm.frame as k

from onyx.syntax import ast
from onyx.syntax.lexer import Lexer
from onyx.syntax.parser import Parser
from onyx.vm.env import EmptyEnv, GlobalEnv, MethodEnv
from onyx.vm.module import ModuleLoader


ONYX_BOOT_SOURCES = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                  '..', 'ost', 'boot'))

INITIAL_FUEL = 10000


def pusher(cls):
    def _method(self, *args):
        self.pushk(cls, *args)
        self.marks = {}
    return _method


def task_attr(name):
    def _getter(self):
        return getattr(self.running_task, name)
    def _setter(self, value):
        setattr(self.running_task, name, value)
    return property(_getter, _setter)


@attr.s(frozen=True)
class Doing:
    node = attr.ib()
    is_done = False
    is_doing = True

    def step(self, vm):
        self.node.visit(vm)


@attr.s(frozen=True)
class Done:
    value = attr.ib()
    is_done = True
    is_doing = False

    def step(self, vm):
        vm.do_continue(self.value)


@attr.s(hash=False, cmp=False, repr=False)
class Task:
    state = attr.ib(default=None)
    priority = attr.ib(default=50)
    main_task = attr.ib(default=False)
    stack = attr.ib(init=False, default=attr.Factory(k.Stack))
    env = attr.ib(init=False, default=attr.Factory(EmptyEnv))
    marks = attr.ib(init=False, default=attr.Factory(dict))
    dead_channel_slot = attr.ib(init=False, default=attr.Factory(o.Slot))

    def get_slot(self, i):
        if i == 0:
            return self.dead_channel_slot
        else:
            raise KeyError(self, i)


@attr.s
class ReadyQueue:
    queue = attr.ib(init=False, default=attr.Factory(list))
    counter = attr.ib(init=False, default=0)

    def is_empty(self):
        return len(self.queue) == 0

    def __contains__(self, task):
        return task in (x[2] for x in self.queue)

    def add(self, task):
        item = (task.priority, self.counter, task)
        self.counter += 1
        heapq.heappush(self.queue, item)

    def next(self):
        _, _, task = heapq.heappop(self.queue)
        return task


class Interpreter:
    def __init__(self):
        self.running_task = Task(main_task=True)
        self.globals = GlobalEnv()
        self.module_loader = ModuleLoader(self)
        self.halted = True
        self.msg_tally = u.Tally()
        self.ready_tasks = ReadyQueue()
        self.waiting_tasks = set()
        self.atomic = False
        self.fuel = INITIAL_FUEL

    state = task_attr('state')
    stack = task_attr('stack')
    env = task_attr('env')
    marks = task_attr('marks')

    def doing(self, node):
        self.state = Doing(node)

    def done(self, value):
        self.state = Done(value)

    def should_stop(self):
        return (self.running_task.main_task and
            self.state.is_done and
            self.stack.is_empty())

    def is_running(self):
        return not self.should_stop()

    def is_task_switch(self):
        if self.running_task is None:
            return True
        if self.atomic:
            return False
        return self.fuel <= 0

    def step(self):
        self.state.step(self)
        self.fuel = self.fuel - 1

    def run(self):
        self.halted = False
        while self.is_running() and not self.halted:
            self.step()
            if self.is_task_switch():
                self.do_task_switch()
        return self.state.value

    def run_script(self, filename):
        with open(filename, 'r') as src:
            p = Parser(Lexer(filename, src))
            syntax = p.parse_module()
        name = object()
        self.module_loader.visit(name, syntax)
        return self.module_loader.instantiate(name)

    def eval(self, node):
        self.doing(node)
        return self.run()

    def eval_string(self, s, name=None, require=None):
        inp = io.StringIO(s)
        p = Parser(Lexer(s, inp))
        syntax = p.parse_module()
        name = name or object()
        require = require or []
        for r in require:
            self.module_loader.add_import(syntax, r)
        self.module_loader.visit(name, syntax)
        return self.module_loader.instantiate(name)

    def do_continue(self, value):
        frame = self.stack.pop()
        self.env = frame.env
        self.marks = frame.marks
        frame.do_continue(self, value)

    def lookup_variable(self, loc):
        return loc.find_ref(self.globals, self.env)

    def core_lookup(self, name):
        name = ('core', name)
        return self.globals.lookup(name).value

    def make_continuation(self, prompt_tag):
        # XXX: check for invalid frame index
        prompt_frame_i = self.stack.find_prompt(prompt_tag)
        frames = self.stack.get_frames_after(prompt_frame_i)
        return o.Continuation(frames)

    def make_method_dict(self, methods):
        return {m.name: m for m in methods}

    def make_block_env(self, block_closure, args):
        env = block_closure.env.extend(args,  len(block_closure.block.temps))
        return env

    def make_method_env(self, method, args, receiver, klass):
        env = MethodEnv(klass, receiver)
        env = env.extend(args, len(method.temps))
        return env

    def make_dnu_args(self, selector, args):
        msg_cls = self.core_lookup(o.get_symbol('Message'))
        msg = msg_cls.new_instance()
        msg.get_slot(msg_cls.instance_variable_slot(o.get_symbol('selector'))).assign(selector)
        msg.get_slot(msg_cls.instance_variable_slot(o.get_symbol('arguments'))).assign(args)
        return [msg]

    def do_block(self, block_closure, args):
        self.env = self.make_block_env(block_closure, args)
        self.doing(block_closure.block.statements)

    def do_message_dispatch(self, execute, message, value):
        if len(message.args) > 0:
            self.push_kmessage(message.args[0], execute, message, value, [], 1)
            self.doing(message.args[0])
        else:
            execute(message, value, [])

    def deref_value(self, v):
        if hasattr(v, 'deref'):
            return v.deref()
        return v

    def get_onyx_class(self, v):
        if hasattr(v, 'onyx_class'):
            return v.onyx_class(self)
        elif v is None:
            cls_name = 'UndefinedObject'
        elif v is True:
            cls_name = 'True'
        elif v is False:
            cls_name = 'False'
        else:
            cls_name = o.onyx_class_map.get(type(v)) or v.__class__.__name__
        return self.core_lookup(cls_name)

    def do_message_send(self, message, receiver, args):
        self.msg_tally.tally(message.selector)
        receiver_class = self.get_onyx_class(receiver)
        is_class = getattr(receiver, 'is_class', False)
        if message.method_cache.get((receiver_class.name, is_class)):
            result = message.method_cache[(receiver_class.name, is_class)]
        else:
            result = receiver_class.lookup_method(self, message.selector, is_class)
            message.method_cache[(receiver_class.name, is_class)] = result

        if not result.is_success:
            dnu_selector = o.get_symbol('doesNotUnderstand:')
            result = receiver_class.lookup_method(self, dnu_selector, is_class)
            if not result.is_success:
                raise Exception('dnu')

            args = self.make_dnu_args(message.selector,
                                      [self.deref_value(a) for a in args])

        receiver = self.deref_value(receiver)
        args = [self.deref_value(a) for a in args]
        self.env = self.make_method_env(result.method, args, receiver, result.cls)
        self.doing(result.method.statements)

    def do_primitive(self, message, receiver, args):
        self.msg_tally.tally(message.selector)
        if message.primitive:
            primitive = message.primitive
        else:
            name = 'primitive_' + u.camel_to_snake(message.selector[1:])
            primitive = getattr(self, name)
            message.primitive = primitive
        primitive(receiver, *args)

    def do_task_switch(self):
        if self.running_task is not None:
            self.ready_tasks.add(self.running_task)
        if self.ready_tasks.is_empty():
            raise Exception('no ready tasks')
        self.running_task = self.ready_tasks.next()
        self.fuel = INITIAL_FUEL

    def pushk(self, kcls, ast, *args):
        frame = kcls(self.env, self.marks, ast, *args)
        self.stack.push(frame)

    push_kassign = pusher(k.KAssign)
    push_kcascade = pusher(k.KCascade)
    push_kcond = pusher(k.KCond)
    push_kmessage = pusher(k.KMessage)
    push_kprompt = pusher(k.KPrompt)
    push_kreceiver = pusher(k.KReceiver)
    push_kseq = pusher(k.KSeq)
    push_ktrait = pusher(k.KTrait)

    def visit_assign(self, assignment):
        self.push_kassign(assignment, assignment.var)
        self.doing(assignment.expr)

    def visit_block(self, block):
        closure = o.BlockClosure(self.env, block)
        self.done(closure)

    def visit_cascade(self, cascade, value):
        if len(cascade.messages) > 1:
            self.push_kcascade(cascade, value, cascade.messages[1:])
        cascade.messages[0].visit(self, value)

    def visit_class(self, cls):
        self.push_kassign(cls, cls.loc)
        super_cls = cls.superclass_name and self.lookup_variable(cls.superclass_name).value
        method_dict = self.make_method_dict(cls.methods)
        if cls.meta:
            class_method_dict = self.make_method_dict(cls.meta.methods)
        else:
            class_method_dict = {}
        cls_o = o.Class(cls.name, super_cls, cls.instance_vars,
                        method_dict, class_method_dict)
        if cls.trait_expr is None:
            self.done(cls_o)
        else:
            self.push_ktrait(cls.trait_expr, cls_o)
            self.doing(cls.trait_expr)

    def visit_cond(self, cond):
        self.push_kcond(cond.test, cond.ift, cond.iff)
        self.doing(cond.test)

    def visit_const(self, const):
        self.done(const.value)

    def visit_global_ref(self, ref):
        self.done(self.globals.lookup(ref.name).value)

    def visit_message(self, message, value):
        self.do_message_dispatch(self.do_message_send, message, value)

    def visit_primitive_message(self, message, value):
        self.do_message_dispatch(self.do_primitive, message, value)

    def visit_ref(self, ref):
        self.done(self.lookup_variable(ref.name).value)

    def visit_repeat(self, repeat):
        self.push_kseq(repeat, [repeat])
        self.doing(repeat.body)

    def visit_scope(self, scope):
        self.env = self.env.extend([], len(scope.temps))
        self.doing(scope.body)

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
        self.push_kassign(trait, trait.loc)
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

    def continue_kcond(self, k, value):
        assert value is True or value is False
        if value is True:
            self.doing(k.success)
        elif value is False:
            self.doing(k.failure)

    def continue_kmessage(self, k, value):
        arg_values = k.arg_values + [value]
        if k.next_arg < len(k.message.args):
            expression = k.message.args[k.next_arg]
            next_arg = k.next_arg + 1
            self.pushk(k.__class__, expression, k.execute, k.message,
                       k.receiver_value, arg_values, next_arg)
            self.doing(expression)
        else:
            k.execute(k.message, k.receiver_value, arg_values)

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
        self.done([None] * size)

    def primitive_array_size(self, array):
        self.done(len(array))

    def primitive_block_argument_count(self, block):
        self.done(len(block.block.args))

    def primitive_block_value(self, block):
        self.do_block(block, [])

    def primitive_block_value_(self, block, a):
        self.do_block(block, [a])

    def primitive_block_value_value_(self, block, a, b):
        self.do_block(block, [a, b])

    def primitive_block_value_value_value_(self, block, a, b, c):
        self.do_block(block, [a, b, c])

    def primitive_block_value_value_value_value_(self, block, a, b, c, d):
        self.do_block(block, [a, b, c, d])

    def primitive_block_value_with_arguments_(self, block, array):
        self.do_block(block, array)

    def primitive_block_with_continuation_(self, block, prompt_tag):
        k = self.make_continuation(prompt_tag)
        self.do_block(block, [k])

    def primitive_block_with_mark_value_(self, block, mark, value):
        self.marks[mark] = value
        self.do_block(block, [])

    def primitive_block_with_prompt_abort_(self, block, prompt_tag, abort_block):
        self.push_kprompt(block.block, prompt_tag, abort_block)
        self.do_block(block, [])

    def primitive_byte_array_at_(self, barray, index):
        self.done(barray[index])

    def primitive_byte_array_at_put_(self, barray, index, value):
        barray[index] = value
        self.done(value)

    def primitive_byte_array_new_(self, _cls, size):
        self.done(bytearray(size))

    def primitive_byte_array_size(self, barray):
        self.done(len(barray))

    def primitive_character_as_lowercase(self, c):
        self.done(o.get_character(ord(chr(c.codepoint).lower())))

    def primitive_character_as_string(self, c):
        self.done(chr(c.codepoint))

    def primitive_character_code_point(self, c):
        self.done(c.codepoint)

    def primitive_character_code_point_(self, _, i):
        self.done(o.Character(i))

    def primitive_class_name(self, klass):
        self.done(str(klass.name))

    def primitive_class_superclass(self, klass):
        self.done(klass.super_class)

    def primitive_class_new(self, klass):
        self.done(klass.new_instance())

    def primitive_continuation_do_(self, continuation, block):
        for f in continuation.frames:
            self.stack.push(f)
        self.do_block(block, [])

    def primitive_continuation_mark_first_mark_(self, mark, prompt_tag):
        if mark in self.marks:
            value = self.marks[mark]
        else:
            value = self.stack.find_first_mark(mark, prompt_tag)
        self.done(value)

    def primitive_continuation_marks_(self, mark, prompt_tag):
        v = []
        if mark in self.marks:
            v.append(self.marks[mark])
        v += self.stack.find_marks(mark, prompt_tag)
        self.done(v)

    def primitive_number_print_string(self, n):
        self.done(str(n))

    def primitive_object_class(self, obj):
        self.done(self.get_onyx_class(obj))

    def primitive_object_debug(self, obj):
        m = getattr(obj, 'debug', print)
        m(obj)
        self.done(obj)

    def primitive_object_equal_(self, a, b):
        self.done(a is b)

    def primitive_object_halt(self, o):
        self.halted = True
        import pdb
        pdb.set_trace()

    def primitive_prompt_abort_(self, prompt_tag, value):
        # XXX: check for invalid frame index
        prompt_frame_i = self.stack.find_prompt(prompt_tag)
        abort_block = self.stack.frames[prompt_frame_i].abort_block
        self.stack.top = prompt_frame_i
        self.do_continue(None)
        self.do_block(abort_block, [value])

    def primitive_small_int_add_(self, a, b):
        self.done(a + b)

    def primitive_small_int_bit_and_(self, a, b):
        self.done(a & b)

    def primitive_small_int_bit_shift_(self, a, b):
        if b >= 0:
            v = (a << b) & 0xFFFFFFFFFFFFFFFF
        else:
            v = (a >> -b) & 0xFFFFFFFFFFFFFFFF
        self.done(v)

    def primitive_small_int_equal_(self, a, b):
        self.done(a == b)

    def primitive_small_int_gt_(self, a, b):
        self.done(a > b)

    def primitive_small_int_lt_(self, a, b):
        self.done(a < b)

    def primitive_small_int_modulo_(self, a, b):
        self.done(a % b)

    def primitive_small_int_mul_(self, a, b):
        self.done(a * b)

    def primitive_small_int_quo_(self, a, b):
        self.done(a // b)

    def primitive_small_int_sub_(self, a, b):
        self.done(a - b)

    def primitive_string_at_(self, s, i):
        c = ord(s[i])
        self.done(o.Character(c))

    def primitive_string_concatenate_(self, a, b):
        self.done(a + b)

    def primitive_string_display(self, s):
        import sys
        sys.stdout.write(s)
        sys.stdout.flush()
        self.done(None)

    def primitive_string_size(self, s):
        self.done(len(s))

    def primitive_string_slice_from_to_(self, s, start, end):
        self.done(s[start:end + 1])

    def primitive_symbol_as_string(self, symbol):
        self.done(str(symbol))

    def primitive_system_is_broken_(self, obj, msg):
        # XXX: make better
        raise Exception(obj, msg)

    def primitive_task_atomic_begin(self, task_cls):
        self.atomic = True
        self.done(None)

    def primitive_task_atomic_end(self, task_cls):
        self.atomic = False
        self.done(None)

    def primitive_task_current(self, task_cls):
        self.done(self.running_task)

    def primitive_task_new(self, cls):
        task = Task()
        message = ast.Message(None, o.get_symbol('value'), [])
        frame = k.KReceiver(EmptyEnv(), {}, None, message)
        task.stack.push(frame)
        self.waiting_tasks.add(task)
        self.done(task)

    def primitive_task_resume_(self, task, value):
        self.waiting_tasks.discard(task)
        if task not in self.ready_tasks:
            task.state = Done(value)
            self.ready_tasks.add(task)
        self.done(None)

    def primitive_task_state(self, task):
        state = None
        if task == self.running_task:
            state = o.get_symbol('running')
        elif task in self.ready_tasks:
            state = o.get_symbol('ready')
        elif task in self.waiting_tasks:
            state = o.get_symbol('suspended')
        else:
            state = o.get_symbol('terminated')
        self.done(state)

    def primitive_task_suspend(self, task):
        if task == self.running_task:
            self.running_task = None
            self.atomic = False
        if task in self.ready_tasks:
            self.ready_tasks.remove(task)
        self.waiting_tasks.add(task)

    def primitive_task_terminate(self, task):
        if task == self.running_task:
            self.running_task = None
            self.atomic = False
        if task in self.ready_tasks:
            self.ready_tasks.remove(task)
        if task in self.waiting_tasks:
            self.waiting_tasks.remove()

    def primitive_trait_merge_(self, a, b):
        self.done(a.merge_trait(b))

    def primitive_trait_new(self, trait):
        self.done(o.Trait(None, {}, {}))
