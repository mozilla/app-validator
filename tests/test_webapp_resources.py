from functools import wraps
import os

from mock import Mock, patch
from nose.tools import eq_, raises
import requests.exceptions as reqexc

import appvalidator.testcases.webappbase as appbase
from helper import TestCase
from appvalidator.constants import ICON_LIMIT
from appvalidator.errorbundle import ErrorBundle


class TestWebappDataURL(TestCase):
    """Test that data url resources are properly decoded."""

    @patch("appvalidator.testcases.webappbase.try_get_data_uri")
    def test_data_uri_when_appropriate(self, tgdu):
        assert appbase.try_get_resource(
            self.err, None, "data:foobar", "webapp.manifest", "icon")
        assert tgdu.called

    @patch("base64.urlsafe_b64decode")
    def test_data_uri_stripping(self, b64decode):
        for uri in ("data:abc;def,foo",
                    "data:def,foo",
                    "data:foo"):
            appbase.try_get_resource(
                self.err, None, uri, "webapp.manifest", "icon")
            eq_(b64decode.call_args[0][0], "foo")


class TestPackagedAppLocalResource(TestCase):

    def setUp(self):
        super(TestPackagedAppLocalResource, self).setUp()
        self.setup_err()
        self.err.save_resource("packaged", True)

        self.package = Mock()
        self.package.read.return_value = "read"

    def test_local_url(self):
        eq_(appbase.try_get_resource(
                self.err, self.package, "/local.txt", ""), "read")
        self.package.read.assert_called_once_with("local.txt")

    def test_local_url_relative(self):
        eq_(appbase.try_get_resource(
                self.err, self.package, "local.txt", ""), "read")
        self.package.read.assert_called_once_with("local.txt")

    def test_local_not_found(self):
        self.package.read.side_effect = Exception("read error")
        appbase.try_get_resource(self.err, self.package, "local.txt", "")
        self.package.read.assert_called_once_with("local.txt")
        self.assert_failed(with_errors=True)

    @raises(ValueError)
    @patch("requests.get")
    def test_absolute_url(self, requests_get):
        requests_get.side_effect = ValueError("Whoops!")
        appbase.try_get_resource(self.err, self.package, "http://foo.bar/", "")


def mock_requests(with_exception, text):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with patch("requests.get") as requests_get:
                requests_get.side_effect = with_exception(text)
                return func(*args, **kwargs)
        return wrapper
    return decorator


class TestResourceExceptions(TestCase):

    def setUp(self):
        super(TestResourceExceptions, self).setUp()
        self.setup_err()

    @mock_requests(reqexc.MissingSchema, "Bad URL")
    def test_bad_url_MissingSchema(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)

    @mock_requests(reqexc.URLRequired, "Bad URL")
    def test_bad_url_URLRequired(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)

    @mock_requests(reqexc.ConnectionError, "Connection Error")
    def test_ConnectionError(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)

    @mock_requests(reqexc.Timeout, "Timeout")
    def test_Timeout(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True, with_warnings=False)

    @mock_requests(reqexc.HTTPError, "404")
    def test_HTTPError(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)

    @mock_requests(reqexc.TooManyRedirects, "Redirects")
    def test_TooManyRedirects(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)


