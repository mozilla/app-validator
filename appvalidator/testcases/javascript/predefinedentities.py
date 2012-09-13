import math

import actions
from actions import _get_as_str
import call_definitions
from call_definitions import python_wrap
from entity_values import entity
from jstypes import JSWrapper

# A list of identifiers and member values that may not be used.
BANNED_IDENTIFIERS = {
    u"newThread": "Creating threads from JavaScript is a common cause "
                  "of crashes and is unsupported in recent versions of the platform",
    u"processNextEvent": "Spinning the event loop with processNextEvent is a common "
                         "cause of deadlocks, crashes, and other errors due to "
                         "unintended reentrancy. Please use asynchronous callbacks "
                         "instead wherever possible",
}

BANNED_PREF_BRANCHES = [
    u"browser.preferences.instantApply",
    u"capability.policy.",
    u"extensions.alwaysUnpack",
    u"extensions.blocklist.",
    u"extensions.bootstrappedAddons",
    u"extensions.checkCompatibility",
    u"extensions.dss.",
    u"extensions.getAddons.",
    u"extensions.getMoreThemesURL",
    u"extensions.installCache",
    u"extensions.lastAppVersion",
    u"extensions.pendingOperations",
    u"extensions.update.",
    u"general.useragent.",
    u"network.http.",
    u"network.websocket.",
    u"nglayout.debug.disable_xul_cache",
]

BANNED_PREF_REGEXPS = [
    r"extensions\..*\.update\.(url|enabled|interval)",
]


# See https://github.com/mattbasta/amo-validator/wiki/JS-Predefined-Entities
# for details on entity properties.

CONTENT_DOCUMENT = None


# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": {"value": lambda t: {"value": GLOBAL_ENTITIES}},
    u"null": {"literal": lambda t: JSWrapper(None, traverser=t)},

    u"document":
        {"value":
             {u"title":
                  {"overwriteable": True,
                   "readonly": False},
              u"defaultView":
                  {"value": lambda t: {"value": GLOBAL_ENTITIES}},
              u"createElement":
                  {"dangerous":
                       lambda a, t, e:
                           not a or
                           unicode(t(a[0]).get_literal_value()).lower() ==
                               "script"},
              u"createElementNS":
                  {"dangerous":
                       lambda a, t, e:
                           not a or
                           unicode(t(a[0]).get_literal_value()).lower() ==
                               "script"},
              u"loadOverlay":
                  {"dangerous":
                       lambda a, t, e:
                           not a or
                           not unicode(t(a[0]).get_literal_value()).lower()
                               .startswith(("chrome:", "resource:"))},
              u"xmlEncoding": entity("document.xmlEncoding"),
              u"xmlVersion": entity("document.xmlVersion"),
              u"xmlStandalone": entity("document.xmlStandalone")}},

    # The nefariuos timeout brothers!
    u"setTimeout": {"dangerous": actions._call_settimeout},
    u"setInterval": {"dangerous": actions._call_settimeout},

    u"encodeURI": {"readonly": True},
    u"decodeURI": {"readonly": True},
    u"encodeURIComponent": {"readonly": True},
    u"decodeURIComponent": {"readonly": True},
    u"escape": {"readonly": True},
    u"unescape": {"readonly": True},
    u"isFinite": {"readonly": True},
    u"isNaN": {"readonly": True},
    u"parseFloat": {"readonly": True},
    u"parseInt": {"readonly": True},

    u"eval": {"dangerous": True},

    u"Function": {"dangerous": True},
    u"Object":
        {"value":
             {u"prototype": {"readonly": True},
              u"constructor":  # Just an experiment for now
                  {"value": lambda t: GLOBAL_ENTITIES["Function"]}}},
    u"String":
        {"value":
             {u"prototype": {"readonly": True}},
         "return": call_definitions.string_global},
    u"Array":
        {"value":
             {u"prototype": {"readonly": True}},
         "return": call_definitions.array_global},
    u"Number":
        {"value":
             {u"prototype":
                  {"readonly": True},
              u"POSITIVE_INFINITY":
                  {"value": lambda t: JSWrapper(float('inf'), traverser=t)},
              u"NEGATIVE_INFINITY":
                  {"value": lambda t: JSWrapper(float('-inf'), traverser=t)}},
         "return": call_definitions.number_global},
    u"Boolean":
        {"value":
             {u"prototype": {"readonly": True}},
         "return": call_definitions.boolean_global},
    u"RegExp": {"value": {u"prototype": {"readonly": True}}},
    u"Date": {"value": {u"prototype": {"readonly": True}}},
    u"File": {"value": {u"prototype": {"readonly": True}}},

    u"Math":
        {"value":
             {u"PI":
                  {"value": lambda t: JSWrapper(math.pi, traverser=t)},
              u"E":
                  {"value": lambda t: JSWrapper(math.e, traverser=t)},
              u"LN2":
                  {"value": lambda t: JSWrapper(math.log(2), traverser=t)},
              u"LN10":
                  {"value": lambda t: JSWrapper(math.log(10), traverser=t)},
              u"LOG2E":
                  {"value": lambda t: JSWrapper(math.log(math.e, 2),
                                                traverser=t)},
              u"LOG10E":
                  {"value": lambda t: JSWrapper(math.log10(math.e),
                                                traverser=t)},
              u"SQRT2":
                  {"value": lambda t: JSWrapper(math.sqrt(2), traverser=t)},
              u"SQRT1_2":
                  {"value": lambda t: JSWrapper(math.sqrt(1/2), traverser=t)},
              u"abs":
                  {"return": python_wrap(abs, [("num", 0)])},
              u"acos":
                  {"return": python_wrap(math.acos, [("num", 0)])},
              u"asin":
                  {"return": python_wrap(math.asin, [("num", 0)])},
              u"atan":
                  {"return": python_wrap(math.atan, [("num", 0)])},
              u"atan2":
                  {"return": python_wrap(math.atan2, [("num", 0),
                                                      ("num", 1)])},
              u"ceil":
                  {"return": python_wrap(math.ceil, [("num", 0)])},
              u"cos":
                  {"return": python_wrap(math.cos, [("num", 0)])},
              u"exp":
                  {"return": python_wrap(math.exp, [("num", 0)])},
              u"floor":
                  {"return": python_wrap(math.floor, [("num", 0)])},
              u"log":
                  {"return": call_definitions.math_log},
              u"max":
                  {"return": python_wrap(max, [("num", 0)], nargs=True)},
              u"min":
                  {"return": python_wrap(min, [("num", 0)], nargs=True)},
              u"pow":
                  {"return": python_wrap(math.pow, [("num", 0),
                                                    ("num", 0)])},
              u"random": # Random always returns 0.5 in our fantasy land.
                  {"return": call_definitions.math_random},
              u"round":
                  {"return": call_definitions.math_round},
              u"sin":
                  {"return": python_wrap(math.sin, [("num", 0)])},
              u"sqrt":
                  {"return": python_wrap(math.sqrt, [("num", 1)])},
              u"tan":
                  {"return": python_wrap(math.tan, [("num", 0)])},
                  }},

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
    u"Infinity":
        {"value":
             lambda t:
                 GLOBAL_ENTITIES[u"Number"]["value"][u"POSITIVE_INFINITY"]},
    u"NaN": {"readonly": True},
    u"undefined": {"readonly": True},

    u"innerHeight": {"readonly": False},
    u"innerWidth": {"readonly": False},
    u"width": {"readonly": False},
    u"height": {"readonly": False},

    u"content":
        {"context": "content",
         "value":
             {u"document":
                  {"value": lambda t: GLOBAL_ENTITIES[u"document"]}}},
    u"contentWindow":
        {"context": "content",
         "value":
             lambda t: {"value": GLOBAL_ENTITIES}},
    u"_content": {"value": lambda t: GLOBAL_ENTITIES[u"content"]},
    u"gBrowser":
        {"value":
             {u"contentDocument":
                  {"context": "content",
                   "value": lambda t: CONTENT_DOCUMENT},
              u"contentWindow":
                  {"value":
                       lambda t: {"value": GLOBAL_ENTITIES}},
              u"selectedTab":
                  {"readonly": False}}},
    u"opener":
        {"value":
             lambda t: {"value": GLOBAL_ENTITIES}},

    # Preference creation in pref defaults files
    u"pref": {"dangerous": actions._call_create_pref},
    u"user_pref": {"dangerous": actions._call_create_pref},

    u"unsafeWindow": {"dangerous": "The use of unsafeWindow is insecure and "
                                   "should be avoided whenever possible. "
                                   "Consider using a different API if it is "
                                   "available in order to achieve similar "
                                   "functionality."},
}

CONTENT_DOCUMENT = GLOBAL_ENTITIES[u"content"]["value"][u"document"]
