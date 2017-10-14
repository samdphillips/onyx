
import attr
import os.path
from collections import namedtuple

import onyx.syntax.ast as ast
import onyx.objects as o

from onyx.syntax.macros import Expander
from onyx.syntax.parser import Parser


ONYX_LIB_SOURCES = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                 '..', 'ost'))
ONYX_BOOT_SOURCES = os.path.join(ONYX_LIB_SOURCES, 'boot')


@attr.s
class RefCompile:
    module_name = attr.ib()
    module_loader = attr.ib()
    top_names = attr.ib(init=False, default=attr.Factory(dict))
    exports = attr.ib(init=False, default=attr.Factory(set))
    export_classes = attr.ib(init=False, default=attr.Factory(set))
    class_slots = attr.ib(init=False, default=attr.Factory(dict))
    unresolved = attr.ib(init=False, default=attr.Factory(set))

    def load_import_names(self, imports):
        for imp in imports:
            m = self.module_loader.visit_module(imp.name)
            for name in m.exports:
                self.top_names[name] = ast.GlobalLoc(m.name, name)
            self.class_slots.update(m.class_slots)

    def compile(self, mod_syntax):
        self.load_import_names(mod_syntax.imports)
        compiled = self.visit(mod_syntax.body, [], [], True)
        if len(self.unresolved) > 0:
            raise Exception('unresolved', self.unresolved)
        return compiled

    def clear_unresolved(self, name):
        self.unresolved.discard(name)

    def make_lex_loc(self, i, j):
        return ast.LexLoc(i, j)

    def make_cls_loc(self, j):
        return ast.SlotLoc(j)

    def lookup_var_in_top(self, name):
        loc = self.top_names.get(name)
        if loc is None:
            loc = ast.GlobalLoc(self.module_name, name)
            self.unresolved.add(name)
        return loc

    def lookup_var_in_lex(self, env, name):
        for i, slots in enumerate(env):
            if name in slots:
                j = slots.index(name)
                return self.make_lex_loc(i, j)

    def lookup_var_in_cls(self, env, name):
        for i, v in reversed(list(enumerate(env))):
            if v == name:
                return self.make_cls_loc(i)

    def lookup_var(self, name, lex_env, cls_env):
        return (self.lookup_var_in_lex(lex_env, name) or
                self.lookup_var_in_cls(cls_env, name) or
                self.lookup_var_in_top(name))

    def visit(self, node, cls_env, lex_env, top):
        return node.visit(self, cls_env, lex_env, top)

    def visit_assign(self, assign, cls_env, lex_env, top):
        loc = self.lookup_var(assign.var, lex_env, cls_env)
        if top:
            self.clear_unresolved(assign.var)
            self.exports.add(assign.var)
            self.top_names[assign.var] = loc

        return assign._replace(
            var=loc,
            expr=self.visit(assign.expr, cls_env, lex_env, top)
        )

    def visit_block(self, block, cls_env, lex_env, top):
        local_vars = block.args + block.temps
        lex_env = [local_vars] + lex_env
        return block.visit_children_static(self.visit, cls_env, lex_env, False)

    def visit_class(self, cls, cls_env, lex_env, top):
        super_name = cls.superclass_name
        if super_name == o.get_symbol('nil'):
            super_slots = []
            super_cls_loc = None
        else:
            super_cls_loc = self.lookup_var_in_top(super_name)
            super_slots = self.class_slots[super_cls_loc]
        instance_vars = super_slots + cls.instance_vars
        self.clear_unresolved(cls.name)
        self.exports.add(cls.name)
        loc = ast.GlobalLoc(self.module_name, cls.name)
        self.top_names[cls.name] = loc
        self.class_slots[loc] = instance_vars
        self.export_classes.add(loc)
        cls = cls._replace(loc=loc, superclass_name=super_cls_loc)
        return cls.visit_children_static(self.visit, instance_vars, lex_env, False)

    def visit_meta(self, meta, cls_env, lex_env, top):
        return meta.visit_children_static(self.visit, [], lex_env, top)

    def visit_method(self, method, cls_env, lex_env, top):
        local_vars = method.args + method.temps
        lex_env = [local_vars] + lex_env
        return method.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_ref(self, ref, cls_env, lex_env, top):
        name = ref.name
        if name == o.get_symbol('self'):
            loc = ast.SelfLoc()
        elif name == o.get_symbol('super'):
            loc = ast.SuperLoc()
        else:
            loc = self.lookup_var(name, lex_env, cls_env)
        return ref._replace(name=loc)

    def visit_scope(self, scope, cls_env, lex_env, top):
        lex_env = [scope.temps] + lex_env
        return scope.visit_children_static(self.visit, cls_env, lex_env, False)

    def visit_trait(self, trait, cls_env, lex_env, top):
        self.clear_unresolved(trait.name)
        self.exports.add(trait.name)
        loc = ast.GlobalLoc(self.module_name, trait.name)
        self.top_names[trait.name] = loc
        trait = trait._replace(loc=loc)
        return trait.visit_children_static(self.visit, [], lex_env, False)

    ### traversals

    def visit_cascade(self, cascade, cls_env, lex_env, top):
        return cascade.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_cond(self, cond, cls_env, lex_env, top):
        return cond.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_const(self, const, cls_env, lex_env, top):
        return const

    def visit_message(self, message, cls_env, lex_env, top):
        return message.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_primitive_message(self, message, cls_env, lex_env, top):
        return message.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_repeat(self, repeat, cls_env, lex_env, top):
        return repeat.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_return(self, ret, cls_env, lex_env, top):
        return ret.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_send(self, send, cls_env, lex_env, top):
        return send.visit_children_static(self.visit, cls_env, lex_env, top)

    def visit_seq(self, seq, cls_env, lex_env, top):
        return seq.visit_children_static(self.visit, cls_env, lex_env, top)


