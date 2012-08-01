import json

from . import constants
from errorbundler import ErrorBundle
import loader
import submain
import webapp


def validate_app(data, listed=True, market_urls=None):
    """
    A handy function for validating apps.

    `data`:
        A copy of the manifest as a JSON string.
    `listed`:
        Whether the app is headed for the app marketplace.
    `market_urls`:
        A list of URLs to use when validating the `installs_allowed_from`
        field of the manifest. Does not apply if `listed` is not set to `True`.

    Notes:
    - App validation is always determined because there is only one tier.
    - Spidermonkey paths are not accepted by this function because we don't
      perform JavaScript validation on webapps.
    - We don't accept a flag for compatibility because there are no
      compatibility tests for apps, nor will there likely ever be. The same
      goes for associated parameters (i.e.: for_appversions).
    - `approved_applications` is not set because apps are not bound to
      individual Mozilla apps.
    """
    bundle = ErrorBundle(listed=listed, determined=True)

    # Set the market URLs.
    set_market_urls(market_urls)

    webapp.detect_webapp_string(bundle, data)
    return format_result(bundle, "json")


def format_result(bundle, format):
    # Write the results to the pipe
    formats = {"json": lambda b: b.render_json()}
    if format is not None:
        return formats[format](bundle)
    else:
        return bundle


def set_market_urls(market_urls=None):
    if market_urls is not None:
        constants.DEFAULT_WEBAPP_MRKT_URLS = market_urls

