import math

import actions
from actions import _get_as_str
import call_definitions
from call_definitions import python_wrap
from entity_values import entity
from jstypes import JSWrapper


# See https://github.com/mattbasta/amo-validator/wiki/JS-Predefined-Entities
# for details on entity properties.


def get_global(*args):
    def wrap(t):
        element = GLOBAL_ENTITIES[args[0]]
        for layer in args[1:]:
            value = element["value"]
            while callable(value):
                value = value(t=t)
            element = value[layer]
        return element
    return wrap


get_constant = lambda val: lambda t: JSWrapper(val, traverser=t)
get_constant_method = lambda val: lambda **kw: JSWrapper(
        val, traverser=kw['traverser'])
global_identity = lambda t: {"value": GLOBAL_ENTITIES}

MUTABLE = {"overwriteable": True, "readonly": False}
READONLY = {"readonly": True}


def feature(constant, fallback=None):
    def wrap(t):
        t.log_feature(constant)
        t._debug("Found feature: %s" % constant)
        if fallback:
            t._debug("Feature has fallback: %s" % repr(fallback))
        return {"value": fallback} if fallback else {}

    return {'value': wrap,
            'return': lambda traverser, *a, **kw:
                traverser.log_feature(constant)}


MOZAPPS = {
    u'installPackage': feature('PACKAGED_APPS'),
}


# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": {"value": global_identity},
    u"null": {"literal": get_constant(None)},

    u"document":
        {"value":
            {u"title": MUTABLE,
             u"defaultView": {"value": global_identity},
             u"createElement": entity("createElement"),
             u"createElementNS": entity("createElementNS"),

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
        {"value":
             {u"prototype": READONLY,
              u"constructor":
                  {"value": get_global("Function")}}},
    u"String":
        {"value":
             {u"prototype": READONLY,
              u"constructor":
                  {"value": get_global("Function")}},
         "return": call_definitions.string_global},
    u"Array":
        {"value":
             {u"prototype": READONLY,
              u"constructor":
                  {"value": get_global("Function")}},
         "return": call_definitions.array_global},
    u"Number":
        {"value":
             {u"prototype":
                  READONLY,
              u"constructor":
                  {"value": get_global("Function")},
              u"POSITIVE_INFINITY":
                  {"value": get_constant(float('inf'))},
              u"NEGATIVE_INFINITY":
                  {"value": get_constant(float('-inf'))}},
         "return": call_definitions.number_global},
    u"Boolean":
        {"value":
             {u"prototype": READONLY,
              u"constructor":
                  {"value": get_global("Function")}},
         "return": call_definitions.boolean_global},
    u"RegExp":
        {"value":
            {u"prototype": READONLY,
             u"constructor":
                 {"value": get_global("Function")}}},
    u"Date":
        {"value":
            {u"prototype": READONLY,
             u"constructor":
                 {"value": get_global("Function")}}},
    u"File":
        {"value":
            {u"prototype": READONLY,
             u"constructor":
                 {"value": get_global("Function")}}},

    u"Math":
        {"value":
             {u"PI": {"value": get_constant(math.pi)},
              u"E": {"value": get_constant(math.e)},
              u"LN2": {"value": get_constant(math.log(2))},
              u"LN10": {"value": get_constant(math.log(10))},
              u"LOG2E": {"value": get_constant(math.log(math.e, 2))},
              u"LOG10E": {"value": get_constant(math.log10(math.e))},
              u"SQRT2": {"value": get_constant(math.sqrt(2))},
              u"SQRT1_2": {"value": get_constant(math.sqrt(1/2))},
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
              u"random": {"return": get_constant_method(0.5)},
              u"round": {"return": call_definitions.math_round},
              u"sin": {"return": python_wrap(math.sin, [("num", 0)])},
              u"sqrt": {"return": python_wrap(math.sqrt, [("num", 1)])},
              u"tan": {"return": python_wrap(math.tan, [("num", 0)])},
            },
        },

    u"XMLHttpRequest":
        {"value":
             {u"open":
                  {"dangerous":
                       # Ban synchronous XHR by making sure the third arg
                       # is absent and false.
                       lambda a, t, e:
                           a and len(a) >= 3 and
                           not t(a[2]).get_literal_value() and
                           "Synchronous HTTP requests can cause serious UI "
                           "performance problems, especially to users with "
                           "slow network connections."}}},

    # Global properties are inherently read-only, though this formalizes it.
    u"Infinity": {"value": get_global("Number", "POSITIVE_INFINITY")},
    u"NaN": READONLY,
    u"undefined": READONLY,

    u"innerHeight": MUTABLE,
    u"innerWidth": MUTABLE,
    u"width": MUTABLE,
    u"height": MUTABLE,
    u"opener": {"value": global_identity},

    u"navigator":
        {"value":
            {u"apps": feature("APPS", MOZAPPS),
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
             u"getGamepad": feature("GAMEPAD"),
             u"mozGetGamepad": feature("GAMEPAD"),
             u"webkitGetGamepad": feature("GAMEPAD"),
            },
        },

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

}
