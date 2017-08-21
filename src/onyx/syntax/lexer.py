
import re

from collections import namedtuple
from operator import methodcaller

import onyx.objects as o

Token = namedtuple('Token', 'type value')
EmptyMatch = namedtuple('EmptyMatch', 'is_success')(False)

# XXX: InvalidInput
# XXX: AmbiguousToken


def extract_group(n):
    def _extract(match):
        return match.group(n)
    return _extract


def make_character(match):
    return o.Character(ord(match.group(1)))


def make_symbol(match):
    return o.get_symbol(match.group(1))


def convert_int(match):
    return o.SmallInt(match.group())


def scan_string(scanner, lexer):
    j = 1
    s = []
    while True:
        while lexer.buf[j] != "'":
            j += 1
        s.append(lexer.buf[1:j])
        lexer.advance_buffer(j)
        lexer.fill_buffer()
        j = 1
        if len(lexer.buf) > 1 and lexer.buf[1] == "'":
            s.append("'")
            lexer.advance_buffer(1)
            j = 1
        else:
            lexer.advance_buffer(1)
            return scanner.make_token(o.String(''.join(s)))


class Match:
    is_success = True

    def __init__(self, scanner, re_match):
        self.scanner = scanner
        self.re_match = re_match

    def scan(self, lexer):
        return self.scanner.scan(lexer, self.re_match)

    def score(self):
        return len(self.re_match.group())


class Scanner:
    def __init__(self, pattern, token_type, convert=None, scan_func=None):
        self.re = re.compile(pattern)
        self.token_type = token_type
        self.convert = convert or extract_group(0)
        self.scan_func = scan_func

    def match(self, s):
        m = self.re.match(s)
        if m:
            return Match(self, m)
        return EmptyMatch

    def make_token(self, val):
        return Token(self.token_type, val)

    def scan(self, lexer, match):
        if self.scan_func is None:
            size = len(match.group())
            lexer.advance_buffer(size)
            val = self.convert(match)
            return self.make_token(val)
        return self.scan_func(self, lexer)


class Lexer:
    scanners = [
        Scanner(r'\s+', 'whitespace'),
        Scanner(r'"([^"]*)"', 'comment', extract_group(1)),
        Scanner(r'([a-zA-Z_][a-zA-Z0-9]*)', 'id', make_symbol),
        Scanner(r':([a-zA-Z_][a-zA-Z0-9]*)', 'blockarg', extract_group(1)),
        Scanner(r'[a-zA-Z_][a-zA-Z0-9]*:', 'kw'),
        Scanner(r'[+-]?\d+', 'int', convert_int),
        Scanner(r'[`~!@%&*+=|\\?/<>,-]+', 'binsel'),
        Scanner(r'\$(.)', 'character', make_character),
        Scanner(r'#([a-zA-Z_][a-zA-Z0-9]*)', 'symbol', make_symbol),
        Scanner(r'#([`~!@%&*+=|\\?/<>,-]+)', 'symbol', make_symbol),
        Scanner(r'#(([a-zA-Z_][a-zA-Z0-9]*:)+)', 'symbol', make_symbol),
        Scanner(r"#'([^']+)'", 'symbol', make_symbol),
        Scanner(r"#\(", 'lparray'),
        Scanner(r"'", 'string', None, scan_string),
        Scanner(r'\^', 'caret'),
        Scanner(r';', 'semi'),
        Scanner(r':=', 'assign'),
        Scanner(r'\.', 'dot'),
        Scanner(r'\(', 'lpar'),
        Scanner(r'\)', 'rpar'),
        Scanner(r'{', 'lcurl'),
        Scanner(r'}', 'rcurl'),
        Scanner(r'\[', 'lsq'),
        Scanner(r']', 'rsq')
    ]

    skip_tokens = 'whitespace comment'.split()

    def __init__(self, inp):
        self.inp = inp
        self.buf = ''
        self.fill_buffer()

    def buffer_at_end(self):
        return self.buf == ''

    def fill_buffer(self):
        size = 1024 - len(self.buf)
        self.buf += self.inp.read(size)

    def advance_buffer(self, size):
        self.buf = self.buf[size:]

    def scan_matches(self):
        matches = []
        for s in self.scanners:
            m = s.match(self.buf)
            if m.is_success:
                matches.append(m)
        return matches

    def best_scan_match(self, matches):
        matches.sort(key=methodcaller('score'), reverse=True)
        if len(matches) > 1:
            a = matches[0]
            b = matches[1]
            if a.score() == b.score():
                self.ambiguous_token(a, b)
        return matches[0]

    def scan_token(self):
        matches = self.scan_matches()
        if len(matches) == 0:
            self.invalid_input()
        m = self.best_scan_match(matches)
        return m.scan(self)

    def raw_lex_token(self):
        self.fill_buffer()
        if self.buffer_at_end():
            return Token('eof', None)
        return self.scan_token()

    def lex_token(self):
        while True:
            token = self.raw_lex_token()
            if token.type not in self.skip_tokens:
                return token
