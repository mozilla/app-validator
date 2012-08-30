from nose.tools import eq_

from js_helper import TestCase

from appvalidator.testcases.javascript.actions import _get_as_num
from appvalidator.testcases.javascript.jstypes import JSWrapper


class TestSyntax(TestCase):

    def test_array_destructuring(self):
        """
        Make sure that multi-level and prototype array destructuring don't cause
        tracebacks.
        """

        def test(self, script):
            self.setUp()
            self.run_script(script)
            self.assert_silent()

        yield test, self, '[a, b, c, d] = [1, 2, 3, 4]; [] = bar();'
        yield test, self, 'function foo(x, y, [a, b, c], z) { bar(); }'

    def test_get_as_num(self):
        """Test that `_get_as_num` parses literals properly."""

        def test(input, output):
            eq_(_get_as_num(input), output)

        yield test, 1, 1
        yield test, 1.0, 1.0
        yield test, "1", 1
        yield test, "1.0", 1.0
        yield test, None, 0
        yield test, "0xF", 15
        yield test, True, 1
        yield test, False, 0

        yield test, JSWrapper(1), 1
        yield test, JSWrapper(1.0), 1.0
        yield test, JSWrapper("1"), 1
        yield test, JSWrapper("1.0"), 1.0
        yield test, JSWrapper(None), 0
