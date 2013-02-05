import hashlib

import markup.csstester as testendpoint_css
import markup.markuptester as testendpoint_markup
import scripting as testendpoint_js
from . import register_test
from .. import unicodehelper
from ..constants import *
from ..contextgenerator import ContextGenerator


FLAGGED_FILES = set([".DS_Store", "Thumbs.db", "desktop.ini",
                     "_vti_cnf"])
FLAGGED_EXTENSIONS = set([".orig", ".old", ".tmp", "~"])

with open(os.path.join(os.path.dirname(__file__), "hashes.txt")) as f:
    hash_blacklist = set(map(str.rstrip, f))


@register_test(tier=2)
def test_packed_packages(err, package=None):

    if not package:
        return

    processed_files = 0
    pretested_files = err.get_resource("pretested_files") or []

    # Iterate each item in the package.
    for name in package:

        # Warn for things like __MACOSX directories and .old files.
        if ("__MACOSX" in name or
            name.split("/")[-1].startswith(".")):
            err.warning(
                err_id=("testcases_content", "test_packed_packages",
                        "hidden_files"),
                warning="Hidden files and folders flagged",
                description="Hidden files and folders can make the review process "
                            "difficult and may contain sensitive information "
                            "about the system that generated the zip. Please "
                            "modify the packaging process so that these files "
                            "aren't included.",
                filename=name)
            continue
        elif (any(name.endswith(ext) for ext in FLAGGED_EXTENSIONS) or
              name in FLAGGED_FILES):
            err.warning(
                err_id=("testcases_content", "test_packaged_packages",
                        "flagged_files"),
                warning="Flagged filename found",
                description="Files were found that are either unnecessary "
                            "or have been included unintentionally. They "
                            "should be removed.",
                filename=name)
            continue

        # Skip the file if it's in the pre-tested file resources.
        if name in pretested_files:
            continue

        # Read the file from the archive if possible.
        file_data = u""
        try:
            file_data = package.read(name)
        except KeyError:  # pragma: no cover
            pass

        # Skip over whitelisted hashes unless we are checking for compatibility.
        hash = hashlib.sha1(file_data).hexdigest()
        if hash in hash_blacklist:
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

    return processed_files


def _process_file(err, package, name, file_data):
    """Process a single file's content tests."""

    name_lower = name.lower()

    if name_lower.endswith((".css", ".js", ".xml", ".html", ".xhtml")):

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

    return False
