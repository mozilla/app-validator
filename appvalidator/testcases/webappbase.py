import base64
import gzip
import urlparse
from cStringIO import StringIO

import requests
from PIL import Image

from . import register_test
from .. import constants
from ..webapp import detect_webapp_string
from markup.remote import RemoteHTMLParser


MANIFEST_URL = "https://developer.mozilla.org/docs/Web/Apps/Manifest#%s"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0"
}


@register_test(tier=1)
def test_app_manifest(err, package):

    if not err.get_resource("packaged"):
        # This is done by the validate_*() functions.
        return

    if "manifest.webapp" not in package:
        return err.error(
            err_id=("webappbase", "test_app_manifest", "missing_manifest"),
            error="Packaged app missing manifest",
            description=["All apps must contain an app manifest file.",
                         "Attempted to find a manifest at `/manifest.webapp`, "
                         "but no file was found."])

    webapp = detect_webapp_string(err, package.read("manifest.webapp"))
    err.save_resource("manifest", webapp)
    if webapp:
        err.save_resource("app_type", str(webapp.get("type", "web")).lower())


@register_test(tier=2)
def test_permissions(err, package):

    if (not err.get_resource("permissions") or
        not err.get_resource("manifest")):
        return

    app_type = err.get_resource("app_type")
    packaged = err.get_resource("packaged")

    def error(permission):
        err.error(
            err_id=("webappbase", "test_permissions", "unauthorized"),
            error="App requested unavailable permission",
            description=["A permission requested by the app is not available "
                         "for the app's type. See %s for more information." %
                             MANIFEST_URL % "type",
                         "Requested permission: %s" % permission,
                         "App's type: %s" % app_type],
            filename="manifest.webapp" if packaged else "")

    if app_type == "web":
        for perm in err.get_resource("permissions"):
            if perm not in constants.PERMISSIONS["web"]:
                error(perm)
    elif app_type == "privileged":
        available_perms = (constants.PERMISSIONS["web"] |
                           constants.PERMISSIONS["privileged"])

        for perm in err.get_resource("permissions"):
            if perm not in available_perms:
                error(perm)


class DataURIException(Exception):
    pass


def try_get_data_uri(data_url):
    # Strip off the leading "data:"
    data_url = data_url[5:]

    mime = None
    if ";" in data_url:
        mime, data_url = data_url.split(";", 1)
    encoding = None
    if "," in data_url:
        encoding, data_url = data_url.split(",", 1)

    if not encoding:
        # Don't decode unencoded strings.
        return data_url

    try:
        data_url = str(data_url)  # Because Python.
        decoded = base64.urlsafe_b64decode(data_url)
    except (TypeError, ValueError):
        if mime:
            raise DataURIException(
                "Could not decode `data:` URI with MIME `%s` encoded as `%s`" %
                (mime, encoding))
        else:
            raise DataURIException("Could not decode `data:` URI")
    else:
        return decoded


def _normalize_url(err, url):
    manifest_url = err.get_resource("manifest_url")
    if not manifest_url:
        return url

    p_url = urlparse.urlparse(url)
    p_defurl = urlparse.urlparse(manifest_url)

    return urlparse.urlunparse(p_defurl[:2] + p_url[2:])


