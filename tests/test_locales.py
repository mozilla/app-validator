from nose.tools import eq_

import appvalidator.testcases.locales as locales
from appvalidator.errorbundle import ErrorBundle
from helper import TestCase


def test_canonicalize():
    def test(locale, expected_locale):
        eq_(locales.canonicalize(locale), expected_locale)

    yield test, "en-US", "en-US"
    yield test, "EN-us", "en-US"
    yield test, "EN", "en-US"
    yield test, "en", "en-US"
    # pt-BR is a supported locale, so keep it at that.
    yield test, "pt-BR", "pt-BR"
    yield test, "pt-PT", "pt-PT"
    yield test, "pt-FOO", "pt-PT"


class TestLocales(TestCase):

    def setUp(self):
        self.setup_err()
        self.manifest = {
            "default_locale": "en-US",
            "locales": {},
        }
        self.err.save_resource("manifest", self.manifest)

    def run(self):
        locales.validate_locales(self.err, None)

    def test_passes(self):
        self.run()
        self.assert_silent()

    def test_passes_no_default(self):
        del self.manifest["default_locale"]
        self.run()
        self.assert_silent()

    def test_passes_locales(self):
        self.manifest["locales"]["pt-BR"] = {}
        self.run()
        self.assert_silent()

    def test_warns_locales(self):
        self.manifest["locales"]["foo"] = {}
        self.run()
        self.assert_failed(with_warnings=True)

    def test_warns_bad_default_locale(self):
        self.manifest["default_locale"] = "foobar"
        self.manifest["locales"]["pt-BR"] = {}
        self.run()
        self.assert_failed(with_warnings=True)

    def test_default_locale_invalid(self):
        self.manifest["default_locale"] = "asdf"
        self.run()
        self.assert_failed(with_errors=True)

    def test_locales_locale_invalid(self):
        self.manifest["default_locale"] = "asdf"
        self.manifest["locales"]["foo"] = {}
        self.run()
        self.assert_failed(with_errors=True)

    def test_warngs_invalid_default(self):
        self.manifest["default_locale"] = "en_US"
        self.manifest["locales"]["pt-BR"] = {}
        self.run()
        self.assert_failed(with_warnings=True)

    def test_warngs_invalid_locales(self):
        self.manifest["locales"]["pt_BR"] = {}
        self.run()
        self.assert_failed(with_warnings=True)
