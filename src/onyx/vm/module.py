
import os.path
from collections import namedtuple

import onyx.syntax.ast as ast
import onyx.objects as o

from onyx.syntax.macros import Expander
from onyx.syntax.parser import Parser


ONYX_LIB_SOURCES = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                 '..', 'ost'))
ONYX_BOOT_SOURCES = os.path.join(ONYX_LIB_SOURCES, 'boot')


class AnalyzeModule:
    def __init__(self, name, loader):
        self.name = name
        self.loader = loader
        self.imports = set()
        self.qnames = {}
        self.references = {}
        self.class_slots = {}

    def add_flag(self, name, flag):
        f = self.references.get(name, set())
        f.add(flag)
        self.references[name] = f

    def has_flag(self, ref, flag):
        return flag in self.references.get(ref, [])

    def is_assign(self, ref):
        return self.has_flag(ref, 'assign') or self.has_flag(ref, 'top-assign')

    def is_import(self, ref):
        return self.has_flag(ref, 'import')

    def is_reference(self, ref):
        return self.has_flag(ref, 'reference')

    def is_top_assign(self, ref):
        return self.has_flag(ref, 'top-assign')

    def is_class(self, ref):
        return self.has_flag(ref, 'class')

    def get_exports(self):
        return [r for r in self.references
                if self.is_top_assign(r)]

    def check(self, syntax):
        syntax.visit(self)

        assign_import = []
        undeclared = []
        for r in self.references:
            if self.is_assign(r) and self.is_import(r):
                assign_import.append(r)
            if (self.is_reference(r) and
                not self.is_top_assign(r) and
                not self.is_import(r)):
                undeclared.append(r)

        fail = False
        if assign_import != []:
            fail = True
            print('assigned import', assign_import)
        if undeclared != []:
            fail = True
            print('undeclared variables', undeclared)

        if fail:
            raise 'fail'

    def visit_const(self, const, env, top):
        pass

    def visit_seq(self, seq, env=None, top=True):
        # XXX: are true, false, and nil necessary
        env = (env or
               [o.get_symbol('nil'), o.get_symbol('true'), o.get_symbol('false')])
        for s in seq.statements:
            s.visit(self, env, top)

    def visit_module_import(self, imp, env, top):
        m = self.loader.visit_module(imp.name.id)
        self.imports.add(imp.name.id)
        for name in m.exports:
            self.qnames[name] = (m.name, name)
            self.add_flag(name, 'import')

        self.class_slots.update(m.class_slots)

    def visit_class(self, cls, env, top):
        self.add_flag(cls.name, 'top-assign')
        self.add_flag(cls.name, 'class')
        instance_vars = cls.instance_vars
        if cls.superclass_name != o.get_symbol('nil'):
            self.add_flag(cls.superclass_name, 'reference')
            if cls.superclass_name in self.qnames:
                super_name = self.qnames[cls.superclass_name]
            else:
                super_name = cls.superclass_name
            instance_vars += self.class_slots[super_name]
        self.class_slots[cls.name] = set(instance_vars)

        if cls.trait_expr:
            cls.trait_expr.visit(self, env, top)

        for m in cls.meta.methods:
            m.visit(self, env, False)

        for m in cls.methods:
            m.visit(self, instance_vars, False)

    def visit_trait(self, trait, env, top):
        self.add_flag(trait.name, 'top-assign')

        if trait.trait_expr:
            trait.trait_expr.visit(self, env, top)

        if trait.meta:
            for m in trait.meta.methods:
                m.visit(self, env, False)

        for m in trait.methods:
            m.visit(self, env, False)

    def visit_method(self, method, env, top):
        menv = (env + method.args + method.temps +
                [o.get_symbol('self'), o.get_symbol('super')])
        method.statements.visit(self, menv, top)

    def visit_send(self, send, env, top):
        send.receiver.visit(self, env, top)
        send.message.visit(self, env, top)

    def visit_ref(self, ref, env, top):
        if ref.name not in env:
            self.add_flag(ref.name, 'reference')

    def visit_primitive_message(self, message, env, top):
        self.visit_message(message, env, top)

    def visit_message(self, message, env, top):
        for a in message.args:
            a.visit(self, env, top)

    def visit_cascade(self, cascade, env, top):
        for m in cascade.messages:
            m.visit(self, env, top)

    def visit_assign(self, assign, env, top):
        if assign.var not in env:
            flag = '{}assign'.format(top and "top-" or "")
            self.add_flag(assign.var, flag)
        assign.expr.visit(self, env, top)

    def visit_repeat(self, repeat, env, top):
        repeat.body.visit(self, env, top)

    def visit_scope(self, scope, env, top):
        scope.body.visit(self, env + scope.temps, top)

    def visit_block(self, block, env, top):
        benv = env + block.args + block.temps
        block.statements.visit(self, benv, False)

    def visit_return(self, ret, env, top):
        ret.expression.visit(self, env, top)

    def visit_cond(self, cond, env, top):
        cond.test.visit(self, env, top)
        cond.ift.visit(self, env, top)
        cond.iff.visit(self, env, top)


