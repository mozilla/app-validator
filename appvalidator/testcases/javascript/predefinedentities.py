import math

import call_definitions
from appvalidator.constants import JS_DEBUG
from call_definitions import python_wrap
from entity_values import entity
from jstypes import JSGlobal, JSLiteral


# See https://github.com/mozilla/app-validator/wiki/JS-Predefined-Entities
# for details on entity properties.

def resolve_entity(traverser, *args):
    element = GLOBAL_ENTITIES[args[0]]
    for layer in args[1:]:
        value = element["value"]
        while callable(value):
            value = value(t=t)
        element = value[layer]
    return element

def get_global(*args):
    return lambda trav: resolve_entity(trav, *args)

global_identity = {"value": lambda *args: GLOBAL_ENTITIES}
READONLY = {"readonly": True}


def feature(constant, fallback=None):
    def wrap(t):
        t.log_feature(constant)
        t._debug("Found feature: %s" % constant)
        if fallback:
            t._debug("Feature has fallback: %s" % repr(fallback))
        return lambda *a: fallback if fallback else {}

    return {'value': wrap,
            'return': lambda **kw: kw['traverser'].log_feature(constant)}


MOZAPPS = {
    u'installPackage': feature('PACKAGED_APPS'),
}


NAVIGATOR = {
    u"apps": feature("APPS", MOZAPPS),
    u"mozApps": feature("APPS", MOZAPPS),
    u"pay": feature("PAY"),
    u"mozPay": feature("PAY"),
    u"battery": feature("BATTERY"),
    u"bluetooth": feature("BLUETOOTH"),
    u"mozBluetooth": feature("BLUETOOTH"),
    u"contacts": feature("CONTACTS"),
    u"mozContacts": feature("CONTACTS"),
    u"getDeviceStorage": feature("DEVICE_STORAGE"),
    u"geolocation": feature("GEOLOCATION"),
    u"getCurrentPosition": feature("GEOLOCATION"),
    u"addIdleObserver": feature("IDLE"),
    u"removeIdleObserver": feature("IDLE"),
    u"connection": feature("NETWORK_INFO"),
    u"mozConnection": feature("NETWORK_INFO"),
    u"mozMobileConnection": feature("NETWORK_INFO"),
    u"networkStats": feature("NETWORK_STATS"),
    u"mozNetworkStats": feature("NETWORK_STATS"),
    u"push": feature("PUSH"),
    u"mozPush": feature("PUSH"),
    u"time": feature("TIME_CLOCK"),
    u"mozTime": feature("TIME_CLOCK"),
    u"vibrate": feature("VIBRATE"),
    u"FM": feature("FM"),
    u"mozFM": feature("FM"),
    u"mozFMRadio": feature("FM"),
    # XXX: The "SMS" API's capitalization seems to be inconsistent at the moment.
    u"SMS": feature("SMS"),
    u"mozSMS": feature("SMS"),
    u"mozSms": feature("SMS"),
    u"mozNotification": feature("NOTIFICATION"),
    u"mozAlarms": feature("ALARM"),
    u"getGamepad": feature("GAMEPAD"),
    u"mozGetGamepad": feature("GAMEPAD"),
    u"webkitGetGamepad": feature("GAMEPAD"),
    u"mozTCPSocket": feature("TCPSOCKET"),
    u"mozInputMethod": feature("THIRDPARTY_KEYBOARD_SUPPORT"),
    u"mozMobileConnections": feature("NETWORK_INFO_MULTIPLE"),
    u"getMobileIdAssertion": feature("MOBILEID"),
    u"getUserMedia": entity("getUserMedia"),
}


# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": global_identity,
    u"null": {"literal": None},

    u"document":
        {"value":
            {u"defaultView": global_identity,

             u"cancelFullScreen": feature("FULLSCREEN"),
             u"mozCancelFullScreen": feature("FULLSCREEN"),
             u"webkitCancelFullScreen": feature("FULLSCREEN"),

             u"fullScreenElement": feature("FULLSCREEN"),
             u"mozFullScreenElement": feature("FULLSCREEN"),
             u"webkitFullScreenElement": feature("FULLSCREEN"),
             },
         },

    # The nefariuos timeout brothers!
    u"setTimeout": entity("setTimeout"),
    u"setInterval": entity("setInterval"),

    u"encodeURI": READONLY,
    u"decodeURI": READONLY,
    u"encodeURIComponent": READONLY,
    u"decodeURIComponent": READONLY,
    u"escape": READONLY,
    u"unescape": READONLY,
    u"isFinite": READONLY,
    u"isNaN": READONLY,
    u"parseFloat": READONLY,
    u"parseInt": READONLY,

    u"eval": entity("eval"),
    u"Function": entity("Function"),
    u"Object":
        {"value": {u"constructor": {"value": get_global("Function")}}},
    u"String":
        {"value":
             {u"constructor": {"value": get_global("Function")}},
         "return": call_definitions.string_global,
         "new": call_definitions.string_global,
         "typeof": "string"},
    u"Array":
        {"value":
             {u"constructor": {"value": get_global("Function")}},
         "return": call_definitions.array_global,
         "new": call_definitions.array_global},
    u"Number":
        {"value":
             {u"constructor": {"value": get_global("Function")},
              u"POSITIVE_INFINITY": {"literal": float('inf')},
              u"NEGATIVE_INFINITY": {"literal": float('-inf')},
              u"isNaN": get_global("isNaN")},
         "return": call_definitions.number_global,
         "new": call_definitions.number_global,
         "typeof": "number"},
    u"Boolean":
        {"value":
             {u"constructor": {"value": get_global("Function")}},
         "return": call_definitions.boolean_global,
         "new": call_definitions.boolean_global,
         "typeof": "boolean"},
    u"RegExp":
        {"value":
            {u"constructor": {"value": get_global("Function")}}},
    u"Date":
        {"value":
            {u"constructor": {"value": get_global("Function")}}},
    u"File":
        {"value":
            {u"constructor": {"value": get_global("Function")}}},

    u"Math":
        {"value":
             {u"PI": {"literal": math.pi},
              u"E": {"literal": math.e},
              u"LN2": {"literal": math.log(2)},
              u"LN10": {"literal": math.log(10)},
              u"LOG2E": {"literal": math.log(math.e, 2)},
              u"LOG10E": {"literal": math.log10(math.e)},
              u"SQRT2": {"literal": math.sqrt(2)},
              u"SQRT1_2": {"literal": math.sqrt(1/2)},
              u"abs": {"return": python_wrap(abs, [("num", 0)])},
              u"acos": {"return": python_wrap(math.acos, [("num", 0)])},
              u"asin": {"return": python_wrap(math.asin, [("num", 0)])},
              u"atan": {"return": python_wrap(math.atan, [("num", 0)])},
              u"atan2": {"return": python_wrap(math.atan2, [("num", 0),
                                                            ("num", 1)])},
              u"ceil": {"return": python_wrap(math.ceil, [("num", 0)])},
              u"cos": {"return": python_wrap(math.cos, [("num", 0)])},
              u"exp": {"return": python_wrap(math.exp, [("num", 0)])},
              u"floor": {"return": python_wrap(math.floor, [("num", 0)])},
              u"log": {"return": call_definitions.math_log},
              u"max": {"return": python_wrap(max, [("num", 0)], nargs=True)},
              u"min": {"return": python_wrap(min, [("num", 0)], nargs=True)},
              u"pow": {"return": python_wrap(math.pow, [("num", 0),
                                                        ("num", 0)])},
              # Random always returns 0.5 in our fantasy land.
              u"random": {"return": lambda **kw: JSLiteral(0.5)},
              u"round": {"return": call_definitions.math_round},
              u"sin": {"return": python_wrap(math.sin, [("num", 0)])},
              u"sqrt": {"return": python_wrap(math.sqrt, [("num", 1)])},
              u"tan": {"return": python_wrap(math.tan, [("num", 0)])},
            },
        },

    u"XMLHttpRequest": entity('XMLHttpRequest'),

    # Global properties are inherently read-only, though this formalizes it.
    u"Infinity": get_global("Number", "POSITIVE_INFINITY"),
    u"NaN": READONLY,
    u"undefined": {"readonly": True, "undefined": True, "literal": None},

    u"opener": global_identity,

    u"navigator": {"value": NAVIGATOR},

    u"Activity": feature("ACTIVITY"),
    u"MozActivity": feature("ACTIVITY"),
    u"ondevicelight": feature("LIGHT_EVENTS"),
    u"ArchiveReader": feature("ARCHIVE"),
    u"indexedDB": feature("INDEXEDDB"),
    u"mozIndexedDB": feature("INDEXEDDB"),
    u"ondeviceproximity": feature("PROXIMITY"),
    u"ondeviceorientation": feature("ORIENTATION"),
    u"ontouchstart": feature("TOUCH"),
    u"Audio": feature("AUDIO"),
    u"webkitAudioContext": feature("WEBAUDIO"),
    u"mozAudioContext": feature("WEBAUDIO"),
    u"AudioContext": feature("WEBAUDIO"),
    u"persistentStorage": feature("QUOTA"),
    u"mozPersistentStorage": feature("QUOTA"),
    u"webkitPersistentStorage": feature("QUOTA"),
    u"StorageInfo": feature("QUOTA"),
    u"fullScreen": feature("FULLSCREEN"),

    U"MediaStream": feature("WEBRTC_MEDIA"),
    u"DataChannel": feature("WEBRTC_DATA"),

    u"RTCPeerConnection": feature("WEBRTC_PEER"),
    u"mozRTCPeerConnection": feature("WEBRTC_PEER"),
    u"webkitRTCPeerConnection": feature("WEBRTC_PEER"),

    u"speechSynthesis": feature("SPEECH_SYN"),
    u"SpeechSynthesisUtterance": feature("SPEECH_SYN"),
    u"SpeechRecognition": feature("SPEECH_REC"),

    u"UDPSocket": feature("UDPSOCKET"),
}


def enable_debug():
    def assert_(wrapper, arguments, traverser):
        traverser.asserts = True
        for arg in arguments:
            if not arg.get_literal_value(traverser):
                traverser.err.error(
                    err_id=("js", "debug", "assert"),
                    error="`%s` expected to be truthy" % arg,
                    description="Assertion error")

    GLOBAL_ENTITIES[u"__assert"] = {"return": assert_}

    def callable_(wrapper, arguments, traverser):
        traverser.asserts = True
        for arg in arguments:
            if not arg.callable:
                traverser.err.error(
                    err_id=("js", "debug", "callable"),
                    error="`%s` expected to be callable" % arg,
                    description="Assertion error")

    GLOBAL_ENTITIES[u"__callable"] = {"return": assert_}
