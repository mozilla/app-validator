import sys
import types

from nose import SkipTest
from nose.tools import eq_

from .. import helper
from ..helper import MockXPI
from appvalidator.constants import SPIDERMONKEY_INSTALLATION
from appvalidator.errorbundle import ErrorBundle
from appvalidator.errorbundle.outputhandlers.shellcolors import OutputHandler
import appvalidator.testcases.content
import appvalidator.testcases.scripting as scripting

scripting.traverser.DEBUG = True


def uses_js(func):
    if SPIDERMONKEY_INSTALLATION is None:
        raise SkipTest("Not running JS tests.")

    if func:
        try:
            setattr(func, "js", True)
        except Exception:
            # If Python >2.7 squaks about methods being bound, just work around
            # the nonsense.
            setattr(func.__func__, "js", True)

    return func


class TestCase(helper.TestCase):
    """A TestCase object with specialized functions for JS testing."""

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        for method in filter(callable, (getattr(self, m) for m in dir(self))):
            if not method.__name__.startswith("test_"):
                continue
            uses_js(method)

        uses_js(None)

    def setUp(self):
        self.file_path = "foo.js"
        self.final_context = None
        super(TestCase, self).setUp()

    def run_script_from_file(self, path):
        """
        Run the standard set of JS engine tests on a script found at the
        location in `path`.
        """
        with open(path) as script_file:
            return self.run_script(script_file.read())

    def run_script(self, script):
        """
        Run the standard set of JS engine tests on the script passed via
        `script`.
        """
        if self.err is None:
            self.setup_err()

        appvalidator.testcases.content._process_file(self.err, MockXPI(),
                                                     self.file_path, script)
        if self.err.final_context is not None:
            print self.err.final_context.output()
            self.final_context = self.err.final_context

    def get_var(self, name):
        """
        Return the value of a variable from the final script context.
        """
        try:
            return self.final_context.data[name].get_literal_value()
        except KeyError:
            raise ("Test seeking variable (%s) not found in final context." %
                       name)

    def assert_var_eq(self, name, value, explanation=None):
        """
        Assert that the value of a variable from the final script context
        contains the value specified.
        """
        val = self.get_var(name)
        if isinstance(val, float):
            val *= 100000
            val = round(val)
            val /= 100000

        eq_(val, value,
            explanation or "%r doesn't equal %r" % (val, value))
