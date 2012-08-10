import sys

from appvalidator.zip import ZipPackage
from appvalidator.errorbundle import ErrorBundle
from appvalidator.errorbundle.outputhandlers.shellcolors import OutputHandler


def _do_test(path, test, failure=True, set_type=0,
             listed=False, xpi_mode="r"):

    package_data = open(path, "rb")
    package = ZipPackage(package_data, mode=xpi_mode, name=path)
    err = ErrorBundle()
    if listed:
        err.save_resource("listed", True)

    # Populate in the dependencies.
    if set_type:
        err.set_type(set_type) # Conduit test requires type

    test(err, package)

    print err.print_summary(verbose=True)
    assert err.failed() if failure else not err.failed()

    return err


class TestCase(object):
    def setUp(self):
        self.err = None
        self.is_bootstrapped = False
        self.detected_type = None
        self.listed = True

    def reset(self):
        """
        Reset the test case so that it can be run a second time (ideally with
        different parameters).
        """
        self.err = None

    def setup_err(self):
        """
        Instantiate the error bundle object. Use the `instant` parameter to
        have it output errors as they're generated. `for_appversions` may be set
        to target the test cases at a specific Gecko version range.

        An existing error bundle will be overwritten with a fresh one that has
        the state that the test case was setup with.
        """
        self.err = ErrorBundle(instant=True,
                               listed=getattr(self, "listed", True))
        self.err.handler = OutputHandler(sys.stdout, True)

    def assert_failed(self, with_errors=False, with_warnings=None):
        """
        First, asserts that the error bundle registers a failure (recognizing
        whether warnings are acknowledged). Second, if with_errors is True,
        the presence of errors is asserted. If it is not true (default), it
        is tested that errors are not present. If with_warnings is not None,
        the presence of warnings is tested just like with_errors)
        """
        assert self.err.failed(fail_on_warnings=with_warnings or
                                                with_warnings is None), \
                "Test did not fail; failure was expected."

        if with_errors:
            assert self.err.errors, "Errors were expected."
        elif self.err.errors:
            raise AssertionError("Tests found unexpected errors: %s" %
                                self.err.print_summary(verbose=True))

        if with_warnings is not None:
            if with_warnings:
                assert self.err.warnings, "Warnings were expected."
            elif self.err.warnings:
                raise ("Tests found unexpected warnings: %s" %
                           self.err.print_summary())

    def assert_notices(self):
        """
        Assert that notices have been generated during the validation process.
        """
        assert self.err.notices, "Notices were expected."

    def assert_passes(self, warnings_pass=False):
        """
        Assert that no errors have been raised. If warnings_pass is True, also
        assert that there are no warnings.
        """
        assert not self.failed(fail_on_warnings=not warnings_pass), \
                ("Test was intended to pass%s, but it did not." %
                     (" with warnings" if warnings_pass else ""))

    def assert_silent(self):
        """
        Assert that no messages (errors, warnings, or notices) have been
        raised.
        """
        assert not self.err.errors, 'Got these: %s' % self.err.errors
        assert not self.err.warnings, 'Got these: %s' % self.err.warnings
        assert not self.err.notices, 'Got these: %s' % self.err.notices

    def assert_got_errid(self, errid):
        """
        Assert that a message with the given errid has been generated during
        the validation process.
        """
        assert any(msg["id"] == errid for msg in
                   (self.err.errors + self.err.warnings + self.err.notices)), \
                "%s was expected, but it was not found." % repr(errid)


class MockZipFile:

    def namelist(self):
        return []


class MockXPI:

    def __init__(self, data=None):
        if not data:
            data = {}
        self.zf = MockZipFile()
        self.data = data
        self.filename = "mock_xpi.xpi"

    def test(self):
        return True

    def info(self, name):
        return {"name_lower": name.lower(),
                "extension": name.lower().split(".")[-1]}

    def __iter__(self):
        for name in self.data.keys():
            yield name

    def __contains__(self, name):
        return name in self.data

    def read(self, name):
        return open(self.data[name]).read()

