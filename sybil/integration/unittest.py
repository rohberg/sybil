from typing import TYPE_CHECKING
from unittest import TestCase as BaseTestCase, TestSuite

if TYPE_CHECKING:
    from ..sybil import Sybil


class TestCase(BaseTestCase):

    sybil = namespace = None

    def __init__(self, example):
        BaseTestCase.__init__(self)
        self.example = example

    def runTest(self):
        self.setupNamespace()
        self.example.evaluate()
        self.tearDownNamespace()

    def id(self):
        return f"{self.example.path},line:{self.example.line},column:{self.example.column}"

    __str__ = __repr__ = id

    # @classmethod
    # def setUpClass(self):
    def setupNamespace(self):
        if self.sybil.setup is not None:
            self.sybil.setup(self.namespace)
        self.namespace['self'] = self

    # @classmethod
    # def tearDownClass(self):
    def tearDownNamespace(self):
        if self.sybil.teardown is not None:
            self.sybil.teardown(self.namespace)


def unittest_integration(sybil: 'Sybil'):

    def load_tests(loader=None, tests=None, pattern=None):
        suite = TestSuite()
        for path in sorted(sybil.path.glob('**/*')):
            if path.is_file() and sybil.should_parse(path):
                document = sybil.parse(path)

                case = type(document.path, (TestCase, ), dict(
                    sybil=sybil, namespace=document.namespace,
                ))

                for example in document:
                    suite.addTest(case(example))

        return suite

    return load_tests
