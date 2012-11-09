"Constants that will be used across files."

import json
import os

# Package type constants.
PACKAGE_ANY = 0
PACKAGE_WEBAPP = 8
PACKAGE_PACKAGED_WEBAPP = 9

SPIDERMONKEY_INSTALLATION = os.environ.get("SPIDERMONKEY_INSTALLATION")

DEFAULT_WEBAPP_MRKT_URLS = ["https://marketplace.firefox.com",
                            "https://marketplace-dev.allizom.org"]
BUGZILLA_BUG = "https://bugzilla.mozilla.org/show_bug.cgi?id=%d"

DEFAULT_TIMEOUT = 60

MAX_RESOURCE_SIZE = 2 * 1024 * 1024

# Graciously provided by @kumar in bug 614574
if (not SPIDERMONKEY_INSTALLATION or
    not os.path.exists(SPIDERMONKEY_INSTALLATION)):
    for p in os.environ.get("PATH", "").split(":"):
        SPIDERMONKEY_INSTALLATION = os.path.join(p, "js")
        if os.path.exists(SPIDERMONKEY_INSTALLATION):
            break

if not os.path.exists(SPIDERMONKEY_INSTALLATION):
    SPIDERMONKEY_INSTALLATION = "/usr/bin/js"

# The fallback is simply to disable JS tests.
if (not os.path.exists(SPIDERMONKEY_INSTALLATION) or
    os.environ.get("TRAVIS", "") == "true"):
    SPIDERMONKEY_INSTALLATION = None

try:
    from constants_local import *
except ImportError:
    pass
