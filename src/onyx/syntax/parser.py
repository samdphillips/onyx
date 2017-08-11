
import onyx.syntax.ast as ast

from onyx.syntax.lexer import Token


class ParseError(Exception):
    def __init__(self, actual, expected, buffer):
        self.actual = actual
        self.expected = expected
        self.buffer = buffer

class Parser:
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

    def make_message(self, selector, args=[]):
        msg_class = ast.Message
        if selector.startswith('_'):
            msg_class = ast.PrimitiveMessage
        return msg_class(selector, args)

    def parse_nested_expr(self):
        self.expect('lpar')
        expr = self.parse_expr()
        self.expect('rpar')
        return expr

    def parse_return(self):
        self.expect('caret')
        return ast.Return(self.parse_expr())

    def parse_statement(self):
        if self.current_is_oneof('caret'):
            return self.parse_return()
        elif self.current_is_oneof('string', 'int', 'symbol', 'id', 'lpar', 'lcurl', 'lparray', 'lsq'):
            return self.parse_expr()
        else:
            self.parse_error('expected expr')

    def parse_statements(self):
        stmts = []
        while True:
            if self.current_is_oneof('caret', 'int', 'string', 'symbol', 'id',
                                     'lpar', 'lcurl', 'lparray', 'lsq'):
                stmts.append(self.parse_statement())
            else:
                break

            if self.current_is_oneof('dot'):
                self.step()
            else:
                break
        return stmts

    def parse_executable_code(self, body):
        body['temps'] = self.parse_vars()
        body['statements'] = ast.Seq(self.parse_statements())

    def parse_block(self):
        self.expect('lsq')
        args = []
        if self.current_is_oneof('blockarg'):
            while self.current_is_oneof('blockarg'):
                args.append(self.current_token().value)
                self.step()
            if self.current_token() == Token('binsel', '|'):
                self.step()
            elif self.current_token() == Token('binsel', '||'):
                self.step()
                self.push_token(Token('binsel', '|'))
            else:
                self.parse_error('Expected "|"')

        block = {'args': args}
        self.parse_executable_code(block)
        self.expect('rsq')
        return ast.Block(**block)

    def parse_primary(self):
        if self.current_is_oneof('string', 'int', 'symbol', 'character'):
            v = self.current_token().value
            self.step()
            return ast.Const(v)
        elif self.current_is_oneof('id'):
            name = self.current_token().value
            self.step()
            if name in ['true', 'false', 'nil']:
                return ast.Const.get(name)
            return ast.Ref(name)
        elif self.current_is_oneof('lpar'):
            return self.parse_nested_expr()
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
        self.step()
        return self.make_message(selector, [])

    def parse_unary(self, r):
        while self.current_is_oneof('id'):
            r = ast.Send(r, self.parse_umsg())
        return r

    def parse_bmsg(self):
        operator = self.current_token().value
        self.step()
        arg = self.parse_primary()
        arg = self.parse_unary(arg)
        return self.make_message(operator, [arg])

    def parse_binary(self, r):
        while self.current_is_oneof('binsel'):
            r = ast.Send(r, self.parse_bmsg())
        return r

    def parse_kmsg(self):
        selector = []
        args = []

        while self.current_is_oneof('kw'):
            selector.append(self.current_token().value)
            self.step()

            arg = self.parse_primary()
            arg = self.parse_unary(arg)
            args.append(self.parse_binary(arg))
        selector = ''.join(selector)
        return self.make_message(selector, args)

    def parse_keyword(self, r):
        if self.current_is_oneof('kw'):
            r = ast.Send(r, self.parse_kmsg())
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
            r = ast.Cascade(r, m)
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
            return ast.Assign(token.value, expr)
        self.push_token(token)
        return self.parse_message()

    def parse_expr(self):
        if self.current_is_oneof('lcurl', 'lpar', 'lparray', 'lsq', 'int',
                                 'symbol', 'character', 'string'):
            return self.parse_message()
        elif self.current_is_oneof('id'):
            return self.parse_maybe_assignment()
        else:
            self.parse_error()

    def parse_vars(self):
        vars = []
        if self.current_token() == Token('binsel', '|'):
            self.step()
            while self.current_is_oneof('id'):
                vars.append(self.current_token().value)
                self.step()
            self.expect('binsel', '|')
        elif self.current_token() == Token('binsel', '||'):
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
        self.parse_executable_code(method)
        self.expect('rsq')
        method = ast.Method(**method)
        methods = body.get('methods') or dict()
        methods[method.name] = method
        body['methods'] = methods

    def parse_meta_element(self, meta):
        if self.current_is_oneof('id', 'binsel', 'kw'):
            self.parse_method(meta)
        else:
            self.parse_error('Expected id, binsel, or kw.')

    def parse_meta(self, body):
        self.expect('lsq')
        vars = self.parse_vars()
        meta = {'vars': vars}
        while not self.current_is_oneof('rsq'):
            self.parse_meta_element(meta)
        self.expect('rsq')
        body['meta'] = meta

    def parse_decl_element(self, body):
        if self.current_is_oneof('id'):
            token = self.current_token()
            self.step()

            if self.current_is_oneof('lsq'):
                self.push_token(token)
                self.parse_method(body)
            elif self.current_token() == Token('kw', 'uses:'):
                if token.value != body.get('name'):
                    self.parse_error('Trait clause name does not match')
                self.step()
                self.parse_trait_clause(body)
            elif self.current_token() == Token('id', 'class'):
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

    def parse_decl_body(self, body):
        self.expect('lsq')
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
            'trait_expr': None
        }
        self.parse_decl_body(body)
        return ast.Class(**body)

    def parse_module_element(self):
        if self.current_token() == Token('kw', 'import:'):
            return self.parse_import()
        elif self.current_token() == Token('id', 'Trait'):
            return self.parse_trait()
        elif self.current_is_oneof('id'):
            id = self.current_token()
            self.step()
            if self.current_token() == Token('kw', 'subclass:'):
                self.push_token(id)
                return self.parse_class()
            self.push_token(id)
        return self.parse_module_expr()

    def parse_module(self):
        exprs = []
        while not self.current_is_oneof('eof'):
            exprs.append(self.parse_module_element())
        return ast.Seq(exprs)
