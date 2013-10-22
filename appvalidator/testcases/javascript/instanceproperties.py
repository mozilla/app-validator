import re
import types

from appvalidator.constants import BUGZILLA_BUG
from appvalidator.csp import warn
import jstypes


EVENT_ASSIGNMENT = re.compile("<.+ on[a-z]+=")
JS_URL = re.compile("href=[\'\"]javascript:")


def set_innerHTML(new_value, traverser):
    """Tests that values being assigned to innerHTML are not dangerous."""
    return _set_HTML_property("innerHTML", new_value, traverser)


def set_outerHTML(new_value, traverser):
    """Tests that values being assigned to outerHTML are not dangerous."""
    return _set_HTML_property("outerHTML", new_value, traverser)


def _set_HTML_property(function, new_value, traverser):
    if isinstance(new_value, jstypes.JSLiteral):
        # TODO: This might be optimizable as get_as_str
        literal_value = new_value.get_literal_value(traverser)
        if isinstance(literal_value, types.StringTypes):
            # Static string assignments

            # Test for on* attributes and script tags.
            if EVENT_ASSIGNMENT.search(literal_value.lower()):
                warn(traverser.err,
                     filename=traverser.filename,
                     line=traverser.line,
                     column=traverser.position,
                     context=traverser.context,
                     violation_type="javascript_event_assignment")
            elif "<script" in literal_value or JS_URL.search(literal_value):
                warn(traverser.err,
                     filename=traverser.filename,
                     line=traverser.line,
                     column=traverser.position,
                     context=traverser.context,
                     violation_type="javascript_url")
            else:
                # Everything checks out, but we still want to pass it through
                # the markup validator. Turn off strict mode so we don't get
                # warnings about malformed HTML.
                from ..markup.markuptester import MarkupParser
                parser = MarkupParser(traverser.err, strict=False, debug=True)
                parser.process(traverser.filename, literal_value, "xul")


def set_on_event(new_value, traverser):
    """Ensure that on* properties are not assigned string values."""

    if (isinstance(new_value, jstypes.JSLiteral) and
        isinstance(new_value.get_literal_value(traverser), types.StringTypes)):
        warn(traverser.err,
             filename=traverser.filename,
             line=traverser.line,
             column=traverser.position,
             context=traverser.context,
             violation_type="setting_on-event")


def feature(constant, fallback=None):
    def wrap(traverser):
        traverser.log_feature(constant)
        return fallback
    return {"get": wrap, "set": lambda nv, t: wrap(t)}


OBJECT_DEFINITIONS = {
    "innerHTML": {"set": set_innerHTML},
    "outerHTML": {"set": set_outerHTML},

    "ontouchstart": feature("TOUCH"),
    "ontouchend": feature("TOUCH"),
    "ontouchmove": feature("TOUCH"),
    "ontouchcancel": feature("TOUCH"),
}


def get_operation(mode, property):
    """
    This returns the object definition function for a particular property
    or mode. mode should either be 'set' or 'get'.
    """

    prop = unicode(property)
    if (prop in OBJECT_DEFINITIONS and
        mode in OBJECT_DEFINITIONS[prop]):

        return OBJECT_DEFINITIONS[prop][mode]

    elif mode == "set" and prop.startswith("on") and len(prop) > 2:
        # We can't match all of them manually, so grab all the "on*" properties
        # and funnel them through the set_on_event function.

        return set_on_event
