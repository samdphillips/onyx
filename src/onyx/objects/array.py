
class Array(list):
    is_class = False

    def onyx_class(self, vm):
        return vm.globals.lookup('Array').value
