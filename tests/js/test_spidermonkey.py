import json

from mock import Mock, patch

from appvalidator.errorbundle import ErrorBundle
import appvalidator.testcases.javascript.spidermonkey as spidermonkey
import appvalidator.testcases.scripting as scripting


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


def test_crazy_unicode():
    err = ErrorBundle()
    with open('tests/resources/spidermonkey_unicode.js', 'r') as f:
        scripting.test_js_file(err, "foo.js", f.read())
    assert not err.failed(), err.errors + err.warnings


@patch("appvalidator.testcases.javascript.spidermonkey.run_with_tempfile")
def test_tempfiles_are_not_used_when_not_needed(run_with_tempfile):
    run_with_tempfile.return_value = "{}"
    err = ErrorBundle()
    scripting.test_js_file(err, "foo.js", "var x = [123, 456];")
    assert not run_with_tempfile.called
