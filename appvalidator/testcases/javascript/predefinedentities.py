import math

import actions
from actions import _get_as_str
import call_definitions
from call_definitions import python_wrap
from entity_values import entity
from jstypes import JSWrapper


# See https://github.com/mattbasta/amo-validator/wiki/JS-Predefined-Entities
# for details on entity properties.

# This will be populated later, we just need to reserve its name now.
CONTENT_DOCUMENT = None


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


def get_constant(value):
    def wrap(t):
        return JSWrapper(value, traverser=t)
    return wrap


def global_identity():
    return lambda t: {"value": GLOBAL_ENTITIES}


MUTABLE = {"overwriteable": True, "readonly": False}


# GLOBAL_ENTITIES is also representative of the `window` object.
GLOBAL_ENTITIES = {
    u"window": {"value": global_identity()},
    u"null": {"literal": get_constant(None)},

    u"document":
        {"value":
             {u"title": MUTABLE,
              u"defaultView": {"value": global_identity()},
              u"createElement": entity("createElement"),
              u"createElementNS": entity("createElementNS")}},

    # The nefariuos timeout brothers!
    u"setTimeout": entity("setTimeout"),
    u"setInterval": entity("setInterval"),

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

    u"eval": entity("eval"),
    u"Function": entity("Function"),
    u"Object":
        {"value":
             {u"prototype": {"readonly": True},
              u"constructor":
                  {"value": get_global("Function")}}},
    u"String":
        {"value":
             {u"prototype": {"readonly": True},
              u"constructor":
                  {"value": get_global("Function")}},
         "return": call_definitions.string_global},
    u"Array":
        {"value":
             {u"prototype": {"readonly": True},
              u"constructor":
                  {"value": get_global("Function")}},
         "return": call_definitions.array_global},
    u"Number":
        {"value":
             {u"prototype":
                  {"readonly": True},
              u"constructor":
                  {"value": get_global("Function")},
              u"POSITIVE_INFINITY":
                  {"value": get_constant(float('inf'))},
              u"NEGATIVE_INFINITY":
                  {"value": get_constant(float('-inf'))}},
         "return": call_definitions.number_global},
    u"Boolean":
        {"value":
             {u"prototype": {"readonly": True},
              u"constructor":
                  {"value": get_global("Function")}},
         "return": call_definitions.boolean_global},
    u"RegExp":
        {"value":
            {u"prototype": {"readonly": True},
             u"constructor":
                 {"value": get_global("Function")}}},
    u"Date":
        {"value":
            {u"prototype": {"readonly": True},
             u"constructor":
                 {"value": get_global("Function")}}},
    u"File":
        {"value":
            {u"prototype": {"readonly": True},
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
              u"random": {"return": call_definitions.math_random},
              u"round": {"return": call_definitions.math_round},
              u"sin": {"return": python_wrap(math.sin, [("num", 0)])},
              u"sqrt": {"return": python_wrap(math.sqrt, [("num", 1)])},
              u"tan": {"return": python_wrap(math.tan, [("num", 0)])},
            }
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
    u"NaN": {"readonly": True},
    u"undefined": {"readonly": True},

    u"innerHeight": MUTABLE,
    u"innerWidth": MUTABLE,
    u"width": MUTABLE,
    u"height": MUTABLE,

    u"content":
        {"context": "content",
         "value": {u"document": {"value": get_global("document")}}},
    u"contentWindow":
        {"context": "content",
         "value": global_identity()},
    u"_content": {"value": get_global("content")},
    u"opener": {"value": global_identity()},
}

CONTENT_DOCUMENT = GLOBAL_ENTITIES[u"content"]["value"][u"document"]
