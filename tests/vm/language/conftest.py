
import pytest

def pytest_collect_file(parent, path):
    if parent.config.getoption('--skip-ost'):
        return

    if path.ext == ".ost" and path.basename.startswith("test"):
        return OnyxTestFile(path, parent)


@pytest.fixture
def vm():
    from onyx.vm.interpreter import Interpreter
    return Interpreter()

class OnyxTestFile(pytest.File):
    def load_syntax(self):
        from onyx.syntax.parser import Parser
        import onyx.objects as o
        import onyx.syntax.ast as ast
        mod_syntax = Parser.parse_file(self.fspath.strpath)
        imports = mod_syntax.imports
        syntax = mod_syntax.body
        tester_name = o.get_symbol('tests.tester')
        tester_imp = ast.ModuleImport(None, tester_name)
        imports.append(tester_imp)
        syntax = ast.Assign(None, o.get_symbol('testCase'), syntax)
        return ast.Module(None, imports, syntax)

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
