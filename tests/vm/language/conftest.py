
import pytest

@pytest.fixture
def vm():
    from onyx.vm.interpreter import Interpreter
    return Interpreter()

def pytest_collect_file(parent, path):
    if path.ext == ".ost" and path.basename.startswith("test"):
        return OnyxTestFile(path, parent)

class OnyxTestFile(pytest.File):
    def load_syntax(self):
        from onyx.syntax.parser import Parser
        import onyx.objects as o
        import onyx.syntax.ast as ast
        syntax = Parser.parse_file(self.fspath.strpath)
        tester_name = ast.ModuleName(None, o.get_symbol('tests.tester'))
        tester_imp = ast.ModuleImport(None, tester_name)
        assign = ast.Assign(None, o.get_symbol('testCase'), syntax)
        return ast.Seq(None, [tester_imp, assign])

    def collect(self):
        syntax = self.load_syntax()
        ns = '<<{}>>'.format(self.fspath.basename)
        interpreter = vm()
        interpreter.module_loader.visit(ns, syntax)
        interpreter.module_loader.instantiate(ns)
        num_tests = interpreter.eval_string('testCase numTests', require=[ns])
        for i in range(num_tests):
            name = interpreter.eval_string(
                'testCase testName: %d' % i, require=[ns]
            )
            yield OnyxTest('{}::{}'.format(self.fspath.strpath, name),
                           self, interpreter, ns, i)

class OnyxTest(pytest.Item):
    def __init__(self, name, parent, vm, ns, test_number):
        super(OnyxTest, self).__init__(name, parent)
        self.vm = vm
        self.ns = ns
        self.test_number = test_number

    def runtest(self):
        import onyx.objects as o
        result = self.vm.eval_string(
            'testCase runTest: %d' % self.test_number, require=[self.ns]
        )
        assert result == True
