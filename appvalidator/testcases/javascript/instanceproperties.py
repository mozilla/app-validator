import re
import types

from appvalidator.constants import BUGZILLA_BUG
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
    if not isinstance(new_value, jstypes.JSWrapper):
        new_value = jstypes.JSWrapper(new_value, traverser=traverser)

    if new_value.is_literal():
        literal_value = new_value.get_literal_value()
        if isinstance(literal_value, types.StringTypes):
            # Static string assignments

            # Test for on* attributes and script tags.
            if EVENT_ASSIGNMENT.search(literal_value.lower()):
                traverser.err.warning(
                    err_id=("testcases_javascript_instancetypes",
                            "set_%s" % function, "event_assignment"),
                    warning="Event handler assignment via %s" % function,
                    description=["When assigning event handlers, %s "
                                 "should never be used. Rather, use a "
                                 "proper technique, like addEventListener." %
                                     function,
                                 "Event handler code: %s" %
                                     literal_value.encode("ascii", "replace")],
                    filename=traverser.filename,
                    line=traverser.line,
                    column=traverser.position,
                    context=traverser.context)
            elif ("<script" in literal_value or
                  JS_URL.search(literal_value)):
                traverser.err.warning(
                    err_id=("testcases_javascript_instancetypes",
                            "set_%s" % function, "script_assignment"),
                    warning="Scripts should not be created with `%s`" %
                                function,
                    description="`%s` should not be used to add scripts to "
                                "pages via script tags or JavaScript URLs. "
                                "Instead, use event listeners and external "
                                "JavaScript." % function,
                    filename=traverser.filename,
                    line=traverser.line,
                    column=traverser.position,
                    context=traverser.context)
            else:
                # Everything checks out, but we still want to pass it through
                # the markup validator. Turn off strict mode so we don't get
                # warnings about malformed HTML.
                from ..markup.markuptester import MarkupParser
                parser = MarkupParser(traverser.err, strict=False, debug=True)
                parser.process(traverser.filename, literal_value, "xul")

    else:
        # Variable assignments
        traverser.err.warning(
            err_id=("testcases_javascript_instancetypes", "set_%s" % function,
                        "variable_assignment"),
            warning="%s should not be set dynamically" % function,
            description="Due to both security and performance reasons, "
                        "%s should not be set using dynamic "
                        "values. This can lead to security issues or "
                        "fairly serious performance degradation." % function,
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


def set_on_event(new_value, traverser):
    """Ensure that on* properties are not assigned string values."""

    is_literal = new_value.is_literal()

    if (is_literal and
        isinstance(new_value.get_literal_value(), types.StringTypes)):
        traverser.err.warning(
            err_id=("testcases_javascript_instancetypes", "set_on_event",
                    "on*_str_assignment"),
            warning="on* property being assigned string",
            description="Event handlers in JavaScript should not be "
                        "assigned by setting an on* property to a "
                        "string of JS code. Rather, consider using "
                        "addEventListener.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)
    elif not is_literal and new_value.has_property("handleEvent"):
        traverser.err.error(
            err_id=("js", "on*", "handleEvent"),
            error="`handleEvent` no longer implemented in Gecko 18.",
            description="As of Gecko 18, objects with `handleEvent` methods "
                        "may no longer be assigned to `on*` properties. Doing "
                        "so will be equivalent to assigning `null` to the "
                        "property.",
            filename=traverser.filename,
            line=traverser.line,
            column=traverser.position,
            context=traverser.context)


OBJECT_DEFINITIONS = {"innerHTML": {"set": set_innerHTML},
                      "outerHTML": {"set": set_outerHTML},}


def get_operation(mode, property):
    """
    This returns the object definition function for a particular property
    or mode. mode should either be 'set' or 'get'.
    """

    if (property in OBJECT_DEFINITIONS and
        mode in OBJECT_DEFINITIONS[property]):

        return OBJECT_DEFINITIONS[property][mode]

    elif mode == "set" and unicode(property).startswith("on"):
        # We can't match all of them manually, so grab all the "on*" properties
        # and funnel them through the set_on_event function.

        return set_on_event
