import json

from mock import Mock, patch

from js_helper import TestCase
from appvalidator.errorbundle import ErrorBundle
import appvalidator.testcases.scripting as scripting
import appvalidator.testcases.javascript.spidermonkey as spidermonkey


def test_scripting_enabled():
    err = ErrorBundle()
    err.save_resource("SPIDERMONKEY", None)
    assert scripting.test_js_file(err, "abc def", "foo bar") is None


@patch("appvalidator.testcases.scripting.SPIDERMONKEY_INSTALLATION", None)
def test_scripting_disabled():
    """Ensures that Spidermonkey is not run if it is set to be disabled."""
    err = ErrorBundle()
    assert scripting.test_js_file(err, "abc def", "foo bar") is None


@patch("subprocess.Popen")
def test_reflectparse_presence(Popen):
    "Tests that when Spidermonkey is too old, a proper error is produced"

    SPObj = Mock()
    SPObj.communicate.return_value = (
        json.dumps({"error": True,
                    "error_message": "ReferenceError: Reflect is not defined",
                    "line_number": 0}),
        ""
    )
    Popen.return_value = SPObj

    try:
        spidermonkey._get_tree("foo bar", "[path]")
    except RuntimeError as err:
        assert (str(err) ==
            "Spidermonkey version too old; 1.8pre+ required; "
            "error='ReferenceError: Reflect is not defined'; "
            "spidermonkey='[path]'")

def test_multiline_command_input():
    err = ErrorBundle()
    with open('tests/resources/content/unicode.js', 'r') as f:
        # Just make sure it doesn't raise.
        scripting.test_js_file(err, "foo.js", f.read())
    assert not err.failed()
