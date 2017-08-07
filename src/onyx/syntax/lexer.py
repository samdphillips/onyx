
import re

from collections import namedtuple

Token = namedtuple('Token', 'type value')
EmptyMatch = namedtuple('EmptyMatch', 'is_success')(False)


class Match:
    is_success = True

    def __init__(self, scanner, re_match):
        self.scanner = scanner
        self.re_match = re_match

    def scan(self, lexer):
        return self.scanner.scan(lexer, self.re_match)


class Scanner:
    def __init__(self, pattern, token_type, convert=str, scan_func=None):
        self.re = re.compile(pattern)
        self.token_type = token_type
        self.convert = convert
        self.scan_func = scan_func

    def match(self, s):
        m = self.re.match(s)
        if m:
            return Match(self, m)
        return EmptyMatch

    def make_token(self, sval):
        return Token(self.token_type, self.convert(sval))

    def scan(self, lexer, match):
        if self.scan_func is None:
            sval = match.group()
            size = len(sval)
            lexer.advance_buffer(size)
            return self.make_token(sval)

class Lexer:
    scanners = [
        Scanner(r'\s+', 'whitespace')
    ]

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
        matches.sort()
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

    def lex_token(self):
        self.fill_buffer()
        return self.scan_token()