def try_get_resource(err, package, url, filename, resource_type="URL",
                     max_size=True, simulate=False):

    # Try to process data URIs first.
    if url.startswith("data:"):
        try:
            return try_get_data_uri(url)
        except DataURIException as e:
            err.error(
                err_id=("resources", "data_uri_error"),
                error=str(e),
                description="A `data:` URI referencing a %s could not be "
                            "opened." % resource_type,
                filename=filename)
        return

    # Kill hashes in URLs.
    if "#" in url:
        url, _ = url.split("#", 1)

    # Pull in whatever packaged app resources are required.
    if "://" not in url:
        if err.get_resource("packaged"):
            url = url.lstrip("/")
            try:
                return package.read(url)
            except Exception:
                err.error(
                    err_id=("resources", "packaged", "not_found"),
                    error="Resource in packaged app not found.",
                    description=["A %s within a packaged app is referenced, "
                                 "but the path used does not point to a valid "
                                 "item in the package." % resource_type,
                                 "Requested resource: %s" % url],
                    filename=filename)
                return
        else:
            url = _normalize_url(err, url)

    if simulate:
        return

    http_cache = err.get_or_create('http_cache', {})
    if url in http_cache:
        return http_cache[url]

    def generic_http_error():
        err.error(
            err_id=("resources", "null_response"),
            error="Error while requesting %s" % resource_type,
            description=["A remote resource was requested, but an error "
                         "prevented the request from completing. This may "
                         "include connection, DNS, or HTTP issues.",
                         "Requested resource: %s" % url],
            filename=filename)

    try:
        request = requests.get(url, stream=True, allow_redirects=True,
                               timeout=3, headers=HEADERS)
        data = request.raw.read(constants.MAX_RESOURCE_SIZE)
        # Check that there's not more data than the max size.
        if max_size and request.raw.read(1):
            err.error(
                err_id=("resources", "too_large"),
                error="Resource too large",
                description=["A requested resource returned too much data. "
                             "File sizes are limited to %dMB." %
                                 (constants.MAX_RESOURCE_SIZE / 1204 / 1024),
                             "Requested resource: %s" % url],
                filename=filename)
            return

        try:
            request.raw.close()
        except AttributeError:
            # Some versions of requests don't support close().
            pass

        http_cache[url] = data

        if not data or request.status_code != 200:
            generic_http_error()

        return data

    except requests.exceptions.MissingSchema:
        if (not err.get_resource("packaged") and
            not err.get_resource("manifest_url")):
            err.warning(
                err_id=("resources", "missing_schema"),
                warning="Unable to fetch resource",
                description=["A relative URL was encountered, but because "
                             "the full URL of the manifest is not known, it "
                             "is not possible to fetch the resources. You "
                             "can provide the URL to fix this issue.",
                             "URL: %s" % url],
                filename=filename)
            return
        err.error(
            err_id=("resources", "invalid_url", "schema"),
            error="Invalid URL",
            description=["While attempting to retrieve a remote resource, "
                         "an invalid URL was encountered. All URLs must "
                         "contain a schema.",
                         "URL: %s" % url],
            filename=filename)
    except requests.exceptions.InvalidSchema:
        err.error(
            err_id=("resources", "invalid_url", "bad_schema"),
            error="Invalid URL Schema",
            description=["While attempting to retrieve a remote resource, "
                         "an invalid URL was encountered. The URL uses an "
                         "invalid schema.",
                         "URL: %s" % url],
            filename=filename)
    except requests.exceptions.URLRequired:
        err.error(
            err_id=("resources", "invalid_url", "none"),
            error="Invalid URL",
            description=["While attempting to retrieve a remote resource, "
                         "an invalid URL was encountered.",
                         "URL: %s" % url],
            filename=filename)
    except requests.exceptions.TooManyRedirects:
        err.error(
            err_id=("resources", "too_many_redirects"),
            error="Too many redirects for %s" % resource_type,
            description=["While attempting to retrieve a remote resource, "
                         "too many redirects were encountered. There should "
                         "never be more than a few redirects present at a "
                         "permanent URL in an app.",
                         "Requested resource: %s" % url],
            filename=filename)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError):
        generic_http_error()

    # Save the failed request to the cache.
    http_cache[url] = None


