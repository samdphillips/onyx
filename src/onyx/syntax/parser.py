
import onyx.syntax.ast as ast
import onyx.objects as o

from contextlib import closing

from onyx.syntax.lexer import Lexer, Token


class ParseError(Exception):
    def __init__(self, actual, expected, buffer):
        self.actual = actual
        self.expected = expected
        self.buffer = buffer


class Parser:
    @classmethod
    def parse_file(cls, file_name):
        with closing(Lexer.from_file(file_name)) as lexer:
            parser = cls(lexer)
            return parser.parse_module()

    def __init__(self, lexer):
        self.lexer = lexer
        self.lookahead = []
        self.current = None
        self.step()

    def step(self):
        if len(self.lookahead) == 0:
            self.current = self.lexer.lex_token()
        else:
            self.lookahead.pop()

    def current_token(self):
        if len(self.lookahead) == 0:
            return self.current
        return self.lookahead[-1]

    def push_token(self, token):
        self.lookahead.append(token)

    def current_is_oneof(self, *types):
        return self.current_token().type in types

    def parse_error(self, expected=None):
        raise ParseError(self.current_token(), expected, self.lexer.buf)

    def expect(self, tok_type, tok_value=None):
        # XXX: different exception for parsing expectations
        if self.current_token().type != tok_type:
            self.parse_error([tok_type])
        elif tok_value is not None:
            if tok_value != self.current_token().value:
                self.parse_error([tok_value])
        self.step()

    def make_message(self, source_info, selector, args=[]):
        msg_class = ast.Message
        if selector.startswith('_'):
            msg_class = ast.PrimitiveMessage
        return msg_class(source_info, selector, args)

    def parse_nested_expr(self):
        self.expect('lpar')
        expr = self.parse_expr()
        self.expect('rpar')
        return expr

    def parse_return(self):
        source_info = self.current_token().source_info
        self.expect('caret')
        expr = self.parse_expr()
        source_info += expr.source_info
        return ast.Return(source_info, expr)

    def parse_statement(self):
        if self.current_is_oneof('caret'):
            return self.parse_return()
        elif self.current_is_oneof('character', 'string', 'int', 'symbol',
                                   'id', 'lpar', 'lcurl', 'lbarray', 'lparray',
                                   'lsq'):
            return self.parse_expr()
        else:
            self.parse_error('expected expr')

    def parse_statements(self):
        stmts = []
        source_info = self.current_token().source_info
        while True:
            if self.current_is_oneof('caret', 'character', 'int', 'string',
                                     'symbol', 'id', 'lpar', 'lcurl',
                                     'lbarray', 'lparray', 'lsq'):
                stmt = self.parse_statement()
                stmts.append(stmt)
                source_info += stmt.source_info
            else:
                break

            if self.current_is_oneof('dot'):
                source_info += self.current_token().source_info
                self.step()
            else:
                break
        return source_info, stmts

    def parse_executable_code(self):
        temps = self.parse_vars()
        source_info, statements = self.parse_statements()
        statements = ast.Seq(source_info, statements)
        return temps, statements

    def parse_block(self):
        source_info = self.current_token().source_info
        self.expect('lsq')
        args = []
        if self.current_is_oneof('blockarg'):
            while self.current_is_oneof('blockarg'):
                args.append(self.current_token().value)
                self.step()
            if self.current_token().matches(Token('binsel', '|')):
                self.step()
            elif self.current_token().matches(Token('binsel', '||')):
                source_info = self.current_token().source_info
                self.step()
                self.push_token(Token('binsel', '|', source_info))
            else:
                self.parse_error('Expected "|"')

        block = {'args': args}
        block['temps'], block['statements'] = self.parse_executable_code()
        source_info += self.current_token().source_info
        self.expect('rsq')
        return ast.Block(source_info, **block)

    def parse_byte_array(self):
        source_info = self.current_token().source_info
        self.expect('lbarray')
        elements = []
        while self.current_is_oneof('int'):
            elements.append(self.current_token().value)
            self.step()
        source_info += self.current_token().source_info
        self.expect('rsq')
        return ast.Const(source_info, o.ByteArray(elements))

    def parse_expr_array(self):
        source_info = self.current_token().source_info
        self.expect('lcurl')
        _, statements = self.parse_statements()
        source_info += self.current_token().source_info
        self.expect('rcurl')

        size = len(statements)
        rcvr = ast.Send(source_info,
                        ast.Ref(source_info, o.get_symbol('Array')),
                        ast.Message(source_info, o.get_symbol('new:'),
                                    [ast.Const(source_info, size)]))
        if size == 0:
            return rcvr
        messages = [ast.Message(source_info, o.get_symbol('at:put:'),
                                [ast.Const(source_info, i), e])
                    for i, e in enumerate(statements)]
        messages.append(ast.Message(source_info, o.get_symbol('yourself'), []))
        return ast.Send(source_info, rcvr, ast.Cascade(source_info, messages))

    def parse_literal_array(self):
        source_info = self.current_token().source_info
        self.expect('lparray')
        elements = []
        while self.current_is_oneof('id', 'string', 'int', 'symbol', 'character'):
            v = self.current_token().value
            if self.current_is_oneof('character'):
                v = o.Character(v)
            elif self.current_is_oneof('symbol', 'id'):
                v = o.Symbol(v)
            elements.append(v)
            self.step()
        source_info += self.current_token().source_info
        self.expect('rpar')
        return ast.Const(source_info, o.Array(elements))

    def parse_primary(self):
        if self.current_is_oneof('string', 'int', 'symbol', 'character'):
            v = self.current_token().value
            si = self.current_token().source_info
            self.step()
            return ast.Const(si, v)
        elif self.current_is_oneof('id'):
            name = self.current_token().value
            si = self.current_token().source_info
            self.step()
            if name in ['true', 'false', 'nil']:
                return ast.Const.get(si, name)
            return ast.Ref(si, name)
        elif self.current_is_oneof('lpar'):
            return self.parse_nested_expr()
        elif self.current_is_oneof('lbarray'):
            return self.parse_byte_array()
        elif self.current_is_oneof('lparray'):
            return self.parse_literal_array()
        elif self.current_is_oneof('lsq'):
            return self.parse_block()
        elif self.current_is_oneof('lcurl'):
            return self.parse_expr_array()
        else:
            self.parse_error()

    def parse_umsg(self):
        selector = self.current_token().value
        source_info = self.current_token().source_info
        self.step()
        return self.make_message(source_info, selector, [])

    def parse_unary(self, r):
        while self.current_is_oneof('id'):
            message = self.parse_umsg()
            source_info = r.source_info + message.source_info
            r = ast.Send(source_info, r, message)
        return r

    def parse_bmsg(self):
        operator = self.current_token().value
        source_info = self.current_token().source_info
        self.step()
        arg = self.parse_primary()
        arg = self.parse_unary(arg)
        source_info += arg.source_info
        return self.make_message(source_info, operator, [arg])

    def parse_binary(self, r):
        while self.current_is_oneof('binsel'):
            message = self.parse_bmsg()
            source_info = r.source_info + message.source_info
            r = ast.Send(source_info, r, message)
        return r

    def parse_kmsg(self):
        source_info = self.current_token().source_info
        selector = []
        args = []

        while self.current_is_oneof('kw'):
            selector.append(self.current_token().value)
            self.step()

            arg = self.parse_primary()
            arg = self.parse_unary(arg)
            args.append(self.parse_binary(arg))
        selector = o.get_symbol(''.join(selector))
        source_info += args[-1].source_info
        return self.make_message(source_info, selector, args)

    def parse_keyword(self, r):
        if self.current_is_oneof('kw'):
            message = self.parse_kmsg()
            source_info = r.source_info + message.source_info
            r = ast.Send(source_info, r, message)
        return r

    def parse_cascade_message(self):
        if self.current_is_oneof('id'):
            return self.parse_umsg()
        elif self.current_is_oneof('binsel'):
            return self.parse_bmsg()
        elif self.current_is_oneof('kw'):
            return self.parse_kmsg()
        else:
            self.parse_error('Expected id, binsel, kw')

    def parse_cascade(self, r):
        if self.current_is_oneof('semi'):
            m = [r.message]
            r = r.receiver
            while self.current_is_oneof('semi'):
                self.step()
                m.append(self.parse_cascade_message())
            source_info = r.source_info + m[-1].source_info
            m_source_info = m[0].source_info + m[-1].source_info
            r = ast.Send(source_info, r, ast.Cascade(m_source_info, m))
        return r

    def parse_message(self):
        r = self.parse_primary()
        r = self.parse_unary(r)
        r = self.parse_binary(r)
        r = self.parse_keyword(r)
        r = self.parse_cascade(r)
        return r

    def parse_maybe_assignment(self):
        token = self.current_token()
        self.step()

        if self.current_is_oneof('assign'):
            self.step()
            expr = self.parse_expr()
            source_info = token.source_info + expr.source_info
            return ast.Assign(source_info, token.value, expr)
        self.push_token(token)
        return self.parse_message()

    def parse_expr(self):
        if self.current_is_oneof('lcurl', 'lpar', 'lbarray', 'lparray', 'lsq',
                                 'int', 'symbol', 'character', 'string'):
            return self.parse_message()
        elif self.current_is_oneof('id'):
            return self.parse_maybe_assignment()
        else:
            self.parse_error()

    def parse_vars(self):
        vars = []
        if self.current_token().matches(Token('binsel', '|')):
            self.step()
            while self.current_is_oneof('id'):
                vars.append(self.current_token().value)
                self.step()
            self.expect('binsel', '|')
        elif self.current_token().matches(Token('binsel', '||')):
            self.step()
        return vars

    def parse_method_header(self, method):
        if self.current_is_oneof('id'):
            name = self.current_token().value
            args = []
            self.step()
        elif self.current_is_oneof('binsel'):
            name = self.current_token().value
            self.step()
            if not self.current_is_oneof('id'):
                self.parse_error('expected id')
            args = [self.current_token().value]
            self.step()
        elif self.current_is_oneof('kw'):
            name = []
            args = []
            while self.current_is_oneof('kw'):
                name.append(self.current_token().value)
                self.step()
                if not self.current_is_oneof('id'):
                    self.parse_error('expected id')
                args.append(self.current_token().value)
                self.step()
            name = ''.join(name)
        else:
            self.parse_error('expected id, binsel, or keyword')
        method.update({'name': name, 'args': args})

    def parse_method(self, body):
        method = {}
        self.parse_method_header(method)
        self.expect('lsq')
        method['temps'], method['statements'] = self.parse_executable_code()
        self.expect('rsq')
        method = ast.Method(None, **method)
        methods = body.get('methods') or list()
        methods.append(method)
        body['methods'] = methods

    def parse_meta_element(self, meta):
        if self.current_is_oneof('id', 'binsel', 'kw'):
            self.parse_method(meta)
        else:
            self.parse_error('Expected id, binsel, or kw.')

    def parse_meta(self, body):
        self.expect('lsq')
        vars = self.parse_vars()
        meta = {'instance_vars': vars}
        while not self.current_is_oneof('rsq'):
            self.parse_meta_element(meta)
        self.expect('rsq')
        body['meta'] = ast.Meta(None, **meta)

    def parse_trait_clause(self):
        expr = self.parse_expr()
        self.expect('dot')
        source_info = expr.source_info
        receiver = ast.Ref(source_info, o.get_symbol('Trait'))
        message = ast.Message(source_info, o.get_symbol('build:'), [expr])
        expr = ast.Send(source_info, receiver, message)
        return expr

    def parse_decl_element(self, body):
        if self.current_is_oneof('id'):
            token = self.current_token()
            self.step()

            if self.current_is_oneof('lsq'):
                self.push_token(token)
                self.parse_method(body)
            elif self.current_token().matches(Token('kw', 'uses:')):
                if token.value != body.get('name'):
                    self.parse_error('Trait clause name does not match')
                self.step()
                body['trait_expr'] = self.parse_trait_clause()
            elif self.current_token().matches(Token('id', 'class')):
                if token.value != body.get('name'):
                    parse_error("Meta name doesn't match")
                self.step()
                self.parse_meta(body)
            else:
                self.parse_error('Expected "[" or "uses:" or "class"')
        elif self.current_is_oneof('kw', 'binsel'):
            self.parse_method(body)
        else:
            self.parse_error('Expected id, binsel, or kw.')

    def parse_decl_body(self, body, skip_ivars=False):
        self.expect('lsq')
        if not skip_ivars:
            body['instance_vars'] = self.parse_vars()
        while not self.current_is_oneof('rsq'):
            self.parse_decl_element(body)
        self.expect('rsq')
        return body

    def parse_class(self):
        superclass_name = self.current_token().value
        self.step()
        self.expect('kw', 'subclass:')
        class_name = self.current_token().value
        self.step()
        body = {
            'name': class_name,
            'superclass_name': superclass_name,
            'meta': None,
            'trait_expr': None,
            'methods': []
        }
        self.parse_decl_body(body)
        if not body['meta']:
            body['meta'] = ast.Meta(None, methods=[], instance_vars=[])
        return ast.Class(None, **body)

    def parse_trait(self):
        self.expect('id', 'Trait')
        self.expect('kw', 'named:')
        # XXX: check for id
        trait_name = self.current_token().value
        self.step()
        body = {
            'name': trait_name,
            'trait_expr': None,
            'meta': None
        }
        self.parse_decl_body(body, skip_ivars=True)
        return ast.Trait(None, **body)

    def parse_module_expr(self):
        expr = self.parse_expr()
        if not self.current_is_oneof('eof'):
            self.expect('dot')
        return expr

    def parse_module_name(self):
        start = self.current_token().source_info
        self.expect('lpmod')
        name = []
        while True:
            if not self.current_is_oneof('id'):
                self.parse_error('expected id')

            name.append(self.current_token().value)
            self.step()

            if self.current_token().matches(Token('rcurl', '}')):
                si = start + self.current_token().source_info
                self.step()
                return ast.ModuleName(si, '.'.join(name))

            self.expect('dot')

    def parse_import(self):
        start = self.current_token().source_info
        self.expect('kw', 'import:')
        name = self.parse_module_name()
        return ast.ModuleImport(start + name.source_info, name)

    def parse_module_element(self):
        if self.current_token().matches(Token('kw', 'import:')):
            return self.parse_import()
        elif self.current_token().matches(Token('id', 'Trait')):
            return self.parse_trait()
        elif self.current_is_oneof('id'):
            id = self.current_token()
            self.step()
            if self.current_token().matches(Token('kw', 'subclass:')):
                self.push_token(id)
                return self.parse_class()
            self.push_token(id)
        return self.parse_module_expr()

    def parse_module(self):
        exprs = []
        source_info = self.current_token().source_info
        while not self.current_is_oneof('eof'):
            exprs.append(self.parse_module_element())
        source_info += self.current_token().source_info
        return ast.Seq(source_info, exprs)
