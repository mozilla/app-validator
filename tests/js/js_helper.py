import sys

from nose.tools import eq_

from .. import helper
from ..helper import MockXPI
from appvalidator.errorbundler import ErrorBundle
from appvalidator.outputhandlers.shellcolors import OutputHandler
import appvalidator.testcases.content
import appvalidator.testcases.scripting
appvalidator.testcases.scripting.traverser.DEBUG = True


def _do_test_raw(script, path="foo.js"):
    "Performs a test on a JS file"

    err = ErrorBundle(instant=True)
    err.handler = OutputHandler(sys.stdout, True)

    appvalidator.testcases.content._process_file(err, MockXPI(), path, script)
    if err.final_context is not None:
        print err.final_context.output()

    return err


def _get_var(err, name):
    return err.final_context.data[name].get_literal_value()


def _do_test_scope(script, vars):
    """Test the final scope of a script against a set of variables."""
    scope = _do_test_raw(script)
    for var, value in vars.items():
        print "Testing %s" % var
        var_val = _get_var(scope, var)
        if isinstance(var_val, float):
            var_val *= 100000
            var_val = round(var_val)
            var_val /= 100000
        eq_(var_val, value)


class TestCase(helper.TestCase):
    """A TestCase object with specialized functions for JS testing."""

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

    def assert_var_eq(self, name, value):
        """
        Assert that the value of a variable from the final script context
        contains the value specified.
        """
        eq_(self.get_var(name), value)

