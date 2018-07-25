
import attr
import sys
import onyx.utils as u
from onyx.vm.interpreter import Interpreter


@attr.s
class Profiler:
    tally = attr.ib(factory=dict)
    invokes = attr.ib(factory=dict)
    bill = object()

    def save_method(self, vm, k):
        marks = vm.marks
        marks[self.bill] = marks.get(self.bill, []) + [k]

    def get_active_methods(self, vm):
        v = []
        if self.bill in vm.marks:
            v.append(vm.marks[self.bill])
        v += vm.stack.find_marks(self.bill, None)
        return v

    def on_method_invoke(self, event):
        klass = event.klass
        name = event.method.name
        k = (klass.name, event.method.name)
        self.invokes[k] = self.invokes.get(k, 0) + 1
        self.save_method(event.vm, k)

    def on_step(self, event):
        frames = self.get_active_methods(event.vm)
        for ks in frames:
            for k in ks:
                self.tally[k] = self.tally.get(k, 0) + 1


vm = Interpreter()
prof = Profiler()
vm.listen_for(u.MethodInvoke, prof.on_method_invoke)
vm.listen_for(u.Step, prof.on_step)
vm.run_script(sys.argv[1])

c = reversed(sorted([(v,k) for k,v in prof.tally.items()]))
for count, name in c:
    if name[0] != 'BlockClosure':
        r = float(count) / prof.invokes[name]
        print('{0:>10} {1:>10} {2:>10.2f} {3}'.format(count, prof.invokes[name], r, name))

