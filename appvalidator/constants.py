"Constants that will be used across files."

import json
import os
import types

# Package type constants.
PACKAGE_ANY = 0
PACKAGE_WEBAPP = 8
PACKAGE_PACKAGED_WEBAPP = 9

SPIDERMONKEY_INSTALLATION = os.environ.get("SPIDERMONKEY_INSTALLATION")

DEFAULT_WEBAPP_MRKT_URLS = ["https://marketplace.firefox.com",
                            "https://marketplace-dev.allizom.org"]
BUGZILLA_BUG = "https://bugzilla.mozilla.org/show_bug.cgi?id=%d"

DEFAULT_TIMEOUT = 60

DESCRIPTION_TYPES = types.StringTypes + (list, tuple)

# The maximum size of any string in JS analysis.
MAX_STR_SIZE = 1024 * 24  # 24KB

MAX_RESOURCE_SIZE = 2 * 1024 * 1024

ICON_LIMIT = 10

PERMISSIONS = {
    'web': set([
        'geolocation', 'alarms', 'fmradio', 'desktop-notification', 'storage',
        'audio-channel-normal', 'audio-channel-content'
    ]),
    'privileged': set([
        'device-storage:pictures', 'device-storage:videos',
        'device-storage:music', 'device-storage:sdcard', 'tcp-socket',
        'browser', 'systemXHR', 'audio-channel-notification',
        'audio-channel-alarm', 'contacts', 'mobilenetwork'
    ]),
}

SHORT_LOCALES = {
    'en': 'en-US', 'ga': 'ga-IE', 'pt': 'pt-PT', 'sv': 'sv-SE', 'zh': 'zh-CN'
}

# Taken from Fireplace's hearth/media/js/l10n.js
SUPPORTED_LOCALES = [
    'de', 'en-US', 'es', 'fr', 'pl', 'pt-BR',

    # List of languages from AMO's settings (excluding mkt's active locales).
    'af', 'ar', 'bg', 'ca', 'cs', 'da', 'el', 'eu', 'fa',
    'fi', 'ga-IE', 'he', 'hu', 'id', 'it', 'ja', 'ko', 'mn', 'nl',
    'pt-PT', 'ro', 'ru', 'sk', 'sl', 'sq', 'sv-SE', 'uk', 'vi',
    'zh-CN', 'zh-TW',
    # The hidden list from AMO's settings:
    'cy', 'sr', 'tr',
]

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
