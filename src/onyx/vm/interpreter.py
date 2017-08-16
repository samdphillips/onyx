
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
    boot_sources = 'core number'.split()

    @classmethod
    def boot(cls):
        mods = []
        for root_name in cls.boot_sources:
            src = os.path.join(ONYX_BOOT_SOURCES, '{}.ost'.format(root_name))
            with open(src, 'r') as src_file:
                mods.append(Parser.parse_file(src_file))
        vm = cls()
        vm.eval(ast.Seq(mods))
        return vm

    def __init__(self):
        self.stack = k.Stack()
        self.env = Env()
        self.receiver = None
        self.retp = None
        self.marks = {}
        self.globals = GlobalEnv()
        self.receiver = None

    def doing(self, node):
        self.state = Doing(node)

    def done(self, value):
        self.state = Done(value)

    def is_running(self):
        return not (self.state.is_done and self.stack.is_empty())

    def step(self):
        self.state.step(self)

    def run(self):
        while self.is_running():
            self.step()
        return self.state.value

    def eval(self, node):
        self.doing(node)
        return self.run()

    def eval_string(self, s):
        inp = io.StringIO(s)
        p = Parser(Lexer(inp))
        return self.eval(p.parse_module())

    def do_continue(self, value):
        frame = self.stack.pop()
        self.env = frame.env
        self.receiver = frame.receiver
        self.retp = frame.retk
        self.marks = frame.marks
        frame.do_continue(self, value)

    def lookup_var(self, name):
        return (self.env.lookup(name) or
                (self.receiver and self.receiver.lookup_instance_var(name)) or
                self.globals.lookup(name))

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
            self.push_kmessage(execute, message.selector, value, [], message.args[1:])
            self.doing(message.args[0])
        else:
            execute(message.selector, value, [])

    def do_message_send(self, selector, receiver, args):
        receiver_class = receiver.onyx_class(self)
        result = receiver_class.lookup_method(self, selector, receiver.is_class)
        if not result.is_success:
            raise Exception('write dnu code')

        self.env = self.make_method_env(result.method, args, receiver, result.klass)
        self.receiver = receiver
        self.retp = self.stack.top
        self.doing(result.method.statements)

    def do_primitive(self, selector, receiver, args):
        name = 'primitive_' + u.camel_to_snake(selector[1:])
        primitive = getattr(self, name)
        primitive(receiver, *args)

    def pushk(self, kcls, *args):
        frame = kcls(self.env, self.receiver, self.retp, self.marks, *args)
        self.stack.push(frame)

    push_kassign = pusher(k.KAssign)
    push_kmessage = pusher(k.KMessage)
    push_kreceiver = pusher(k.KReceiver)
    push_kseq = pusher(k.KSeq)
    push_ktrait = pusher(k.KTrait)

    def visit_assign(self, assignment):
        self.push_kassign(assignment.var)
        self.doing(assignment.expr)

    def visit_block(self, block):
        closure = o.BlockClosure(self.env, self.receiver, self.retp, block)
        self.done(closure)

    def visit_class(self, klass):
        self.push_kassign(klass.name)
        super_class = self.lookup_var(klass.superclass_name).value
        method_dict  = self.make_method_dict(klass.methods)
        if klass.meta:
            class_method_dict = self.make_method_dict(klass.meta.methods)
        else:
            class_method_dict = {}
        # XXX: add trait expression
        cls = o.Class(klass.name, super_class, klass.instance_vars,
                      klass.meta.instance_vars, None, method_dict,
                      class_method_dict)
        if klass.trait_expr is None:
            self.done(cls)
        else:
            self.push_ktrait(cls)
            self.doing(klass.trait_expr)

    def visit_const(self, const):
        self.done(const.value)

    def visit_message(self, message, value):
        self.do_message_dispatch(self.do_message_send, message, value)

    def visit_primitive_message(self, message, value):
        self.do_message_dispatch(self.do_primitive, message, value)

    def visit_ref(self, ref):
        self.done(self.lookup_var(ref.name).value)

    def visit_send(self, send):
        self.push_kreceiver(send.message)
        self.doing(send.receiver)

    def visit_seq(self, seq):
        if len(seq.statements) == 0:
            self.done(None)
        elif len(seq.statements) == 1:
            self.doing(seq.statements[0])
        else:
            self.doing(seq.statements[0])
            self.push_kseq(seq.statements[1:])

    def visit_trait(self, trait):
        name = trait.name
        self.push_kassign(name)
        method_dict = self.make_method_dict(trait.methods)
        if trait.meta:
            class_method_dict = self.make_method_dict(trait.meta.methods)
        else:
            class_method_dict = {}
        trait_value = o.Trait(name, None, method_dict, class_method_dict)
        if trait.trait_expr is None:
            self.done(trait_value)
        else:
            self.push_ktrait(trait_value)
            self.doing(trait.trait_expr)

    def continue_kassign(self, k, value):
        var = self.lookup_var(k.name)
        var.value = value

    def continue_kmessage(self, k, value):
        arg_values = k.arg_values + [value]
        if len(k.arg_expressions) > 0:
            expression = k.arg_expressions[0]
            arg_expressions = k.arg_expressions[1:]
            self.pushk(k.__class__, k.execute, k.selector,
                       k.receiver_value, arg_values, arg_expressions)
            self.doing(expression)
        else:
            k.execute(k.selector, k.receiver_value, arg_values)

    def continue_kreceiver(self, k, value):
        k.message.visit(self, value)

    def continue_kseq(self, k, value):
        if len(k.statements) > 1:
            self.push_kseq(k.statements[1:])
        self.doing(k.statements[0])

    def continue_ktrait(self, k, value):
        decl = k.declaration
        self.done(decl._replace(trait=value))

    def primitive_block_value(self, block):
        self.do_block(block, [])

    def primitive_class_new(self, klass):
        self.done(klass.new_instance())

    def primitive_small_int_add_(self, a, b):
        self.done(o.SmallInt(a + b))

    def primitive_small_int_lt_(self, a, b):
        self.done(o.onyx_bool(a < b))