Module = namedtuple('Module', 'name exports imports class_slots code')


class ModuleLoader:
    def __init__(self, vm):
        self.vm = vm
        self.modules = {}
        self.status = {}

    def is_module_visited(self, name):
        return self.status.get(name) in ["visited", "instantiated"]

    def is_module_visiting(self, name):
        return self.status.get(name) == "visiting"

    def is_module_instantiated(self, name):
        return self.status.get(name) == "instantiated"

    def add_import(self, mod, name):
        imp = ast.ModuleImport(None, name)
        mod.imports.append(imp)

    def add_core_import(self, syntax):
        return self.add_import(syntax, o.get_symbol('core'))

    def load_core_syntax(self):
        boot_sources = 'core exception number collection string stream'.split()
        syntaxes = []
        for root_name in boot_sources:
            src = os.path.join(ONYX_BOOT_SOURCES, '{}.ost'.format(root_name))
            syntaxes.append(Parser.parse_file(src).body)
        return ast.Module(None, [], ast.Seq(None, syntaxes))

    def find_module_file(self, name):
        p = name.split('.')
        p[-1] = p[-1] + '.ost'
        return os.path.join(ONYX_LIB_SOURCES, *p)

    def load_syntax(self, name):
        if name == 'core':
            return self.load_core_syntax()
        file_name = self.find_module_file(name)
        return Parser.parse_file(file_name)

    def visit(self, name, mod_syntax):
        self.status[name] = "loading"
        if name != 'core':
            self.add_core_import(mod_syntax)

        mod_syntax = Expander().expand(mod_syntax)
        rcmp = RefCompile(name, self)
        code = rcmp.compile(mod_syntax)
        imports = [imp.name for imp in mod_syntax.imports]
        class_slots = {k: rcmp.class_slots[k]
                       for k in rcmp.export_classes}
        m = Module(name, rcmp.exports, imports, class_slots, code)
        self.modules[name] = m
        self.status[name] = 'loaded'
        return m

    def visit_module(self, name):
        if self.is_module_visited(name):
            return self.modules[name]
        if self.is_module_visiting(name):
            raise Exception('recursion in loading')
        syntax = self.load_syntax(name)
        return self.visit(name, syntax)

    def instantiate(self, name):
        if self.is_module_instantiated(name):
            return

        self.status[name] = 'instantiating'
        m = self.modules.get(name)
        for i in m.imports:
            self.instantiate(i)
        v = self.vm.eval(m.code)
        self.status[name] = 'instantiated'
        return v
