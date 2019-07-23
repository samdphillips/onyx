

class Base:
    DEBUG_FMT = "<{0.__class__.__name__}> {0}"

    def onyx_class(self, vm):
        name = self.__class__.__name__.lstrip('_')
        return vm.core_lookup(name)

    def deref(self):
        return self

    def debug(self, _):
        print(self.DEBUG_FMT.format(self))
