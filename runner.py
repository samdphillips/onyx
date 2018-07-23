
import attr
import sys
import onyx.utils as u
from onyx.vm.interpreter import Interpreter


@attr.s
class Profiler:
    cur_method = attr.ib(default=None)
    tally = attr.ib(factory=dict)

    def on_message_send(self, event):
        print(event)


vm = Interpreter()
prof = Profiler()
vm.listen_for(u.MessageSend, prof.on_message_send)
vm.run_script(sys.argv[1])