class RewriteRefs:
    def __init__(self, module_info):
        self.module_info = module_info

    def rewrite(self, syntax):
        # XXX: rewrite instance and local variables
        return syntax.visit(self, [])

    def rewrite_ref_name(self, name):
        if self.module_info.is_import(name):
            return self.module_info.qnames.get(name)
        return (self.module_info.name, name)

    def visit_module_import(self, imp, env):
        pass

    def visit_const(self, const, env):
        return const

    def visit_seq(self, seq, env):
        statements = [s.visit(self, env) for s in seq.statements]
        statements = [s for s in statements if s]
        if len(statements) == 1:
            return statements[0]
        return seq._replace(statements=statements)

    def visit_class(self, cls, env):
        name = self.rewrite_ref_name(cls.name)
        if cls.superclass_name != o.get_symbol('nil'):
            superclass_name = self.rewrite_ref_name(cls.superclass_name)
        else:
            superclass_name = cls.superclass_name

        meta_methods = [m.visit(self, env) for m in cls.meta.methods]
        methods = [m.visit(self, cls.instance_vars) for m in cls.methods]
        meta = cls.meta._replace(methods=meta_methods)
        return cls._replace(name=name,
                            trait_expr=cls.trait_expr and cls.trait_expr.visit(self, env),
                            superclass_name=superclass_name,
                            meta=meta,
                            methods=methods)

    def visit_trait(self, trait, env):
        meta = trait.meta
        if trait.meta:
            meta = [m.visit(self, env) for m in trait.meta.methods]
        return trait._replace(name=self.rewrite_ref_name(trait.name),
                              trait_expr=trait.trait_expr and trait.trait_expr.visit(self, env),
                              meta=meta,
                              methods=[m.visit(self, env) for m in trait.methods])

    def visit_method(self, method, env):
        menv = (env + method.args + method.temps +
                [o.get_symbol('self'), o.get_symbol('super')])
        return method._replace(statements=method.statements.visit(self, menv))

    def visit_send(self, send, env):
        return send._replace(receiver=send.receiver.visit(self, env),
                             message=send.message.visit(self, env))

    def visit_ref(self, ref, env):
        if ref.name in env:
            return ref
        return ast.GlobalRef(ref.source_info, self.rewrite_ref_name(ref.name))

    def visit_primitive_message(self, message, env):
        return self.visit_message(message, env)

    def visit_message(self, message, env):
        return message._replace(args=[a.visit(self, env) for a in message.args])

    def visit_cascade(self, cascade, env):
        return cascade._replace(messages=[m.visit(self, env) for m in cascade.messages])

    def visit_assign(self, assign, env):
        var = assign.var
        if var not in env:
            var = self.rewrite_ref_name(var)
        return assign._replace(var=var, expr=assign.expr.visit(self, env))

    def visit_repeat(self, repeat, env):
        return repeat._replace(body=repeat.body.visit(self, env))

    def visit_scope(self, scope, env):
        return scope._replace(body=scope.body.visit(self, env + scope.temps))

    def visit_block(self, block, env):
        benv = env + block.args + block.temps
        return block._replace(statements=block.statements.visit(self, benv))

    def visit_return(self, ret, env):
        return ret._replace(expression=ret.expression.visit(self, env))

    def visit_cond(self, cond, env):
        return cond._replace(test=cond.test.visit(self, env),
                             ift=cond.ift.visit(self, env),
                             iff=cond.iff.visit(self, env))


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

    def add_import(self, syntax, name):
        mod_name = ast.ModuleName(None, name)
        i = ast.ModuleImport(None, mod_name)
        return ast.Seq(None, [i, syntax])

    def add_core_import(self, syntax):
        return self.add_import(syntax, o.get_symbol('core'))

    def load_core_syntax(self):
        boot_sources = 'core exception number collection string stream'.split()
        mods = []
        for root_name in boot_sources:
            src = os.path.join(ONYX_BOOT_SOURCES, '{}.ost'.format(root_name))
            mods.append(Parser.parse_file(src))
        return ast.Seq(None, mods)

    def find_module_file(self, name):
        p = name.split('.')
        p[-1] = p[-1] + '.ost'
        return os.path.join(ONYX_LIB_SOURCES, *p)

    def load_syntax(self, name):
        if name == 'core':
            return self.load_core_syntax()
        file_name = self.find_module_file(name)
        return Parser.parse_file(file_name)

    def visit(self, name, syntax):
        self.status[name] = "loading"
        if name != 'core':
            syntax = self.add_core_import(syntax)

        syntax = Expander().expand(syntax)
        an_mod = AnalyzeModule(name, self)
        an_mod.check(syntax)
        exports = an_mod.get_exports()
        imports = an_mod.imports
        class_slots = {(name, k): an_mod.class_slots[k]
                       for k in exports if an_mod.is_class(k)}
        code = RewriteRefs(an_mod).rewrite(syntax)
        m = Module(name, exports, imports, class_slots, code)
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
