import os
import validator.testcases.scripting

def _do_test(path):
    "Performs a test on a JS file"
    script = open(path).read()
    
    err = validator.testcases.scripting.traverser.MockBundler()
    validator.testcases.scripting.test_js_file(err, path, script)

    return err

def test_mb_chars():
    "Tests that multi-byte characters are stripped properly"

    err = _do_test("tests/resources/bug_626496.js")
    # There should be a single error.
    print err.ids
    assert err.ids[0][2] == "syntax_error"
