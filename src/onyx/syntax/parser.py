
import onyx.syntax.ast as ast


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

    def make_message(self, selector, args=[]):
        msg_class = ast.Message
        if selector.startswith('_'):
            msg_class = ast.PrimitiveMessage
        return msg_class(selector, args)

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

    def parse_keyword(self, r):
        return r

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
        if self.current_is_oneof('lcurl', 'lpar', 'lparray', 'lsq', 'int', 'symbol', 'character', 'string'):
            return self.parse_message()
        elif self.current_is_oneof('id'):
            return self.parse_maybe_assignment()
        else:
            self.parse_error()
