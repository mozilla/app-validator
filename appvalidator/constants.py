"Constants that will be used across files."

import os
import types

# Package type constants.
PACKAGE_ANY = 0
PACKAGE_WEBAPP = 8
PACKAGE_PACKAGED_WEBAPP = 9

JS_DEBUG = False
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

MAX_GARBAGE = 100 * 1024

PERMISSIONS = {
    'web': set([
        'alarms', 'audio-capture', 'audio-channel-content',
        'audio-channel-normal', 'desktop-notification', 'fmradio',
        'geolocation', 'push', 'storage', 'video-capture'
    ]),
    'privileged': set([
        'audio-channel-alarm', 'audio-channel-notification', 'browser',
        'camera', 'contacts', 'device-storage:pictures',
        'device-storage:videos', 'device-storage:music',
        'device-storage:sdcard', 'feature-detection',
        'input', 'mobileid', 'mobilenetwork', 'speaker-control', 'systemXHR',
        'tcp-socket'
    ]),
    'certified': set([
        'attention', 'audio-channel-ringer', 'audio-channel-telephony',
        'audio-channel-publicnotification', 'background-sensors',
        'backgroundservice', 'bluetooth', 'cellbroadcast',
        'downloads', 'device-storage:apps', 'embed-apps', 'idle',
        'mobileconnection', 'network-events', 'networkstats-manage',
        'open-remote-window', 'permissions', 'phonenumberservice', 'power',
        'settings', 'sms', 'telephony', 'time', 'voicemail', 'webapps-manage',
        'wifi-manage', 'wappush'
    ]),
    'prerelease': set([
        'moz-attention',
        'moz-firefox-accounts',
        'moz-audio-channel-telephony',
        'moz-audio-channel-ringer',
    ]),
}
ALL_PERMISSIONS = set.union(*PERMISSIONS.values())
PRERELEASE_PERMISSIONS = PERMISSIONS['prerelease']
PRIVILEGED_PERMISSIONS = ALL_PERMISSIONS - PERMISSIONS['certified']
WEB_PERMISSIONS = PERMISSIONS['web']

# Those 3 *_LANGUAGES settings are taken from zamboni's mkt/settings.py
SUPPORTED_LANGUAGES = (
    'bg', 'bn-BD', 'ca', 'cs', 'da', 'de', 'el', 'en-US', 'es', 'eu', 'fr',
    'ga-IE', 'hr', 'hu', 'it', 'ja', 'ko', 'mk', 'nb-NO', 'nl', 'pa', 'pl',
    'pt-BR', 'ro', 'ru', 'sk', 'sq', 'sr', 'sr-Latn', 'ta', 'tr', 'xh',
    'zh-CN', 'zh-TW', 'zu',
)
HIDDEN_LANGUAGES = (
    'af', 'ar', 'fa', 'fi', 'he', 'id', 'mn', 'pt-PT', 'sl', 'sv-SE',
    'uk', 'vi',
    'cy',
)
SHORTER_LANGUAGES = {'en': 'en-US', 'ga': 'ga-IE', 'pt': 'pt-PT',
                     'sv': 'sv-SE', 'zh': 'zh-CN'}

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
