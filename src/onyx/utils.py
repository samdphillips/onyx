

@attr.s
class Tally:
    counts = attr.ib(init=None, default=attr.Factory(dict))

    def tally(self, tag):
        self.counts[tag] = self.counts.get(tag, 0) + 1

    def report(self, n=20):
        c = reversed(sorted([(v, k) for k, v in self.counts.items()]))
        for _, x in zip(range(n), c):
            print(x)


def camel_to_snake(name):
    s = name[0].lower()
    for c in name[1:]:
        if c.isupper():
            s += "_" + c.lower()
        elif c == ':':
            s += "_"
        else:
            s += c
    return s
