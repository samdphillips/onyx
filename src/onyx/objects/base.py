

DEBUG_FMT = "<{0.__class__.__name__}> {0}"

class Base:
    is_class = False

    def onyx_class(self, vm):
        name = self.__class__.__name__.lstrip('_')
        return vm.core_lookup(name)

    def deref(self):
        return self

    def debug(self):
        print(DEBUG_FMT.format(self))
