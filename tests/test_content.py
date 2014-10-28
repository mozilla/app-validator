import hashlib
from mock import patch
from nose.tools import eq_, ok_

from helper import MockXPI, TestCase

from appvalidator.zip import ZipPackage
import appvalidator.testcases.content as content
from appvalidator.constants import *


class MockTestEndpoint(object):
    """
    Simulates a test module and reports whether individual tests have been
    attempted on it.
    """

    def __init__(self, expected, td_error=False):
        expectations = {}
        for expectation in expected:
            expectations[expectation] = {"count": 0, "subpackage": 0}

        self.expectations = expectations
        self.td_error = td_error
        self.found_tiers = []

    def _tier_test(self, err, package, name):
        "A simulated test case for tier errors"
        print "Generating subpackage tier error..."
        self.found_tiers.append(err.tier)
        err.error(("foo", ),
                  "Tier error",
                  "Just a test")

    def __getattribute__(self, name):
        """Detects requests for validation tests and returns an
        object that simulates the outcome of a test."""

        print "Requested: %s" % name

        if name == "test_package" and self.td_error:
            return self._tier_test

        if name in ("expectations",
                    "assert_expectation",
                    "td_error",
                    "_tier_test",
                    "found_tiers"):
            return object.__getattribute__(self, name)

        if name in self.expectations:
            self.expectations[name]["count"] += 1

        if name == "test_package":
            def wrap(package, name):
                pass
        elif name in ("test_css_file", "test_js_file", "process"):
            def wrap(err, name, file_data):
                pass
        else:
            def wrap(err, pak):
                if isinstance(pak, ZipPackage) and pak.subpackage:
                    self.expectations[name]["subpackage"] += 1

        return wrap

    def assert_expectation(self, name, count, type_="count"):
        """Asserts that a particular test has been run a certain number
        of times"""

        print self.expectations
        assert name in self.expectations
        eq_(self.expectations[name][type_], count)


class MockMarkupEndpoint(MockTestEndpoint):
    "Simulates the markup test module"

    def __getattribute__(self, name):

        if name == "MarkupParser":
            return lambda x: self

        return MockTestEndpoint.__getattribute__(self, name)


class TestContent(TestCase):

    def _run_test(self, mock_package):
        return content.test_packed_packages(self.err, mock_package)

    @patch("appvalidator.testcases.content.testendpoint_markup",
           MockMarkupEndpoint(("process", )))
    def test_markup(self):
        "Tests markup files in the content validator."
        self.setup_err()
        mock_package = MockXPI({"foo.xml": "tests/resources/content/junk.xpi"})

        eq_(self._run_test(mock_package), 1)
        content.testendpoint_markup.assert_expectation("process", 1)
        content.testendpoint_markup.assert_expectation(
            "process", 0, "subpackage")

    @patch("appvalidator.testcases.content.testendpoint_css",
           MockTestEndpoint(("test_css_file", )))
    def test_css(self):
        "Tests css files in the content validator."

        self.setup_err()
        mock_package = MockXPI(
            {"foo.css": "tests/resources/content/junk.xpi"})

        eq_(self._run_test(mock_package), 1)
        content.testendpoint_css.assert_expectation("test_css_file", 1)
        content.testendpoint_css.assert_expectation(
            "test_css_file", 0, "subpackage")

    @patch("appvalidator.testcases.content.testendpoint_js",
           MockTestEndpoint(("test_js_file", )))
    def test_js(self):
        """Test that JS files are properly tested in the content validator."""

        self.setup_err()
        mock_package = MockXPI(
            {"foo.js": "tests/resources/content/junk.xpi"})

        eq_(self._run_test(mock_package), 1)
        content.testendpoint_js.assert_expectation("test_js_file", 1)
        content.testendpoint_js.assert_expectation(
            "test_js_file", 0, "subpackage")

    def test_hidden_files(self):
        """Tests that hidden files are reported."""

        def test_structure(structure):
            self.setup_err()
            mock_package = MockXPI(
                dict([(structure, "tests/resources/content/junk.xpi")]))
            content.test_packed_packages(self.err, mock_package)
            print structure
            print self.err.print_summary(verbose=True)
            self.assert_failed()

        for structure in (".hidden", "dir/__MACOSX/foo", "dir/.foo.swp",
                          "dir/file.old", "dir/file.xul~"):
            yield test_structure, structure

    def test_too_much_garbage(self):
        """Tests that hidden files are reported."""
        self.setup_err()
        mock_package = MockXPI(
            {".junky": "tests/resources/content/junk.xpi"},
            default_size=50 * 1024)

        content.test_packed_packages(self.err, mock_package)
        self.assert_failed(with_warnings=True)

        mock_package = MockXPI(
            {".junky": "tests/resources/content/junk.xpi",
             ".morejunk": "tests/resources/content/junk.xpi",},
            default_size=50 * 1024)

        content.test_packed_packages(self.err, mock_package)
        self.assert_failed(with_warnings=True, with_errors=True)

    def test_whitelist(self):
        """Test that whitelisted files are properly skipped tested by the
        content validator."""

        self.setup_err()
        # Build a fake package with a js file that would not validate if it
        # wasn't whitelisted.
        mock_package = MockXPI({"foo.js": "tests/resources/content/error.js"})
        
        # Build the mock whitelist. Convert line-endings to unix-style before
        # building the hash, it should still validate properly as the code that
        # validates the package converts every js file to unix-style endings
        # first.
        ok_('\r\n' in mock_package.read('foo.js'))
        foo_js = mock_package.read('foo.js').replace('\r\n', '\n')
        hashes_whitelist = [hashlib.sha256(foo_js).hexdigest()]

        with patch("appvalidator.testcases.content.hashes_whitelist",
                   hashes_whitelist):
            eq_(self._run_test(mock_package), 0)
            self.assert_passes()

        # Prove that it would fail otherwise.
        eq_(self._run_test(mock_package), 1)
        self.assert_failed()


class TestCordova(TestCase):

    def test_cordova_fail(self):
        "Test that cordova is detected in the content tests."
        self.setup_err()
        mock_package = MockXPI({"foo.bar": "tests/resources/content/junk.xpi"})

        content.test_cordova(self.err, mock_package)
        assert not self.err.metadata["cordova"]

        # We can recycle the error bundle since it's clean.
        mock_package = MockXPI({"www/cordova.js": "tests/resources/content/junk.xpi"})

        content.test_cordova(self.err, mock_package)
        assert self.err.metadata["cordova"]
