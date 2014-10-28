import hashlib

import markup.csstester as testendpoint_css
import markup.markuptester as testendpoint_markup
import scripting as testendpoint_js
from . import register_test
from .. import unicodehelper
from ..constants import *


FLAGGED_FILES = set([".DS_Store", "Thumbs.db", "desktop.ini",
                     "_vti_cnf"])
FLAGGED_EXTENSIONS = set([".orig", ".old", ".tmp", "~"])


with open(os.path.join(os.path.dirname(__file__), "hashes.txt")) as f:
    hashes_whitelist = set([s.strip().split(None, 1)[0] for s in f])


@register_test(tier=2)
def test_packed_packages(err, package=None):

    if not package:
        return

    processed_files = 0
    garbage_files = 0

    # Iterate each item in the package.
    for name in package:
        file_info = package.info(name)
        file_name = file_info["name_lower"]
        file_size = file_info["size"]

        if "__MACOSX" in name or file_name[0] in (".", "_", ):
            err.warning(
                err_id=("testcases_content", "test_packed_packages",
                        "hidden_files"),
                warning="Unused files or directories flagged.",
                description="Hidden files and folders can make the review process "
                            "difficult and may contain sensitive information "
                            "about the system that generated the zip. Please "
                            "modify the packaging process so that these files "
                            "aren't included.",
                filename=name)
            garbage_files += file_size
            continue
        elif (any(name.endswith(ext) for ext in FLAGGED_EXTENSIONS) or
              name in FLAGGED_FILES):
            err.warning(
                err_id=("testcases_content", "test_packaged_packages",
                        "flagged_files"),
                warning="Garbage file detected",
                description="Files were found that are either unnecessary "
                            "or have been included unintentionally. They "
                            "should be removed.",
                filename=name)
            garbage_files += file_size
            continue

        # Read the file from the archive if possible.
        file_data = u""
        try:
            file_data = package.read(name)
        except KeyError:
            pass

        # Skip over whitelisted hashes - only applies to .js files for now.
        if name.endswith('.js'):
            file_data = file_data.replace("\r\n", "\n")
            if hashlib.sha256(file_data).hexdigest() in hashes_whitelist:
                continue

        # Process the file.
        processed = _process_file(err, package, name, file_data)
        # If the file is processed, it will return True. If the process goes
        # badly, it will return False. If the processing is skipped, it returns
        # None. We should respect that.
        if processed is None:
            continue

        # This aids in creating unit tests.
        processed_files += 1

    if garbage_files >= MAX_GARBAGE:
        err.error(
            err_id=("testcases_content", "garbage"),
            error="Too much garbage in package",
            description="Your app contains too many unused or garbage files. "
                        "These include temporary files, 'dot files', IDE and "
                        "editor backup and configuration, and operating "
                        "system hidden files. They must be removed before "
                        "your app can be submitted.")

    return processed_files


def _process_file(err, package, name, file_data):
    """Process a single file's content tests."""

    name_lower = name.lower()

    if not name_lower.endswith((".css", ".js", ".xml", ".html", ".xhtml")):
        return False

    if not file_data:
        return None

    # Convert the file data to unicode
    file_data = unicodehelper.decode(file_data)

    if name_lower.endswith(".css"):
        testendpoint_css.test_css_file(err, name, file_data)

    elif name_lower.endswith(".js"):
        testendpoint_js.test_js_file(err, name, file_data)

    elif name_lower.endswith((".xml", ".html", ".xhtml")):
        p = testendpoint_markup.MarkupParser(err)
        p.process(name, file_data, package.info(name)["extension"])

    return True


@register_test(tier=2)
def test_cordova(err, package=None):

    if not package:
        return

    err.metadata["cordova"] = "www/cordova.js" in package
