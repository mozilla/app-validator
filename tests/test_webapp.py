# -*- coding: utf-8 -*-
import os
import tempfile
import types

import simplejson as json
from nose.tools import eq_

from helper import TestCase
import appvalidator.constants
from appvalidator.errorbundle import ErrorBundle
from appvalidator.specs.webapps import WebappSpec
import appvalidator.webapp


class TestWebappAccessories(TestCase):
    """
    Test that helper functions for webapp manifests work as they are intended
    to.
    """

    def test_path(self):
        """Test that paths are tested properly for allowances."""

        s = WebappSpec("{}", ErrorBundle())

        eq_(s._path_valid("*"), False)
        eq_(s._path_valid("*", can_be_asterisk=True), True)
        eq_(s._path_valid("/foo/bar"), False)
        eq_(s._path_valid("/foo/bar", can_be_absolute=True), True)
        eq_(s._path_valid("//foo/bar"), False)
        eq_(s._path_valid("//foo/bar", can_be_absolute=True), False)
        eq_(s._path_valid("//foo/bar", can_be_relative=True), False)
        eq_(s._path_valid("http://asdf/"), False)
        eq_(s._path_valid("https://asdf/"), False)
        eq_(s._path_valid("ftp://asdf/"), False)
        eq_(s._path_valid("http://asdf/", can_have_protocol=True), True)
        eq_(s._path_valid("https://asdf/", can_have_protocol=True), True)
        # No FTP for you!
        eq_(s._path_valid("ftp://asdf/", can_have_protocol=True), False)
        eq_(s._path_valid("data:asdf"), False)
        eq_(s._path_valid("data:asdf", can_be_data=True), True)


class WebappBaseTestCase(TestCase):

    def setUp(self):
        super(WebappBaseTestCase, self).setUp()
        self.listed = False

        descr = "Exciting Open Web development action!"
        descr += (1024 - len(descr)) * "_"

        self.data = {
            "version": "1.0",
            "name": "MozBall",
            "description": descr,
            "icons": {
                "16": "/img/icon-16.png",
                "32": "/img/icon-32.png",
                "48": "/img/icon-48.png",
                "60": "/img/icon-60.png",
                "90": "/img/icon-90.png",
                "120": "/img/icon-120.png",
                "128": "/img/icon-128.png",
                "256": "/img/icon-256.png",
            },
            "developer": {
                "name": "Mozilla Labs",
                "url": "http://mozillalabs.com"
            },
            "installs_allowed_from": [
                "https://appstore.mozillalabs.com",
                "HTTP://mozilla.com/AppStore"
            ],
            "launch_path": "/index.html",
            "locales": {
                "es": {
                    "name": "Foo Bar",
                    "description": "¡Acción abierta emocionante del desarrollo",
                    "developer": {
                        "url": "http://es.mozillalabs.com/"
                    }
                },
                "it": {
                    "description": "Azione aperta emozionante di sviluppo di!",
                    "developer": {
                        "url": "http://it.mozillalabs.com/"
                    }
                }
            },
            "default_locale": "en",
            "screen_size": {
                "min_width": "600",
                "min_height": "300"
            },
            "required_features": [
                "touch", "geolocation", "webgl"
            ],
            "orientation": "landscape",
            "fullscreen": "true",
            "type": "web",
        }

        self.resources = [("app_type", "web")]

    def make_privileged(self):
        self.resources = [("app_type", "privileged"),
                          ("packaged", True)]
        self.data["type"] = "privileged"

    def analyze(self):
        """Run the webapp tests on the file."""
        self.detected_type = appvalidator.constants.PACKAGE_WEBAPP
        self.setup_err()

        for resource, value in self.resources:
            self.err.save_resource(resource, value)

        with tempfile.NamedTemporaryFile(delete=False) as t:
            if isinstance(self.data, types.StringTypes):
                t.write(self.data)
            else:
                t.write(json.dumps(self.data))
            name = t.name
        appvalidator.webapp.detect_webapp(self.err, name)
        os.unlink(name)


