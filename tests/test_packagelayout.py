from itertools import repeat

from mock import MagicMock

import appvalidator.testcases.packagelayout as packagelayout
from appvalidator.errorbundle import ErrorBundle
from helper import _do_test, MockXPI, TestCase


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
    package.zf = zf = MagicMock()
    zf.namelist.return_value = ["foo.bar", "foo.bar"]

    err = ErrorBundle()
    packagelayout.test_layout_all(err, package)
    assert err.failed()


def test_version_control():
    """Test that version control in a package are caught."""

    package = MockXPI({".git/foo/bar": None})

    err = ErrorBundle()
    packagelayout.test_blacklisted_files(err, package)
    assert err.failed()


def test_spaces_in_names():
    """Test that spaces in filenames are errors."""

    package = MockXPI({
        "foo/bar/foo.bar ": None,
        "foo/bar/ foo.bar": None,
    })

    err = ErrorBundle()
    packagelayout.test_blacklisted_files(err, package)
    assert err.failed()
    assert len(err.errors) == 2


class TestMETAINF(TestCase):

    def setUp(self):
        self.setup_err()
        self.package = MagicMock()
        self.package.subpackage = False

    def test_metainf_pass(self):
        self.package.zf.namelist.return_value = ["META-INF-foo.js"]
        packagelayout.test_layout_all(self.err, self.package)
        self.assert_silent()

    def test_metainf_fail(self):
        """Test that META-INF directories fail validation."""

        self.package.zf.namelist.return_value = ["META-INF/foo.js"]
        packagelayout.test_layout_all(self.err, self.package)
        self.assert_failed(with_errors=True)
