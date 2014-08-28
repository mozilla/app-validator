# -*- coding: utf-8 -*-
import cStringIO
import gzip
import os
from functools import wraps

import requests.exceptions as reqexc
from mock import Mock, patch
from nose.tools import eq_, raises
from requests.packages.urllib3.response import HTTPResponse

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

    def test_data_uri_unencoded(self):
        eq_(appbase.try_get_data_uri(u'data:this is a test'),
            'this is a test')

    def test_data_uri_unencoded_mime(self):
        eq_(appbase.try_get_data_uri(u'data:test/html;this is a test'),
            'this is a test')

    def test_data_uri_decode(self):
        eq_(appbase.try_get_data_uri(u'data:base64,dGhpcyBpcyBhIHRlc3Q='),
            'this is a test')


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

    def test_local_url_with_hash(self):
        eq_(appbase.try_get_resource(
                self.err, self.package, "/local.txt#foo", ""), "read")
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
    @patch("appvalidator.testcases.webappbase.requests.get")
    def test_absolute_url(self, requests_get):
        requests_get.side_effect = ValueError("Whoops!")
        appbase.try_get_resource(self.err, self.package, "http://foo.bar/", "")


def mock_requests(with_exception, text):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with patch("appvalidator.testcases.webappbase."
                       "requests.get") as requests_get:
                requests_get.side_effect = with_exception(text)
                return func(*args, **kwargs)
        return wrapper
    return decorator


class DummyException(Exception):
    pass


class TestResourceExceptions(TestCase):

    def setUp(self):
        super(TestResourceExceptions, self).setUp()
        self.setup_err()

    @mock_requests(reqexc.MissingSchema, "Bad URL")
    def test_bad_url_MissingSchema(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_warnings=True)

    def test_bad_url_MissingSchema_normalized(self):
        self.err.save_resource(
            "manifest_url", "ftp://test.com/manifest.webapp")
        with patch("appvalidator.testcases.webappbase."
                   "requests.get") as requests_get:
            requests_get.side_effect = DummyException
            try:
                appbase.try_get_resource(self.err, None, "/zip/zap", "")
            except DummyException:
                requests_get.assert_called_once_with(
                    "ftp://test.com/zip/zap", stream=True,
                    allow_redirects=True, timeout=3, headers=appbase.HEADERS)
            else:
                raise AssertionError("Should have gotten DummyException")

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

    @mock_requests(reqexc.TooManyRedirects, "Duplicate error")
    def test_not_duplicated(self):
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)
        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        assert len(self.err.errors) == 1, (
            "HTTP errors should not be duplicated.")