class TestWebapps(WebappBaseTestCase):
    def test_pass(self):
        """Test that a bland webapp file throws no errors."""
        self.analyze()
        self.assert_silent()

        output = json.loads(self.err.render_json())
        assert "manifest" in output and output["manifest"]

    def test_bom(self):
        """Test that a plain webapp with a BOM won't throw errors."""
        self.setup_err()
        appvalidator.webapp.detect_webapp(
            self.err, "tests/resources/unicodehelper/utf8_webapp.json")
        self.assert_silent()

    def test_fail_parse(self):
        """Test that invalid JSON is reported."""
        self.data = "}{"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_missing_required(self):
        """Test that missing the name element is a bad thing."""
        del self.data["name"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_name(self):
        """Test that the name element is a string."""
        self.data["name"] = ["foo", "bar"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_long_name(self):
        """Test that long names are flagged for truncation in Gaia."""
        self.data["name"] = "This is a long name."
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_long_name(self):
        """Test that long names are flagged for truncation in Gaia."""
        self.data["locales"]["es"]["name"] = "This is a long name."
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_role(self):
        """Test that app may contain role element."""
        self.data["role"] = "input"
        self.analyze()
        self.assert_silent()

    def test_invalid_role(self):
        """Test that app may not contain invalid role element."""
        self.data["role"] = "hello"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_long_name(self):
        """Test that long names are flagged for truncation in Gaia."""
        self.data["name"] = None
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_maxlengths(self):
        """Test that certain elements are capped in length."""
        self.data["name"] = "%" * 129
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_keys(self):
        """Test that unknown elements are flagged"""
        self.data["foobar"] = "hello"
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_warn_extra_keys(self):
        """Test that extra keys are flagged."""
        self.data["locales"]["es"]["foo"] = "hello"
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_icons_not_dict(self):
        """Test that the icons property is a dictionary."""
        self.data["icons"] = ["data:foo/bar.png"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_empty(self):
        """Test that no icons doesn't cause a traceback."""
        self.data["icons"] = {}
        self.analyze()

    def test_icons_size(self):
        """Test that webapp icon sizes must be integers."""
        self.data["icons"]["foo"] = "/foo.png"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_data_url(self):
        """Test that webapp icons can be data URLs."""
        self.data["icons"]["128"] = "data:foo/bar.png"
        self.analyze()
        self.assert_silent()

    def test_icons_relative_url(self):
        """Test that webapp icons cannot be relative URLs."""
        self.data["icons"]["128"] = "foo/bar"
        self.analyze()
        self.assert_silent()

    def test_icons_absolute_url(self):
        """Test that webapp icons can be absolute URLs."""
        def test_icon(self, icon):
            self.setUp()
            self.data["icons"]["128"] = icon
            self.analyze()
            self.assert_silent()

        for icon in ['/foo/bar', 'http://foo.com/bar', 'https://foo.com/bar']:
            yield test_icon, self, icon

    def test_icons_has_60(self):
        del self.data["icons"]["60"]
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_icons_has_min_selfhosted(self):
        del self.data["icons"]["128"]
        self.analyze()
        self.assert_silent()

    def test_icons_has_min_listed(self):
        self.listed = True
        self.data["installs_allowed_from"] = \
                appvalidator.constants.DEFAULT_WEBAPP_MRKT_URLS
        del self.data["icons"]["128"]
        del self.data["icons"]["256"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_icons_has_os_sizes(self):
        del self.data["icons"]["256"]
        self.analyze()
        self.assert_notices()

    def test_no_locales(self):
        """Test that locales are not required."""
        del self.data["locales"]
        self.analyze()
        self.assert_silent()

    def test_no_default_locale_no_locales(self):
        """Test that locales are not required if no default_locale."""
        del self.data["default_locale"]
        del self.data["locales"]
        self.analyze()
        self.assert_silent()

    def test_no_default_locale(self):
        """Test that locales require default_locale."""
        del self.data["default_locale"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_invalid_locale_keys(self):
        """Test that locales only contain valid keys."""
        # Banned locale element.
        self.data["locales"]["es"]["default_locale"] = "foo"
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_invalid_locale_keys_missing(self):
        """Test that locales aren't missing any required elements."""
        del self.data["locales"]["es"]["name"]
        self.analyze()
        self.assert_silent()

    def test_installs_allowed_from_not_list(self):
        """Test that the installs_allowed_from path is a list."""
        self.data["installs_allowed_from"] = "foobar"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_installs_allowed_from_path(self):
        """Test that the installs_allowed_from path is valid."""
        self.data["installs_allowed_from"].append("foo/bar")
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_no_amo_installs_allowed_from(self):
        """Test that installs_allowed_from should include Marketplace."""
        # self.data does not include a marketplace URL by default.
        self.listed = True
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_amo_iaf(self):
        """Test that the various Marketplace URLs work."""

        # Test that the Marketplace production URL is acceptable.
        self.setUp()
        orig_iaf = self.data["installs_allowed_from"]

        def test_iaf(self, iaf, url):
            self.setUp()
            self.data["installs_allowed_from"] = iaf + [url]
            self.analyze()
            self.assert_silent()

        for url in appvalidator.constants.DEFAULT_WEBAPP_MRKT_URLS:
            yield test_iaf, self, orig_iaf, url

    def test_iaf_wildcard(self):
        """Test that installs_allowed_from can contain a wildcard."""
        self.listed = True
        self.data["installs_allowed_from"].append("*")
        self.analyze()
        self.assert_silent()

    def test_installs_allowed_from_protocol(self):
        """
        Test that if the developer includes a URL in the `installs_allowed_from`
        parameter that is a valid Marketplace URL but uses HTTP instead of
        HTTPS, we flag it as using the wrong protocol and not as an invalid URL.
        """
        self.listed = True
        bad_url = appvalidator.constants.DEFAULT_WEBAPP_MRKT_URLS[0].replace(
                "https", "http")

        self.data["installs_allowed_from"] = (bad_url, )
        self.analyze()
        self.assert_failed(with_errors=True)
        self.assert_got_errid(("spec", "webapp", "iaf_bad_mrkt_protocol", ))

    def test_launch_path_packaged(self):
        """Test that the launch path is present in a packaged app."""
        del self.data["launch_path"]
        self.resources.append(('packaged', True))
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_launch_path_not_string(self):
        """Test that the launch path is a string."""
        self.data["launch_path"] = [123]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_launch_path(self):
        """Test that the launch path is valid."""
        self.data["launch_path"] = "data:asdf"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_launch_path_protocol(self):
        """Test that the launch path cannot have a protocol."""
        self.data["launch_path"] = "http://foo.com/bar"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_launch_path_absolute(self):
        """Test that the launch path is absolute."""
        self.data["launch_path"] = "/foo/bar"
        self.analyze()
        self.assert_silent()

    def test_widget_deprecated(self):
        """Test that the widget property is deprecated."""
        self.data["widget"] = {
            "path": "/butts.html",
            "width": 100,
            "height": 200
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_dev_missing(self):
        """Test that the developer property cannot be absent."""
        del self.data["developer"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_dev_not_dict(self):
        """Test that the developer property must be a dict."""
        self.data["developer"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_dev_keys(self):
        """Test that the developer keys are present."""
        del self.data["developer"]["name"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_dev_url(self):
        """Test that the developer keys are correct."""
        self.data["developer"]["url"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_screen_size_missing(self):
        """Test that the 'screen_size' property can be absent."""
        del self.data["screen_size"]
        self.analyze()
        self.assert_silent()

    def test_screen_size_is_dict(self):
        """Test that the 'screen_size' property must be a dict."""
        self.data["screen_size"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_screen_size_contains_pair(self):
        """Test that 'screen_size' must contain at least one key/value pair."""
        self.data["screen_size"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_bad_screen_size_key(self):
        """Test that the 'screen_size' keys are correct."""
        self.data["screen_size"]["max_width"] = "500"
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_bad_screen_size_value(self):
        """Test that the 'screen_size' keys are correct."""
        self.data["screen_size"]["min_width"] = "500px"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_required_features_missing(self):
        """Test that the 'required_features' property can be absent."""
        del self.data["screen_size"]
        self.analyze()
        self.assert_silent()

    def test_required_features_is_list(self):
        """Test that the 'required_features' property must be a list."""
        self.data["required_features"] = "fart"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_required_features_missing(self):
        """Test that 'required_features' can be absent."""
        del self.data["required_features"]
        self.analyze()
        self.assert_silent()

    def test_required_features_empty(self):
        """Test that 'required_features' can be an empty list."""
        self.data["required_features"] = []
        self.analyze()
        self.assert_silent()

    def test_orientation_missing(self):
        """Test that the 'orientation' property can be absent."""
        del self.data["orientation"]
        self.analyze()
        self.assert_silent()

    def test_orientation_list(self):
        """Test that the 'orientation' property can be absent."""
        self.data["orientation"] = ["portrait", "portrait-secondary"]
        self.analyze()
        self.assert_silent()

    def test_orientation_is_string(self):
        """Test that the 'orientation' property must be a string."""
        self.data["orientation"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_cannot_be_empty(self):
        """Test that 'orientation' cannot be an empty string."""
        self.data["orientation"] = ""
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_valid_value(self):
        """Test that 'orientation' must have a valid value."""
        def test_orientation(self, orientation):
            self.setUp()
            self.data["orientation"] = orientation
            self.analyze()
            self.assert_silent()

        for key in ("portrait", "landscape", "portrait-secondary",
                    "landscape-secondary", "portrait-primary",
                    "landscape-primary"):
            yield test_orientation, self, key

    def test_orientation_bad_value(self):
        """Test that 'orientation' cannot have an invalid value."""
        self.data["orientation"] = "fart"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_empty_list(self):
        """Test that 'orientation' cannot be an empty list."""
        self.data["orientation"] = []
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_list_invalid(self):
        """Test that 'orientation' cannot be a list with invalid values."""
        self.data["orientation"] = ["fart"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_list_mixed(self):
        """Test that 'orientation' cannot be a list with mixed values."""
        self.data["orientation"] = ["portrait", "fart", "landscape"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_orientation_list_type(self):
        """Test that 'orientation' cannot be a list with non-strings."""
        self.data["orientation"] = ["portrait", 4]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_valid(self):
        """Test with 'inputs' entries throw no errors."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html',
                'types': ['text']
            },
            'siri': {
                'name': 'Voice Control',
                'description': 'Voice Control Input',
                'launch_path': '/vc.html',
                'types': ['text', 'url']
            }
        }
        self.analyze()
        self.assert_silent()

    def test_inputs_dict_empty(self):
        """Test that 'inputs' may not be empty dict."""
        self.data['inputs'] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_missing_name(self):
        """Test that 'inputs' with an entry missing 'name'."""
        self.data['inputs'] = {
            'input1': {
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html',
                'types': ['text']
            }
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_missing_description(self):
        """Test that 'inputs' with an entry missing 'description'."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'launch_path': '/input1.html',
                'types': ['text']
            }
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_missing_launch_path(self):
        """Test that 'inputs' with an entry missing 'launch_path'."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'types': ['text']
            }
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_missing_types(self):
        """Test that 'inputs' with an entry missing 'types'."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html'
            }
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_empty_types(self):
        """Test that 'inputs' with an entry with empty 'types'."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html',
                'types': []
            }
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_invalid_types(self):
        """Test that 'inputs' with an entry with invalid 'types'."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html',
                'types': ['foo']
            }
        }
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_inputs_dict_entry_locales(self):
        """Test that 'inputs' with an localized entry."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html',
                'types': ['text'],
                'locales': {
                    'es': {
                        'name': 'foo',
                        'description': 'bar'
                    }
                }
            }
        }
        self.analyze()
        self.assert_silent()

    def test_inputs_dict_entry_invalid_locales(self):
        """Test that 'inputs' with an localized entry but contain invalid element."""
        self.data['inputs'] = {
            'input1': {
                'name': 'Symbols',
                'description': 'Symbols Virtual Keyboard',
                'launch_path': '/input1.html',
                'types': ['text'],
                'locales': {
                    'es': {
                        'name': 'foo',
                        'description': 'bar',
                        'foo': 'bar2'
                    }
                }
            }
        }
        self.analyze()
        self.assert_failed(with_warnings=True)

    def test_fullscreen_missing(self):
        """Test that the 'fullscreen' property can be absent."""
        del self.data["fullscreen"]
        self.analyze()
        self.assert_silent()

    def test_fullscreen_is_string(self):
        """Test that the 'fullscreen' property must be a string."""
        self.data["fullscreen"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_fullscreen_cannot_be_empty(self):
        """Test that 'fullscreen' cannot be an empty string."""
        self.data["fullscreen"] = ""
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_fullscreen_valid_value(self):
        """Test that 'fullscreen' must have a valid value."""
        def test_fullscreen(self, value):
            self.setUp()
            self.data["fullscreen"] = key
            self.analyze()
            self.assert_silent()

        for key in ("true", "false", ):
            yield test_fullscreen, self, key

    def test_fullscreen_bad_value(self):
        """Test that 'fullscreen' cannot have an invalid value."""
        self.data["fullscreen"] = "fart"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_type_failed(self):
        """Test that the `type` element must be a recognized value."""

        self.data["type"] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_type_valid(self):
        """Test that the `type` element doesn't fail with valid values."""

        def wrap(self, value):
            self.setUp()
            self.resources.append(("packaged", value != "web"))
            self.data["type"] = value
            self.analyze()
            self.assert_silent()

        for key in ("web", "privileged", "certified", ):
            yield wrap, self, key

    def test_type_not_certified(self):
        """Test that certified apps cannot be listed in the marketplace."""
        self.listed = True
        self.data["type"] = "certified"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_type_web_priv_fail(self):
        """Test that web apps cannot be privileged or certified."""
        self.data["type"] = "web"
        self.resources.append(("packaged", False))
        self.analyze()
        self.assert_silent()

    def test_type_packaged_priv_fail(self):
        """Test that web apps cannot be privileged or certified."""
        self.data["type"] = "privileged"
        self.resources.append(("packaged", True))
        self.analyze()
        self.assert_silent()

    ###########
    # Web activities are tested in tests/test_webapp_activity.py
    ###########

    def test_act_root_type(self):
        """Test that the most basic web activity passes."""

        self.data["activities"] = "wrong type"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_version(self):
        """Test that the version matches the format that we require."""
        def wrap(version, passes):
            self.setUp()
            self.data["version"] = version
            self.analyze()
            if passes:
                self.assert_silent()
            else:
                self.assert_failed(with_errors=True)

        yield wrap, "1.0", True
        yield wrap, "1.0.1", True
        yield wrap, "Poop", True
        yield wrap, "1.0b", True
        yield wrap, "*.*", True
        yield wrap, "1.5-alpha", True
        yield wrap, "1.5_windows", True
        yield wrap, "1.5_windows,x64", True
        yield wrap, "Mountain Lion", False
        yield wrap, "", False
        for char in "`~!@#$%^&()+=/|\\<>":
            yield wrap, char * 3, False

    def set_permissions(self):
        """Fill out the permissions node with every possible permission."""
        self.data["permissions"] = {}
        for perm in set.union(appvalidator.constants.PERMISSIONS['web'],
                              appvalidator.constants.PERMISSIONS['privileged'],
                              appvalidator.constants.PERMISSIONS['certified']):
            self.data["permissions"][perm] = {
                "description": "Required to make things good."
            }
            if perm in WebappSpec.PERMISSIONS_ACCESS:
                self.data["permissions"][perm]["access"] = (
                    WebappSpec.PERMISSIONS_ACCESS[perm][0])

    def test_permissions_full(self):
        self.set_permissions()
        self.analyze()
        self.assert_silent()

    def test_permissions_extra_invalid(self):
        self.set_permissions()
        self.data["permissions"]["foo"] = {"description": "lol"}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_permissions_missing_desc(self):
        self.set_permissions()
        self.data["permissions"]["alarm"] = {}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_permissions_missing_access(self):
        self.set_permissions()
        del self.data["permissions"]["contacts"]["access"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_permissions_invalid_access(self):
        self.set_permissions()
        self.data["permissions"]["contacts"]["access"] = "asdf"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_permissions_wrong_access(self):
        self.set_permissions()
        # This access type isn't available for the `settings` permission.
        self.data["permissions"]["settings"]["access"] = "createonly"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_csp(self):
        self.data['csp'] = 'this is the csp policy. it can be a string.'
        self.analyze()
        self.assert_silent()

    def test_description_long(self):
        self.data['description'] = 'x' * 1025
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_locale_description_long(self):
        self.data['locales']['es']['description'] = u'×' * 1025
        self.analyze()
        self.assert_failed(with_errors=True)
        assert 'locales > es > description' in (
            self.err.errors[0]['description'][-1])

    def test_appcache_path_packaged(self):
        self.data["appcache_path"] = '/foo.bar'
        self.analyze()
        self.assert_silent()

        self.resources.append(("packaged", True))
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_messages_not_list(self):
        self.data['messages'] = "foo"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_messages_obj_not_obj(self):
        self.data['messages'] = ["foo"]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_messages_multiple_keys(self):
        self.data['messages'] = [{"a": "1", "b": "2"}]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_messages_pass(self):
        self.data['messages'] = [{"key": "val"}, {"key": "val"}]
        self.analyze()
        self.assert_silent()

    def test_redirects_pass(self):
        self.data['redirects'] = [
            {"to": "asdf", "from": "qwer"},
            {"to": "asdf", "from": "qwer"},
        ]
        self.analyze()
        self.assert_silent()

    def test_redirects_type(self):
        self.data['redirects'] = 'asdf'
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_redirects_subtype(self):
        self.data['redirects'] = [
            'asdf',
            {"to": "asdf", "from": "qwer"},
        ]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_redirects_required_nodes(self):
        self.data['redirects'] = [
            {"bar": "asdf", "foo": "qwer"},
            {"to": "asdf", "from": "qwer"},
        ]
        self.analyze()
        self.assert_failed(with_errors=True)


    def test_redirects_missing_nodes(self):
        self.data['redirects'] = [
            {"to": "asdf"},
            {"to": "asdf", "from": "qwer"},
        ]
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_unprivileged(self):
        self.data['origin'] = 'app://domain.com'
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_pass(self):
        self.make_privileged()
        self.data['origin'] = 'app://domain.com'
        self.analyze()
        self.assert_silent()

    def test_origin_dashes(self):
        self.make_privileged()
        self.data["origin"] = "app://my-domain.com"
        self.analyze()
        self.assert_silent()

    def test_origin_subdomains(self):
        self.make_privileged()
        self.data["origin"] = "app://sub.domain.com"
        self.analyze()
        self.assert_silent()

    def test_origin_non_fqdn(self):
        self.make_privileged()
        self.data["origin"] = "app://hello"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_type(self):
        self.make_privileged()
        self.data["origin"] = 123
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_format(self):
        self.make_privileged()
        self.data["origin"] = "http://asdf"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_path(self):
        self.make_privileged()
        self.data["origin"] = "app://domain.com/path"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_path_trailing_slash(self):
        self.make_privileged()
        self.data["origin"] = "app://domain.com/"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_origin_allowed(self):
        self.make_privileged()
        self.data["origin"] = "app://marketplace.firefox.com"
        self.analyze()
        self.assert_silent()

    def test_origin_banned(self):
        for origin in ("app://system.gaiamobile.org", "app://mozilla.org"):
            self.make_privileged()
            self.data["origin"] = origin
            self.analyze()
            self.assert_failed(with_errors=True)

    def test_chrome(self):
        self.data["chrome"] = {"navigation": True}
        self.analyze()
        self.assert_silent()

    def test_chrome_alt(self):
        self.data["chrome"] = {"navigation": False}
        self.analyze()
        self.assert_silent()

    def test_chrome_bad_navigation(self):
        self.data["chrome"] = {"navigation": 123}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_chrome_bad_keys(self):
        self.data["chrome"] = {"haldo": 123}
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_chrome_bad_type(self):
        self.data["chrome"] = []
        self.analyze()
        self.assert_failed(with_errors=True)
