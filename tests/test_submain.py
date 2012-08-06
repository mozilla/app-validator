import time

import fudge
from mock import patch
from nose.tools import eq_

import appvalidator.submain as submain
from appvalidator.errorbundler import ErrorBundle
from appvalidator.constants import *
from helper import MockXPI


@patch("appvalidator.submain.test_package",
       lambda w, x, y: True)
def test_prepare_package():
    "Tests that the prepare_package function passes for valid data"

    err = ErrorBundle()
    eq_(submain.prepare_package(err, "tests/resources/main/foo.xpi"), err)
    assert not err.failed()


@patch("appvalidator.submain.test_inner_package",
       lambda err, package: time.sleep(1))
def test_validation_timeout():
    err = ErrorBundle()
    submain.prepare_package(err, "tests/resources/main/foo.xpi",
                            timeout=0.1)
    assert len(err.errors) == 1


def test_prepare_package_missing():
    "Tests that the prepare_package function fails when file is not found"

    err = ErrorBundle()
    submain.prepare_package(err, "foo/bar/asdf/qwerty.xyz")

    assert err.failed()


def test_prepare_package_bad_file():
    "Tests that the prepare_package function fails for unknown files"

    err = ErrorBundle()
    submain.prepare_package(err, "tests/resources/main/foo.bar")

    assert err.failed()


@fudge.patch("appvalidator.submain.detect_webapp")
def test_prepare_package_webapp(fake_webapp_validator):
    fake_webapp_validator.expects_call().with_arg_count(2)

    err = ErrorBundle()
    submain.prepare_package(err, "tests/resources/main/mozball.webapp")
    assert not err.failed()


class MockDecorator:

    def __init__(self, fail_tier=None, determined=False):
        self.determined = determined
        self.ordering = [1]
        self.fail_tier = fail_tier
        self.last_tier = 0

    def get_tiers(self):
        "Returns unordered tiers. These must be in a random order."
        return (4, 1, 3, 5, 2)

    def get_tests(self, tier, type):
        "Should return a list of tests that occur in a certain order"

        self.on_tier = tier

        print "Retrieving Tests: Tier %d" % tier

        if self.fail_tier is not None:
            if tier == self.fail_tier:
                print "> Fail Tier"

                yield {"test": lambda x, y: x.fail_tier(),
                       "simple": False,
                       "versions": None}

            assert tier <= self.fail_tier or self.determined

        self.last_tier = tier

        for x in range(1,10): # Ten times because we care
            print "Yielding Complex"
            yield {"test": lambda x, z: x.report(tier),
                   "simple": False,
                   "versions": None}
            print "Yielding Simple"
            yield {"test": lambda x, z=None: x.test_simple(z),
                   "simple": True,
                   "versions": None}

    def report_tier(self, tier):
        "Checks to make sure the last test run is on the current tier."

        assert tier == self.on_tier

    def report_fail(self):
        "Alerts the tester to a failure"

        print self.on_tier
        print self.fail_tier
        assert self.on_tier == self.fail_tier


class MockErrorHandler:

    def __init__(self, mock_decorator, determined=False):
        self.decorator = mock_decorator
        self.detected_type = 0
        self.has_failed = False
        self.determined = determined

        self.pushable_resources = {}
        self.resources = {}

    def save_resource(self, name, value, pushable=False):
        "Saves a resource to the bundler"
        resources = self.pushable_resources if pushable else self.resources
        resources[name] = value

    def set_tier(self, tier):
        "Sets the tier"
        pass

    def report(self, tier):
        "Passes the tier back to the mock decorator to verify the tier"
        self.decorator.report_tier(tier)

    def fail_tier(self):
        "Simulates a failure"
        self.has_failed = True
        self.decorator.report_fail()

    def test_simple(self, z):
        "Makes sure that the second two params of a simple test are respected"
        assert z is None

    def failed(self, fail_on_warnings=False):
        "Simple accessor because the standard error handler has one"
        return self.has_failed


# Test the function of the decorator iterator
@patch("appvalidator.submain.decorator", MockDecorator())
def test_inner_package():
    """Tests that the test_inner_package function works properly."""

    err = MockErrorHandler(submain.decorator)
    submain.test_inner_package(err, "foo")
    assert not err.failed()


@patch("appvalidator.submain.decorator", MockDecorator(3))
def test_inner_package_failtier():
    """Tests that the test_inner_package function fails at a failed tier."""

    err = MockErrorHandler(submain.decorator)
    submain.test_inner_package(err, "foo")
    assert err.failed()


# Test determined modes
@patch("appvalidator.submain.decorator", MockDecorator(None, True))
def test_inner_package_determined():
    "Tests that the determined test_inner_package function works properly"

    err = MockErrorHandler(submain.decorator, True)
    submain.test_inner_package(err, "foo")

    assert not err.failed()
    eq_(submain.decorator.last_tier, 5)


@patch("appvalidator.submain.decorator", MockDecorator(3, True))
def test_inner_package_failtier():
    "Tests the test_inner_package function in determined mode while failing"

    err = MockErrorHandler(submain.decorator, True)
    submain.test_inner_package(err, "foo")

    assert err.failed()
    eq_(submain.decorator.last_tier, 5)