def test_icon(err, data, url, size):
    try:
        size = int(size)
    except ValueError:
        # This is handled elsewhere.
        return

    try:
        icon = Image.open(data)
        icon.verify()
    except IOError, e:
        try:
            name = url.split('/')[-1]
            data.seek(0)  # Rewind the StringIO
            gzf = gzip.GzipFile(name, 'rb', fileobj=data)
            icon = Image.open(gzf)
            icon.verify()

        except IOError, e:
            err.error(
                err_id=("resources", "icon", "ioerror"),
                error="Could not read icon file.",
                description=["A downloaded icon file could not be opened. It "
                             "may contain invalid or corrupt data. Icons may "
                             "be only JPG or PNG images.",
                             "%dpx icon (%s)" % (size, url)])
        finally:
            if gzf:
                gzf.close()
    else:
        width, height = icon.size
        if width != height:
            err.error(
                err_id=("resources", "icon", "square"),
                error="Icons must be square.",
                description=["A downloaded icon was found to have a different "
                             "width and height. All icons must be square.",
                             "%dpx icon (%s)" % (size, url),
                             "Dimensions: %d != %d" % (width, height)],
                filename="manifest.webapp")
        elif width != size:
            err.error(
                err_id=("resources", "icon", "size"),
                error="Icon size %spx does not match." % size,
                description=["A downloaded icon was found to have a different "
                             "width and height than the size that it said it "
                             "was.",
                             "[Purported] %dpx icon (%s)" % (size, url),
                             "Found size: %dpx" % width],
                filename="manifest.webapp")


@register_test(tier=2)
def test_app_resources(err, package):

    # Do not test app resources if something else failed.
    if err.errors:
        return

    manifest = err.get_resource("manifest")
    if not manifest:
        return

    # Test the icons in the manifest. The manifest validator should have thrown
    # a hard error if this isn't a dict, so this won't ever be reached if it'll
    # otherwise fail with subscript errors.
    icon_urls = set()
    icons = manifest.get("icons", {}).items()
    for icon_size, url in icons:

        try:
            icon_size = int(icon_size)
        except ValueError:
            # There will be an error for this someplace else.
            continue

        # Don't test the same icon URL twice.
        if url in icon_urls:
            continue
        elif len(icon_urls) == constants.ICON_LIMIT:
            # If we're going in and there are already ten icons, that's a
            # problem.
            err.warning(
                err_id=("resources", "icon", "count"),
                warning="Too many icon resources.",
                description=["The app's manifest file contains more than %d "
                             "icons. Including too many icons could put "
                             "unnecessary load on a web server." %
                                 constants.ICON_LIMIT,
                             "Found %d icons." % len(icons)],
                filename="manifest.webapp")
            break

        icon_data = try_get_resource(err, package,
                                     url, "manifest.webapp", "icon")
        if not icon_data:
            continue

        test_icon(err, data=StringIO(icon_data), url=url, size=icon_size)
        icon_urls.add(url)

    if "launch_path" in manifest:
        launch_page = try_get_resource(
            err, package, manifest["launch_path"], filename="manifest.webapp",
            resource_type="launch_path", max_size=False)
        if launch_page and not err.get_resource("packaged"):
            parser = RemoteHTMLParser(err)
            parser.feed(launch_page)

            if ("appcache" in err.metadata and
                not manifest.get("appcache_path")):
                err.warning(
                    err_id=("resources", "appcache", "found_hosted"),
                    warning="Appcache manifest found",
                    description=[
                        "An appcache manifest was found in the remote "
                        "`launch_path`, but there was no `appcache_path` "
                        "listed in the manifest. Without an `appcache_path`, "
                        "the app will not be available to users offline.",
                        "Found appcache: %s" % err.metadata["appcache"],
                        "See more: %s" % MANIFEST_URL % "appcache_path"])

    if "appcache_path" in manifest:
        try_get_resource(err, package, manifest["appcache_path"],
                         filename="manifest.webapp", resource_type="manifest",
                         max_size=False)

    def test_developer(branch):
        if branch and "url" in branch:
            try_get_resource(err, package, branch["url"],
                             filename="manifest.webapp",
                             resource_type="developer url",
                             max_size=False, simulate=True)

    test_developer(manifest.get("developer"))
    for locale, locale_data in manifest.get("locales", {}).items():
        test_developer(locale_data.get("developer"))
