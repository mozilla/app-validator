import json

from mock import MagicMock, patch

from js_helper import _do_test_raw
from appvalidator.errorbundle import ErrorBundle
import appvalidator.testcases.scripting as scripting
import appvalidator.testcases.javascript.spidermonkey as spidermonkey


def test_scripting_enabled():

    err = ErrorBundle()
    err.save_resource("SPIDERMONKEY", None)
    assert scripting.test_js_file(err, "abc def", "foo bar") is None


@patch("appvalidator.testcases.scripting.SPIDERMONKEY_INSTALLATION", None)
def test_scripting_disabled():
    "Ensures that Spidermonkey is not run if it is set to be disabled"
    err = ErrorBundle()
    assert scripting.test_js_file(err, "abc def", "foo bar") is None


def test_scripting_snippet():
    "Asserts that JS snippets are treated equally"

    err = ErrorBundle()
    scripting.test_js_snippet(err, "alert(1 + 1 == 2)", "bar.zap")
    assert not err.failed()

    err = ErrorBundle()
    scripting.test_js_snippet(err, "eval('foo');", "bar.zap")
    assert err.failed()


@patch("subprocess.Popen")
def test_reflectparse_presence(Popen):
    "Tests that when Spidermonkey is too old, a proper error is produced"

    SPObj = MagicMock()
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


def test_compiletime_errors():
    "Tests that compile time errors don't break the validator"

    # Syntax error
    assert _do_test_raw("var x =;").failed()

    # Reference error
    assert _do_test_raw("x - y = 4;").failed()

