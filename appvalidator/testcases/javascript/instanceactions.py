"""
Prototype
---------

args
    the raw list of arguments
traverser
    the traverser
node
    the current node being evaluated
"""

import jstypes
import utils
from appvalidator.constants import BUGZILLA_BUG
from appvalidator.csp import warn
from .instanceproperties import _set_HTML_property


def createElement(args, traverser, node, wrapper):
    """Handles createElement calls"""

    if not args:
        return

    first_as_str = utils.get_as_str(args[0].get_literal_value())
    if first_as_str.lower() == u"script":
        _create_script_tag(traverser)
    elif not isinstance(args[0], jstypes.JSLiteral):
        _create_variable_element(traverser)


def createElementNS(args, traverser, node, wrapper):
    """Handles createElementNS calls"""

    if not args or len(args) < 2:
        return

    second_as_str = utils.get_as_str(args[1].get_literal_value())
    if "script" in second_as_str.lower():
        _create_script_tag(traverser)
    elif not isinstance(args[1], jstypes.JSLiteral):
        _create_variable_element(traverser)


def _create_script_tag(traverser):
    """Raises a warning that the dev is creating a script tag"""

    warn(traverser.err,
         filename=traverser.filename,
         line=traverser.line,
         column=traverser.position,
         context=traverser.context,
         violation_type="createElement-script")


def _create_variable_element(traverser):
    """Raises a warning that the dev is creating an arbitrary element"""

    warn(traverser.err,
         filename=traverser.filename,
         line=traverser.line,
         column=traverser.position,
         context=traverser.context,
         violation_type="createElement-variable")


def insertAdjacentHTML(args, traverser, node, wrapper):
    """
    Perfrom the same tests on content inserted into the DOM via
    insertAdjacentHTML as we otherwise would for content inserted via the
    various innerHTML/outerHTML properties.
    """
    if not args or len(args) < 2:
        return

    _set_HTML_property("insertAdjacentHTML", args[1], traverser)


def setAttribute(args, traverser, node, wrapper):
    """This ensures that setAttribute calls don't set on* attributes"""

    if not args:
        return

    first_as_str = utils.get_as_str(args[0].get_literal_value())
    if first_as_str.lower().startswith("on"):
        warn(traverser.err,
             filename=traverser.filename,
             line=traverser.line,
             column=traverser.position,
             context=traverser.context,
             violation_type="setAttribute-on")


def feature(constant):
    def wrap(args, traverser, node, wrapper):
        traverser.log_feature(constant)
    return wrap


INSTANCE_DEFINITIONS = {
    u"createElement": createElement,
    u"createElementNS": createElementNS,
    u"insertAdjacentHTML": insertAdjacentHTML,
    u"setAttribute": setAttribute,
    u"requestFullScreen": feature("FULLSCREEN"),
    u"mozRequestFullScreen": feature("FULLSCREEN"),
    u"webkitRequestFullScreen": feature("FULLSCREEN"),
    u"requestPointerLock": feature("POINTER_LOCK"),
    u"mozRequestPointerLock": feature("POINTER_LOCK"),
    u"webkitRequestPointerLock": feature("POINTER_LOCK"),
}
