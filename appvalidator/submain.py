import logging
import os
import signal
from zipfile import BadZipfile
from zlib import error as zlib_error

from .webapp import detect_webapp
from .xpi import XPIManager
from . import decorator

from constants import *

types = {0: "Unknown",
         1: "Extension/Multi-Extension",
         2: "Theme",
         3: "Dictionary",
         4: "Language Pack",
         5: "Search Provider"}

assumed_extensions = {"jar": PACKAGE_THEME,
                      "xml": PACKAGE_SEARCHPROV}

log = logging.getLogger()


class ValidationTimeout(Exception):

    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return "Validation timeout after %d seconds" % self.timeout


def prepare_package(err, path, expectation=0, for_appversions=None,
                    timeout=None):
    """Prepares a file-based package for validation.

    timeout is the number of seconds before validation is aborted.
    If timeout is -1 then no timeout checking code will run.
    """
    if not timeout:
        timeout = 60  # seconds

    # Test that the package actually exists. I consider this Tier 0
    # since we may not even be dealing with a real file.
    if err and not os.path.isfile(path):
        err.error(("main",
                   "prepare_package",
                   "not_found"),
                  "The package could not be found")
        return

    # Pop the package extension.
    package_extension = os.path.splitext(path)[1]
    package_extension = package_extension.lower()

    if expectation == PACKAGE_WEBAPP:
        return test_webapp(err, path, expectation)

    # Test that the package is an XPI.
    if package_extension not in (".xpi", ".jar"):
        if err:
            err.error(("main",
                       "prepare_package",
                       "unrecognized"),
                      "The package is not of a recognized type.")
        return False

    package = open(path, "rb")
    validation_state = {'complete': False}

    def timeout_handler(signum, frame):
        if validation_state['complete']:
            # There is no need for a timeout. This might be the result of
            # sequential validators, like in the test suite.
            return
        ex = ValidationTimeout(timeout)
        log.error("%s; Package: %s" % (str(ex), path))
        raise ex

    if timeout != -1:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.setitimer(signal.ITIMER_REAL, timeout)
    output = test_package(err, package, path, expectation,
                          for_appversions)
    package.close()
    validation_state['complete'] = True

    return output


def test_webapp(err, package, expectation=0):
    "Tests the package to see if it is a search provider."

    expected_webapp = expectation in (PACKAGE_ANY, PACKAGE_WEBAPP)
    if not expected_webapp:
        return err.warning(
            err_id=("main", "test_webapp", "extension"),
            warning="Unexpected file extension.",
            description="An unexpected file extension was encountered.")

    detect_webapp(err, package)

    if expected_webapp and not err.failed():
        err.set_type(PACKAGE_WEBAPP)


def test_package(err, file_, name, expectation=PACKAGE_ANY,
                 for_appversions=None):
    "Begins tests for the package."

    # Load up a new instance of an XPI.
    try:
        package = XPIManager(file_, mode="r", name=name)
    except IOError:
        # Die on this one because the file won't open.
        return err.error(("main",
                          "test_package",
                          "unopenable"),
                         "The XPI could not be opened.")
    except (BadZipfile, zlib_error):
        # Die if the zip file is corrupt.
        return err.error(
            ("submain", "_load_install_rdf", "badzipfile"),
            error="Corrupt ZIP file",
            description="We were unable to decompress the zip file.")

    if package.extension in assumed_extensions:
        assumed_type = assumed_extensions[package.extension]
        # Is the user expecting a different package type?
        if not expectation in (PACKAGE_ANY, assumed_type):
            err.error(("main",
                       "test_package",
                       "unexpected_type"),
                      "Unexpected package type (found theme)")

    try:
        output = test_inner_package(err, package, for_appversions)
    except ValidationTimeout as ex:
        err.error(
                err_id=("main", "test_package", "timeout"),
                error="Validation timed out",
                description=["The validation process took too long to "
                             "complete. Contact an addons.mozilla.org editor "
                             "for more information.",
                             str(ex)])
        output = None

    return output


def test_inner_package(err, xpi_package, for_appversions=None):
    "Tests a package's inner content."

    # Iterate through each tier.
    for tier in sorted(decorator.get_tiers()):

        # Let the error bundler know what tier we're on.
        err.set_tier(tier)

        # Iterate through each test of our detected type.
        for test in decorator.get_tests(tier, err.detected_type):
            # Test whether the test is app/version specific.
            if test["versions"] is not None:
                # If the test's version requirements don't apply to the add-on,
                # then skip the test.
                if not err.supports_version(test["versions"]):
                    continue

                # If the user's version requirements don't apply to the test or
                # to the add-on, then skip the test.
                if (for_appversions and
                    not (err._compare_version(requirements=for_appversions,
                                              support=test["versions"]) and
                         err.supports_version(for_appversions))):
                    continue

            # Save the version requirements to the error bundler.
            err.version_requirements = test["versions"]

            test_func = test["test"]
            if test["simple"]:
                test_func(err)
            else:
                # Pass in:
                # - Error Bundler
                # - A copy of the package itself
                test_func(err, xpi_package)

        # Return any errors at the end of the tier if undetermined.
        if err.failed(fail_on_warnings=False) and not err.determined:
            err.unfinished = True
            err.discard_unused_messages(ending_tier=tier)
            return err

    # Return the results.
    return err
