import doctest

from . import models

def load_tests(loader, tests, pattern):
    tests.addTests(doctest.DocTestSuite(models))
    return tests
