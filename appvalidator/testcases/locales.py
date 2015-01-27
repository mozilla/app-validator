from . import register_test
from appvalidator.constants import (HIDDEN_LANGUAGES, SHORTER_LANGUAGES,
                                    SUPPORTED_LANGUAGES)


# The validator accepts every language supported by Marketplace, even hidden
# ones.
ALL_SUPPORTED_LANGUAGES = set(SUPPORTED_LANGUAGES + HIDDEN_LANGUAGES)


def canonicalize(locale):
    """Reformat locale with wrong capitalization"""
    if "-" in locale:
        language, region = locale.split('-', 1)
    else:
        language = locale
        region = ""

    language = language.lower()
    region = region.upper()
    locale = '%s-%s' % (language, region)

    if locale in ALL_SUPPORTED_LANGUAGES:
        return locale

    if language in ALL_SUPPORTED_LANGUAGES:
        return language

    if language in SHORTER_LANGUAGES:
        return SHORTER_LANGUAGES[language]

    return locale


@register_test(tier=2)
def validate_locales(err, package=None):
    # Double check that the validation hasn't failed. We don't want to get
    # invalid object types throwing tracebacks from the JSON.
    if err.failed(fail_on_warnings=False):
        return

    manifest = err.get_resource("manifest")
    if not manifest:
        return

    def inspect_value(value):
        if "_" in value:
            err.warning(
                err_id=("locales", "probably_wrong"),
                warning="Potentially invalid locale used.",
                description=["A locale was detected that doesn't appear to be "
                             "valid. Locales should be in the form of "
                             "`xx-YY`. Hyphens should be used, not "
                             "underscores.",
                             "Locale: %s" % value])

    locales = set()
    if "default_locale" in manifest:
        default_locale = manifest["default_locale"]
        locales.add(default_locale)
        # Since default_locale will be used by the Marketplace to decide which
        # locale the name/description from the manifest are saved in, it's
        # crucial for it to be valid - raise an error if it's an invalid or
        # unsupported locale, not just a warning.
        if canonicalize(default_locale) not in ALL_SUPPORTED_LANGUAGES:
            err.error(
                err_id=("default_locale", "not_supported"),
                error="Unsupported default_locale provided.",
                description=["The default_locale provided in the manifest is "
                             "not supported by the Firefox Marketplace. If a "
                             "default_locale is provided, it must be be a "
                             "supported one.",
                             "Provided defaut_locale: %s" % default_locale])

    if "locales" in manifest:
        locales.update(manifest["locales"].keys())

    err.save_resource("locales", locales)

    if not locales:
        return

    if not any(canonicalize(l) in ALL_SUPPORTED_LANGUAGES for l in locales):
        err.error(
            err_id=("locales", "none_supported"),
            error="No supported locales provided.",
            description=["None of the locales provided in the manifest are "
                         "supported by the Firefox Marketplace. At least one "
                         "supported locale must be provided in the manifest.",
                         "Provided locales: %s" % ", ".join(locales)])
        return

    for locale in locales:
        if canonicalize(locale) not in ALL_SUPPORTED_LANGUAGES:
            err.warning(
                err_id=("locales", "not_supported"),
                warning="Unsupported locale provided.",
                description=["A locale which is not supported by the Firefox "
                             "Marketplace was specified in the manifest. The "
                             "information listed in this locale will not be "
                             "stored or displayed to users.",
                             "Unsupported locale: %s" % locale])

    # If present, languages-provided also need to be using supported languages.
    languages_provided = set(manifest.get("languages-provided", {}).keys())
    for language in languages_provided:
        if canonicalize(language) not in ALL_SUPPORTED_LANGUAGES:
            err.error(
                err_id=("languages-provided", "not_supported"),
                error="Unsupported language provided.",
                description=["A language which is not supported by the Firefox"
                             " Marketplace was specified in the "
                             "`languages-provided` object in your manifest.",
                             "Unsupported language: %s" % language])
