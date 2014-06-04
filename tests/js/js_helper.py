import functools
import sys
import types

from nose import SkipTest
from nose.tools import eq_

from .. import helper
from ..helper import MockXPI
from appvalidator.constants import SPIDERMONKEY_INSTALLATION
from appvalidator.errorbundle import ErrorBundle
from appvalidator.errorbundle.outputhandlers.shellcolors import OutputHandler
import appvalidator
import appvalidator.testcases.content

appvalidator.testcases.javascript.traverser.JS_DEBUG = True
appvalidator.testcases.javascript.predefinedentities.enable_debug()


def uses_js(func):
    if func:
        try:
            setattr(func, "js", True)
        except Exception:
            # If Python >2.7 squaks about methods being bound, just work around
            # the nonsense.
            setattr(func.__func__, "js", True)

    return func


def skip_on_acorn(func):
    """Skips a test when the test is run under Acorn."""
    if not SPIDERMONKEY_INSTALLATION:
        raise SkipTest()
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
        print "Running", script

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
        print "Testing {var} == {val}".format(var=name, val=value)
        val = self.get_var(name)
        if isinstance(val, float):
            val *= 100000
            val = round(val)
            val /= 100000

        eq_(val, value,
            explanation or "%r doesn't equal %r" % (val, value))


def must_assert(func):
    "Decorator for asserting that a JS assert method is used."
    @functools.wraps(func)
    def wrap(self):
        func(self)
        assert getattr(self.err, "asserts", False), "Does not assert!"
    return wrap


def silent(func):
    "Decorator for asserting that the output of a test is silent."
    @functools.wraps(func)
    def wrap(self):
        func(self)
        self.assert_silent()
    return wrap


def warnings(count=None):
    "Decorator for asserting that the output of a test has warnings."
    def decorator(func):
        @functools.wraps(func)
        def wrap(self):
            func(self)
            self.assert_failed(with_warnings=True)
            if count is not None:
                eq_(len(self.err.warnings), count,
                    "Warning count does not match")
        return wrap
    return decorator


def errors(count=None):
    "Decorator for asserting that the output of a test has errors."
    def decorator(func):
        @functools.wraps(func)
        def wrap(self):
            func(self)
            self.assert_failed(with_errors=True)
            if count is not None:
                eq_(len(self.err.errors), count,
                    "Warning count does not match")
        return wrap
    return decorator
