
import pytest

@pytest.fixture
def vm():
    from onyx.vm.interpreter import Interpreter
    vm = Interpreter.boot()
    return vm

def pytest_collect_file(parent, path):
    if path.ext == ".ost" and path.basename.startswith("test"):
        return OnyxTestFile(path, parent)

class OnyxTestFile(pytest.File):
    def collect(self):
        from onyx.syntax.parser import Parser
        from onyx.syntax.ast import Seq
        interpreter = vm()
        tester = Parser.parse_file("src/ost/tests/tester.ost")
        test_case_code = Parser.parse_file(self.fspath.strpath)
        test_case = interpreter.eval(Seq(test_case_code.source_info,
                                         [tester, test_case_code]))
        interpreter.globals.lookup('testCase').assign(test_case)
        num_tests = interpreter.eval_string('testCase numTests')
        for i in range(num_tests):
            name = interpreter.eval_string('testCase testName: %d' % i)
            yield OnyxTest('{}::{}'.format(self.fspath.strpath, name),
                           self, interpreter, i)

class OnyxTest(pytest.Item):
    def __init__(self, name, parent, vm, test_number):
        super(OnyxTest, self).__init__(name, parent)
        self.vm = vm
        self.test_number = test_number

    def runtest(self):
        import onyx.objects as o
        result = self.vm.eval_string('testCase runTest: %d' % self.test_number)
        assert result == o.true
