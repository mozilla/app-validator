from nose.tools import eq_

from helper import MockXPI

import appvalidator.testcases.content as content
from appvalidator.errorbundler import ErrorBundle


def test_packed_scripts_ignored():
    """Test that packed scripts are not tested in subpackages."""

    x = MockXPI({"foo.js": "tests/resources/content/one_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    err.save_resource(
        "scripts",
        [{"scripts": ["foo.js"],
          "package": x,
          "state": []}])
    err.package_stack = ["foo"]

    content.test_packed_scripts(err, x)

    assert not err.failed()


def test_packed_scripts_ignored_no_scripts():
    """Test that packed scripts are not tested when there are no scripts."""

    x = MockXPI({"foo.js": "tests/resources/content/one_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    content.test_packed_scripts(err, x)
    assert not err.failed()


def test_packed_scripts():
    """Test that packed scripts are tested properly."""

    x = MockXPI({"foo.js": "tests/resources/content/one_error.js"})

    err = ErrorBundle()
    err.supported_versions = {}

    err.save_resource(
        "scripts",
        [{"scripts": ["foo.js"],
          "package": x,
          "state": []}])

    content.test_packed_scripts(err, x)

    assert err.failed()
    assert err.warnings
    assert not err.errors
