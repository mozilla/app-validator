"Constants that will be used across files."

import json
import os

# Package type constants.
PACKAGE_ANY = 0
PACKAGE_WEBAPP = 8
PACKAGE_PACKAGED_WEBAPP = 9

SPIDERMONKEY_INSTALLATION = os.environ.get("SPIDERMONKEY_INSTALLATION")

DEFAULT_WEBAPP_MRKT_URLS = ["https://marketplace.mozilla.org",
                            "https://marketplace-dev.allizom.org"]
BUGZILLA_BUG = "https://bugzilla.mozilla.org/show_bug.cgi?id=%d"

DEFAULT_TIMEOUT = 60

MAX_RESOURCE_SIZE = 2 * 1024 * 1024

# Graciously provided by @kumar in bug 614574
if (not SPIDERMONKEY_INSTALLATION or
    not os.path.exists(SPIDERMONKEY_INSTALLATION)):
    for p in os.environ.get('PATH', '').split(':'):
        SPIDERMONKEY_INSTALLATION = os.path.join(p, "js")
        if os.path.exists(os.path.join(p, SPIDERMONKEY_INSTALLATION)):
            break

if not os.path.exists(SPIDERMONKEY_INSTALLATION):

    ############ Edit this to change the Spidermonkey location #############
    SPIDERMONKEY_INSTALLATION = "/usr/bin/js"

    if not os.path.exists(SPIDERMONKEY_INSTALLATION):
        # The fallback is simply to disable JS tests.
        SPIDERMONKEY_INSTALLATION = None

try:
    from constants_local import *
except ImportError:
    pass