class TestDataOutput(TestCase):

    def setUp(self):
        super(TestDataOutput, self).setUp()
        self.setup_err()

    @patch("requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_too_big(self, r_g):
        big_response_object = Mock()
        big_response_object.raw.read.return_value = "x" * 100
        r_g.return_value = big_response_object

        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)

    @patch("requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_just_right(self, r_g):
        normal_response_object = Mock()
        normal_response_object.raw.read.side_effect = ["x" * 100, ""]
        r_g.return_value = normal_response_object

        eq_(appbase.try_get_resource(self.err, None, "http://foo.bar/", ""),
            "x" * 100)
        self.assert_silent()

    @patch("requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_empty(self, r_g):
        empty_response = Mock()
        empty_response.raw.read.return_value = ""
        r_g.return_value = empty_response

        eq_(appbase.try_get_resource(
                self.err, None, "http://foo.bar/", ""), "")
        self.assert_failed(with_errors=True)


class TestResourcePolling(TestCase):

    def test_ignore_when_errors(self):
        """When there are errors in validation, don't poll the resources."""
        err = Mock()
        err.errors = True
        appbase.test_app_resources(err, None)
        eq_(err.get_resource.call_count, 0)

    def test_ignore_when_missing_manifest(self):
        """When there are errors in validation, don't poll the resources."""
        self.setup_err()
        appbase.test_app_resources(self.err, None)
        self.assert_silent()

    def setup_manifest(self):
        self.setup_err()
        manifest = {}
        self.err.save_resource("manifest", manifest)
        return manifest

    @patch("appvalidator.testcases.webappbase.test_icon")
    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_icons(self, tgr, test_icon):
        tgr.return_value = "foobar"

        self.setup_manifest()["icons"] = {"32": "fizz"}
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        eq_(test_icon.call_args[1]["data"].getvalue(), "foobar")

    @patch("appvalidator.testcases.webappbase.test_icon", Mock())
    @patch("appvalidator.testcases.webappbase.try_get_resource",
           Mock(return_value="this is an icon."))
    def test_too_many_icons(self):
        self.setup_manifest()["icons"] = dict(
            [(str(i), "http://foo%d.jpg" % i) for i in range(ICON_LIMIT + 1)])
        appbase.test_app_resources(self.err, None)
        self.assert_failed(with_warnings=True)

    @patch("appvalidator.testcases.webappbase.test_icon", Mock())
    @patch("appvalidator.testcases.webappbase.try_get_resource",
           Mock(return_value="this is an icon."))
    def test_many_icons_same_url(self):
        self.setup_manifest()["icons"] = dict(
            [(str(i), "foo.jpg") for i in range(ICON_LIMIT + 1)])
        appbase.test_app_resources(self.err, None)
        self.assert_silent()

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_appcache_path(self, tgr):
        self.setup_manifest()["appcache_path"] = "fizz"
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        # Test that we don't warn the dev that their appcache exceeds a size
        # limit.
        eq_(tgr.call_args[1]["max_size"], False)

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_launch_path(self, tgr):
        self.setup_manifest()["launch_path"] = "fizz"
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        # Test that we don't warn the dev that their origin exceeds a size
        # limit.
        eq_(tgr.call_args[1]["max_size"], False)

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_root_developer_absent(self, tgr):
        self.setup_manifest()["developer"] = {}
        appbase.test_app_resources(self.err, None)
        assert not tgr.called

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_root_developer_present(self, tgr):
        self.setup_manifest()["developer"] = {"url": "fizz"}
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        # Test that we don't warn the dev that their homepage exceeds a size
        # limit.
        eq_(tgr.call_args[1]["max_size"], False)

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_locale_developer_absent(self, tgr):
        self.setup_manifest()["locales"] = {"es": {}}
        appbase.test_app_resources(self.err, None)
        assert not tgr.called

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_locale_developer_url_absent(self, tgr):
        self.setup_manifest()["locales"] = {"es": {"developer": {}}}
        appbase.test_app_resources(self.err, None)
        assert not tgr.called

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_locale_developer_present(self, tgr):
        self.setup_manifest()["locales"] = {
            "es": {"developer": {"url": "fizz"}}
        }
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        # Test that we don't warn the dev that their homepage exceeds a size
        # limit.
        eq_(tgr.call_args[1]["max_size"], False)


class TestIconProperties(TestCase):
    """Test that icons are properly validated."""

    def setUp(self):
        super(TestIconProperties, self).setUp()
        self.setup_err()

    def _test_icon(self, name, size):
        url = "http://example.com/%s" % name
        with open(os.path.join(os.path.dirname(__file__),
                               "resources", name)) as icon:
            appbase.test_icon(self.err, icon, url, size)

    def test_pass(self):
        self._test_icon("icon-128.png", 128)
        self.assert_silent()

    def test_bad_icon(self):
        self._test_icon("corrupt.xpi", 128)
        self.assert_failed(with_errors=True)

    def test_not_square(self):
        self._test_icon("icon-128x64.png", 128)
        self.assert_failed(with_errors=True)

    def test_bad_size(self):
        self._test_icon("icon-128.png", 256)
        self.assert_failed(with_errors=True)
