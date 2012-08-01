import appvalidator.testcases.packagelayout as packagelayout
from appvalidator.errorbundler import ErrorBundle
from helper import _do_test, MockXPI


def test_blacklisted_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""

    err = _do_test("tests/resources/packagelayout/ext_blacklist.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_extension"]


def test_java_jar_detection():
    """
    Test that Java archives are flagged as such so that they do not generate
    hundreds or thousands of errors.
    """

    classes = ("c%d.class" % i for i in xrange(1000))
    def strings():  # Look at how functional this is. How functional!
        while 1:
            yield ""
    mock_xpi = MockXPI(dict(zip(classes, strings())))
    err = ErrorBundle(None, True)
    packagelayout.test_blacklisted_files(err, mock_xpi)

    assert not err.failed()
    assert err.notices


def test_blacklisted_magic_numbers():
    "Tests that blacklisted magic numbers are banned"

    err = _do_test("tests/resources/packagelayout/magic_number.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_content"]
    assert "binary_components" not in err.metadata


class MockDupeZipFile(object):
    """Mock a ZipFile class, simulating duplicate filename entries."""

    def namelist(self):
        return ["foo.bar", "foo.bar"]


class MockDupeXPI(object):
    """Mock the XPIManager class, simulating duplicate filename entries."""

    def __init__(self):
        self.zf = MockDupeZipFile()
        self.subpackage = False


def test_duplicate_files():
    """Test that duplicate files in a package are caught."""

    err = ErrorBundle()
    err.save_resource("has_install_rdf", True)
    packagelayout.test_layout_all(err, MockDupeXPI())
    assert err.failed()