class TestDataOutput(TestCase):

    def setUp(self):
        super(TestDataOutput, self).setUp()
        self.setup_err()

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_too_big(self, r_g):
        big_response_object = Mock()
        big_response_object.raw.read.return_value = "x" * 100
        big_response_object.status_code = 200
        r_g.return_value = big_response_object

        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
        self.assert_failed(with_errors=True)

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_just_right(self, r_g):
        normal_response_object = Mock()
        normal_response_object.raw.read.side_effect = ["x" * 100, ""]
        normal_response_object.encoding = ""
        normal_response_object.status_code = 200
        r_g.return_value = normal_response_object

        eq_(appbase.try_get_resource(self.err, None, "http://foo.bar/", ""),
            "x" * 100)
        self.assert_silent()

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_unicodeness(self, r_g):
        normal_response_object = Mock()
        normal_response_object.raw.read.side_effect = [u"é".encode('utf-8')
                                                       * 100, ""]
        normal_response_object.encoding = "UTF-8"
        normal_response_object.status_code = 200
        r_g.return_value = normal_response_object

        eq_(appbase.try_get_resource(self.err, None, "http://foo.bar/", ""),
            u"é" * 100)
        self.assert_silent()

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_unicode_binary(self, r_g):
        normal_response_object = Mock()
        # The u"é" is *not* encoded in UTF-8 this time, so it would throw an
        # UnicodeEncodeError if we'd try to decode it.
        normal_response_object.raw.read.side_effect = [u"é" * 100, ""]
        normal_response_object.encoding = "UTF-8"
        normal_response_object.status_code = 200
        r_g.return_value = normal_response_object

        eq_(appbase.try_get_resource(self.err, None, "http://foo.bar/", "",
                                     binary=True), u"é" * 100)
        self.assert_silent()

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_decode_gzip(self, r_g):
        def compressed_gzip_body():
            stream = cStringIO.StringIO()
            compressor = gzip.GzipFile(fileobj=stream, mode='w')
            compressor.write(u"é".encode('utf-8') * 100)
            compressor.close()
            stream.seek(0)
            return stream

        normal_response_object = Mock()
        # Build an HTTPResponse object like the one requests uses, with
        # a gzip compressed body. `decode_content` needs to be False to
        # properly emulate requests behaviour : it's the caller's
        # responsability to decode, since it's supposed to be a raw stream.
        body = compressed_gzip_body()
        normal_response_object.raw = HTTPResponse(
            status=200, preload_content=False, headers={
            'content-encoding': 'gzip',
            'content-type': 'application/blah; charset=utf-8'
        }, body=body, decode_content=False)
        normal_response_object.encoding = 'UTF-8'
        normal_response_object.status_code = 200
        r_g.return_value = normal_response_object

        eq_(appbase.try_get_resource(self.err, None, "http://foo.bar/", ""),
            u"é" * 100)
        self.assert_silent()

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_empty(self, r_g):
        empty_response = Mock()
        empty_response.raw.read.return_value = ""
        empty_response.encoding = ""
        empty_response.status_code = 200
        r_g.return_value = empty_response

        eq_(appbase.try_get_resource(
                self.err, None, "http://foo.bar/", ""), "")
        self.assert_failed(with_errors=True)

    @patch("appvalidator.testcases.webappbase.requests.get")
    @patch("appvalidator.constants.MAX_RESOURCE_SIZE", 100)
    def test_eventual_404(self, r_g):
        error_response = Mock()
        error_response.raw.read.side_effect = ["x" * 100, ""]
        error_response.encoding = ""
        error_response.status_code = 404
        r_g.return_value = error_response

        appbase.try_get_resource(self.err, None, "http://foo.bar/", "")
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
        self.err.save_resource("packaged", True)
        return manifest

    @patch("appvalidator.testcases.webappbase.test_icon")
    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_icons(self, tgr, test_icon):
        tgr.return_value = "foobar"

        self.setup_manifest()["icons"] = {"32": "fizz"}
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")

        # Icons must be fetched with "binary" keyword argument.
        eq_(tgr.call_args[1]['binary'], True)
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
        tgr.return_value = False
        self.setup_manifest()["launch_path"] = "fizz"
        self.err.save_resource('packaged', False)
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        # Test that we don't warn the dev that their origin exceeds a size
        # limit.
        eq_(tgr.call_args[1]["max_size"], False)

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_launch_path_no_appcache(self, tgr):
        tgr.return_value = """
        <html haldo="trogdor"></html>
        """
        self.setup_manifest()["launch_path"] = "fizz"
        self.err.save_resource('packaged', False)
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        assert not self.err.failed()

    @patch("appvalidator.testcases.webappbase.try_get_resource")
    def test_launch_path_appcache(self, tgr):
        tgr.return_value = """
        <html manifest="hello"></html>
        """
        self.setup_manifest()["launch_path"] = "fizz"
        self.err.save_resource('packaged', False)
        appbase.test_app_resources(self.err, None)
        eq_(tgr.call_args[0][2], "fizz")
        assert self.err.failed(fail_on_warnings=True)

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

        self._test_icon("icon-128.png", "128")
        self.assert_silent()

    def test_pass_gzip(self):
        """
        Since we need to use raw sockets to pull in the data, we don't get
        gzip-uncompressed data back for servers that proactively compress
        assets. This tests that a GZ file can be accepted and pass just the
        same as a standard icon file can.
        """

        self._test_icon("icon-128.png.gz", 128)
        self.assert_silent()

        self._test_icon("icon-128.png.gz", "128")
        self.assert_silent()

    def test_bad_icon(self):
        self._test_icon("corrupt.xpi", 128)
        self.assert_failed(with_errors=True)

    def test_not_square(self):
        self._test_icon("icon-128x64.png", 128)
        self.assert_failed(with_errors=True)

        self.setup_err()
        self._test_icon("icon-128x64.png", "128")
        self.assert_failed(with_errors=True)

    def test_bad_size(self):
        self._test_icon("icon-128.png", 256)
        self.assert_failed(with_errors=True)


class TestURLNormalizer(TestCase):
    """Test that URLs are normalized properly."""

    def setUp(self):
        super(TestURLNormalizer, self).setUp()
        self.setup_err()
        self.err.save_resource("manifest_url", "https://foo.bar/zip/zap.htm")

    def url(self, input, expected):
        def wrap():
            self.setUp()
            normalized = appbase._normalize_url(self.err, input)
            eq_(normalized, expected)
        return wrap

    def test_urls(self):
        yield self.url("path/file.txt", "https://foo.bar/path/file.txt")
        yield self.url("/path/file.txt", "https://foo.bar/path/file.txt")
        yield self.url("file.txt", "https://foo.bar/file.txt")
        yield self.url("/file.txt", "https://foo.bar/file.txt")
        yield self.url("http://nice.try/asdf", "https://foo.bar/asdf")

    def test_nulls(self):
        self.err.save_resource("manifest_url", None)
        eq_(appbase._normalize_url(self.err, '/foo.txt'), '/foo.txt')
