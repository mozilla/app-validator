from nose.tools import eq_

import appvalidator.testcases.locales as locales
from helper import TestCase


def test_canonicalize():
    eq_(locales.canonicalize("en-US"), "en-US")
    eq_(locales.canonicalize("EN-us"), "en-US")
    eq_(locales.canonicalize("EN"), "en-US")
    eq_(locales.canonicalize("en"), "en-US")
    # pt-BR is a supported locale, so keep it at that.
    eq_(locales.canonicalize("pt-BR"), "pt-BR")
    eq_(locales.canonicalize("pt-PT"), "pt-PT")
    eq_(locales.canonicalize("pt-FOO"), "pt-PT")


class TestLocales(TestCase):

    def setUp(self):
        self.setup_err()
        self.manifest = {
            'default_locale': 'en-US',
            'locales': {},
        }
        self.err.save_resource('manifest', self.manifest)

    def run(self):
        locales.validate_locales(self.err, None)

    def test_passes(self):
        self.run()
        self.assert_silent()

    def test_passes_no_default(self):
        del self.manifest['default_locale']
        self.run()
        self.assert_silent()

    def test_passes_locales(self):
        self.manifest['locales']['pt-BR'] = {}
        self.run()
        self.assert_silent()

    def test_passes_default_locale(self):
        self.manifest['default_locale'] = 'pt-BR'
        self.run()
        self.assert_silent()

    def test_passes_default_locale_hidden(self):
        self.manifest['default_locale'] = 'af'
        self.run()
        self.assert_silent()

    def test_passes_default_locale_shorter(self):
        self.manifest['default_locale'] = 'en'
        self.run()
        self.assert_silent()

    def test_warns_locales(self):
        self.manifest['locales']['foo'] = {}
        self.run()
        # Only a warning since the rest of the content is fine.
        self.assert_failed(with_warnings=True)

    def test_bad_default_locale(self):
        self.manifest['default_locale'] = 'foobar'
        self.manifest['locales']['pt-BR'] = {}
        self.run()
        # We have an invalid default_locale. Even though we have a valid
        # 'locales', we should return an error.
        self.assert_failed(with_errors=True)

    def test_default_locale_invalid(self):
        self.manifest['default_locale'] = 'asdf'
        self.run()
        # Invalid default_locale, we should return an error.
        self.assert_failed(with_errors=True)

    def test_default_locale_should_be_unsupported_but_language_is(self):
        self.manifest['default_locale'] = 'fr-BR'
        self.run()
        # Valid because the language part is good.
        self.assert_silent()

    def test_default_locale_invalid_with_locales_valid(self):
        self.manifest['default_locale'] = 'en_US'  # Should use '-', not '_'.
        self.manifest['locales']['pt-BR'] = {}
        self.run()
        # We have an invalid default_locale. Even though we have a valid
        # 'locales', we should return an error.
        self.assert_failed(with_errors=True)

    def test_default_locale_and_locales_invalid(self):
        self.manifest['default_locale'] = 'asdf'
        self.manifest['locales']['foo'] = {}
        self.run()
        # Both are invalid, so we should return an error.
        self.assert_failed(with_errors=True)

    def test_default_locale_wrong_format(self):
        self.manifest['default_locale'] = 'pt_BR'
        self.run()
        # Invalid, should use '-', not '_'.
        self.assert_failed(with_errors=True)

    def test_warns_invalid_locales(self):
        self.manifest['locales']['pt_BR'] = {}
        self.run()
        # Invalid, should use '-', not '_', but since it's just one of the
        # locales and not the default one, a warning is enough.
        self.assert_failed(with_warnings=True)
