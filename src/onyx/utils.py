
import attr


@attr.s
class Continue:
    vm = attr.ib()
    value = attr.ib()
    stack = attr.ib()


@attr.s
class MessageSend:
    vm = attr.ib()
    receiver = attr.ib()
    selector = attr.ib()
    args = attr.ib()


@attr.s
class MethodInvoke:
    vm = attr.ib()
    klass = attr.ib()
    receiver = attr.ib()
    method = attr.ib()


@attr.s
class PrimitiveSend:
    vm = attr.ib()
    receiver = attr.ib()
    selector = attr.ib()
    args = attr.ib()

@attr.s
class Step:
    vm = attr.ib()
    node = attr.ib()


@attr.s
class Subscription:
    event_spec = attr.ib()
    action = attr.ib()

    def wants(self, event_cls):
        return any((issubclass(event_cls, s) for s in self.event_spec))

    def announce(self, event):
        self.action(event)


@attr.s
class Announcer:
    subscriptions = attr.ib(factory=list)

    def wants(self, event_cls):
        return any((s.wants(event_cls) for s in self.subscriptions))

    def listen_for(self, event_spec, action):
        if type(event_spec) != list:
            event_spec = [event_spec]
        event_spec = list(event_spec)
        sub = Subscription(event_spec, action)
        self.subscriptions.append(sub)

    def announce(self, event):
        for s in self.subscriptions:
            if s.wants(event.__class__):
                s.announce(event)


@attr.s
class Tally:
    counts = attr.ib(init=False, factory=dict)

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
