import json

import unicodehelper
from .specs.webapps import WebappSpec


def detect_webapp(err, package):
    """Detect, parse, and validate a webapp manifest."""

    # Parse the file.
    with open(package, mode="r") as f:
        detect_webapp_string(err, f.read())


def detect_webapp_string(err, data):
    """Parse and validate a webapp based on the string version of the provided
    manifest.

    """

    try:
        u_data = unicodehelper.decode(data)
        webapp = json.loads(u_data)

    except ValueError as exc:
        err.error(
            err_id=("webapp", "detect_webapp", "parse_error"),
            error="JSON Parse Error",
            description=["The webapp extension could not be parsed due to a "
                         "syntax error in the JSON.",
                         unicode(exc)])

    else:
        ws = WebappSpec(webapp, err)
        ws.validate()

        def long_name_warning(appendix=None):
            if appendix:
                appendix = [appendix]
            else:
                appendix = []
            err.warning(
                err_id=("webapp", "b2g", "name_truncated"),
                warning="App name may be truncated on Firefox OS devices.",
                description=["Your app's name is long enough to possibly be "
                             "truncated on Firefox OS devices. Consider using a "
                             "shorter name for your app.",
                             "App names may be truncated after 12 "
                             "characters."] + appendix)

        def test_name(locale, appendix=None):
            if not isinstance(locale, dict):
                return
            name = locale.get("name")
            # This magic number brought to you by @cvan (see bug 770755)
            # Updated 11/21/12: Bumped to 12 because Gaia is different.
            if name and isinstance(name, (str, unicode)) and len(name) > 12:
                long_name_warning(appendix)

        test_name(webapp)
        locales = webapp.get("locales")
        if locales and isinstance(locales, dict):
            for locale in locales:
                test_name(locales[locale], 'Seen in the "%s" locale.' % locale)

        # If the manifest is still good, save it
        if not err.failed(fail_on_warnings=False):
            err.save_resource("manifest", webapp)

        return webapp
