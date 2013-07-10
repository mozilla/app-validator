from . import register_test
from appvalidator.constants import SHORT_LOCALES, SUPPORTED_LOCALES


def canonicalize(locale):
    # Format the locale properly.
    if "-" in locale:
        language, region = locale.split('-', 1)
    else:
        language = locale
        region = ""

    language = language.lower()
    region = region.upper()
    locale = '%s-%s' % (language, region)

    if locale in SUPPORTED_LOCALES:
        return locale

    if language in SUPPORTED_LOCALES:
        return language

    if language in SHORT_LOCALES:
        return SHORT_LOCALES[language]

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
        locales.add(manifest["default_locale"])

    if "locales" in manifest:
        for locale in manifest["locales"]:
            locales.add(locale)

    err.save_resource("locales", locales)

    if not locales:
        return

    if not any(canonicalize(loc) in SUPPORTED_LOCALES for loc in locales):
        err.error(
            err_id=("locales", "none_supported"),
            error="No supported locales provided.",
            description=["None of the locales provided in the manifest are "
                         "supported by the Firefox Marketplace. At least one "
                         "supported locale must be provided in the manifest.",
                         "Provided locales: %s" % ", ".join(locales)])
        return

    for locale in locales:
        if canonicalize(locale) not in SUPPORTED_LOCALES:
            err.warning(
                err_id=("locales", "not_supported"),
                warning="Unsupported locale provided.",
                description=["An locale which is not supported by the Firefox "
                             "Marketplace was specified in the manifest. The "
                             "information listed in this locale will not be "
                             "stored or displayed to users.",
                             "Unsupported locale: %s" % locale])
