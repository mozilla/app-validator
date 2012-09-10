from nose.tools import eq_

from js_helper import TestCase


class TestDuplicates(TestCase):
    def test_no_dups(self):
        """Test that errors are not duplicated."""

        def test(self, script, message_count):
            self.setUp()
            self.run_script(script)
            if not message_count:
                self.assert_silent()
            else:
                self.assert_failed(with_warnings=True)
                eq_(self.err.message_count, message_count)

        yield test, self, 'eval("test");', 1
        yield test, self, 'var x = eval();', 1
        yield test, self, 'eval = 123;', 0
        yield test, self, 'eval.prototype = true;', 1
