
import attr
import re

from collections import namedtuple
from operator import methodcaller

import onyx.objects as o


EmptyMatch = namedtuple('EmptyMatch', 'is_success')(False)

# XXX: InvalidInput
# XXX: AmbiguousToken

@attr.s
class FileSource:
    file_name = attr.ib()
    file = attr.ib(default=None)

    def name(self):
        return self.file_name

    def __getitem__(self, index):
        if not self.file:
            self.file = open(self.file_name, 'r')
        else:
            self.file.seek(0)

        self.file.seek(index.start)
        data = self.file.read(index.stop - index.start)
        return data


@attr.s
class SourceInfo:
    source = attr.ib()
    start = attr.ib(validator=attr.validators.instance_of(int))
    end = attr.ib(validator=attr.validators.instance_of(int))

    @end.validator
    def check(self, attribute, value):
        if value < self.start:
            raise ValueError('end is less than start')

    def __add__(self, other):
        assert self.source == other.source
        return SourceInfo(self.source, self.start, other.end)

    def source_name(self):
        if isinstance(self.source, str):
            return '<<string>>'
        else:
            return self.source.name()

    def source_text(self):
        return self.source[self.start:self.end]

    def __format__(self, format_spec):
        return '{}\n    {}'.format(self.source_name(), self.source_text())


@attr.s
class Token:
    type = attr.ib(validator=attr.validators.instance_of(str))
    value = attr.ib()
    source_info = attr.ib(default=None)

    def matches(self, other):
        return self.type == other.type and self.value == other.value


def extract_group(n):
    def _extract(match):
        return match.group(n)
    return _extract


def make_character(match):
    return o.get_character(ord(match.group(1)))


def make_symbol(match):
    return o.get_symbol(match.group(1))


def convert_int(match):
    return int(match.group().replace('_', ''))


def convert_nrm_int(match):
    sign = match.group(1) or '+'
    if sign == '+':
        sign = 1
    else:
        sign = -1

    base = int(match.group(2))
    number = match.group(3).replace('_', '')
    return int(number, base=base) * sign


def scan_string(scanner, lexer):
    start = lexer.position
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
            end = lexer.position
            source_info = SourceInfo(lexer.source, start, end)
            return scanner.make_token(''.join(s), source_info)


@attr.s
class Match:
    scanner = attr.ib()
    re_match = attr.ib()
    is_success = True

    def scan(self, lexer):
        return self.scanner.scan(lexer, self.re_match)

    def score(self):
        return len(self.re_match.group())


@attr.s
class Scanner:
    pattern = attr.ib(converter=re.compile)
    token_type = attr.ib(validator=attr.validators.instance_of(str))
    convert = attr.ib(default=extract_group(0))
    scan_func = attr.ib(default=None)

    def match(self, s):
        m = self.pattern.match(s)
        if m:
            return Match(self, m)
        return EmptyMatch

    def make_token(self, val, source_info):
        return Token(self.token_type, val, source_info)

    def make_source_info(self, lexer, size):
        pos = lexer.position
        return SourceInfo(lexer.source, pos, pos + size)

    def scan(self, lexer, match):
        if self.scan_func is None:
            size = len(match.group())
            source_info = self.make_source_info(lexer, size)
            lexer.advance_buffer(size)
            val = self.convert(match)
            return self.make_token(val, source_info)
        return self.scan_func(self, lexer)


class Lexer:
    scanners = [
        Scanner(r'\s+', 'whitespace'),
        Scanner(r'"([^"]*)"', 'comment', extract_group(1)),
        Scanner(r'([a-zA-Z_][a-zA-Z0-9]*)', 'id', make_symbol),
        Scanner(r':([a-zA-Z_][a-zA-Z0-9]*)', 'blockarg', extract_group(1)),
        Scanner(r'([a-zA-Z_][a-zA-Z0-9]*:)', 'kw', make_symbol),
        Scanner(r'[+-]?[0-9_]+', 'int', convert_int),
        Scanner(r'([+-]?)([2-9]|[12][0-9]|3[0-6])r([0-9a-zA-Z_]+)', 'int', convert_nrm_int),
        Scanner(r'([`~!@%&*+=|\\?/<>,-]+)', 'binsel', make_symbol),
        Scanner(r'\$(.)', 'character', make_character),
        Scanner(r'#([a-zA-Z_][a-zA-Z0-9]*)', 'symbol', make_symbol),
        Scanner(r'#([`~!@%&*+=|\\?/<>,-]+)', 'symbol', make_symbol),
        Scanner(r'#(([a-zA-Z_][a-zA-Z0-9]*:)+)', 'symbol', make_symbol),
        Scanner(r"#'([^']+)'", 'symbol', make_symbol),
        Scanner(r"#\[", 'lbarray'),
        Scanner(r"#\(", 'lparray'),
        Scanner(r"#{", 'lpmod'),
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

    @classmethod
    def from_file(cls, file_name):
        f = open(file_name, 'r')
        return cls(FileSource(file_name), f)

    def __init__(self, source, inp):
        self.source = source
        self.inp = inp
        self.buf = ''
        self.position = 0
        self.fill_buffer()

    def close(self):
        return self.inp.close()

    def buffer_at_end(self):
        return self.buf == ''

    def fill_buffer(self, fill_size=1024):
        size = fill_size - len(self.buf)
        if size > 0:
            self.buf += self.inp.read(size)

    def advance_buffer(self, size):
        self.position += size
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
        size = 1024
        while size < 10000:
            matches = self.scan_matches()
            if len(matches) == 0:
                size *= 2
                self.fill_buffer(size)
            else:
                m = self.best_scan_match(matches)
                return m.scan(self)
        self.invalid_input()

    def raw_lex_token(self):
        self.fill_buffer()
        if self.buffer_at_end():
            return Token('eof', None,
                         SourceInfo(self.source, self.position, self.position))
        return self.scan_token()

    def lex_token(self):
        while True:
            token = self.raw_lex_token()
            if token.type not in self.skip_tokens:
                return token
