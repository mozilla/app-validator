from itertools import repeat

from mock import MagicMock

import appvalidator.testcases.packagelayout as packagelayout
from appvalidator.errorbundle import ErrorBundle
from helper import _do_test, MockXPI


def test_blacklisted_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""

    err = _do_test("tests/resources/packagelayout/ext_blacklist.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_extension"]


def test_blacklisted_magic_numbers():
    "Tests that blacklisted magic numbers are banned"

    err = _do_test("tests/resources/packagelayout/magic_number.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_content"]
    assert "binary_components" not in err.metadata


def test_duplicate_files():
    """Test that duplicate files in a package are caught."""

    package = MagicMock()
    package.subpackage = False
    zf = MagicMock()
    zf.namelist.return_value = ["foo.bar", "foo.bar"]
    package.zf = zf

    err = ErrorBundle()
    err.save_resource("has_install_rdf", True)
    packagelayout.test_layout_all(err, package)
    assert err.failed()
