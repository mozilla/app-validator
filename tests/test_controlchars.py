import sys

from nose.tools import eq_, nottest

from appvalidator.errorbundle import ErrorBundle
from appvalidator.errorbundle.outputhandlers.shellcolors import OutputHandler
import appvalidator.unicodehelper
import appvalidator.testcases.scripting
from helper import TestCase


class TestControlChars(TestCase):

    @nottest
    def run_test(self, path):
        self.setup_err()
        with open(path, "rb") as package:
            script = appvalidator.unicodehelper.decode(package.read())
        appvalidator.testcases.scripting.test_js_file(self.err, path, script)

    def test_controlchars_ascii_ok(self):
        """Test that multi-byte characters are decoded properly (utf-8)."""

        self.run_test("tests/resources/controlchars/controlchars_ascii_ok.js")
        self.assert_silent()

    def test_controlchars_ascii_warn(self):
        """
        Test that multi-byte characters are decoded properly (utf-8) but
        remaining non-ASCII characters raise warnings.
        """

        self.run_test(
            "tests/resources/controlchars/controlchars_ascii_warn.js")
        self.assert_failed(with_warnings=True)
        eq_(self.err.warnings[0]["id"][2], "syntax_error")

    def test_controlchars_utf8_ok(self):
        """Test that multi-byte characters are decoded properly (utf-8)."""

        self.run_test("tests/resources/controlchars/controlchars_utf-8_ok.js")
        self.assert_silent()

    def test_controlchars_utf8_warn(self):
        """
        Tests that multi-byte characters are decoded properly (utf-8) but remaining
        non-ASCII characters raise warnings.
        """

        self.run_test("tests/resources/controlchars/controlchars_utf-8_warn.js")
        self.assert_failed(with_warnings=True)
        eq_(self.err.warnings[0]["id"][2], "syntax_error")
