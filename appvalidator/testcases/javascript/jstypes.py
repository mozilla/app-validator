import types

import instanceproperties
import utils


def fake(traverser, **kw):
    return JSWrapper(JSObject(), traverser=traverser, **kw)


class JSObject(object):
    """
    Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements.
    """

    TYPEOF = "object"

    def __init__(self, data=None, traverser=None):
        self.const = False
        self.traverser = traverser
        self.type_ = "object"  # For use when an object is pushed as a context.
        self.data = {}
        if data:
            self.data.update(data)

        self.recursing = False

    def get(self, traverser, name, instantiate=False):
        "Returns the value associated with a property name"
        name = unicode(name)
        output = None

        if name in self.data:
            output = self.data[name]
            if callable(output):
                output = output()
        elif instantiate or name in ('constructor', 'prototype'):
            output = fake(traverser)
            self.set(name, output, traverser=traverser)

        if traverser:
            modifier = instanceproperties.get_operation("get", name)
            if modifier:
                modifier(traverser)

        if output is None:
            return fake(traverser)

        return output

    def get_literal_value(self, traverser=None):
        return u"[object Object]"

    def set(self, name, value, traverser=None):
        if traverser:
            modifier = instanceproperties.get_operation("set", name)
            if modifier:
                modified_value = modifier(value, traverser)
                if modified_value is not None:
                    value = modified_value

        self.data[unicode(name)] = value

    def has_var(self, name, traverser=None):
        return unicode(name) in self.data

    def output(self):
        if self.recursing:
            return u"(recursion)"

        # Prevent unruly recursion with a recursion buster.
        self.recursing = True

        output_dict = {}
        for key in self.data.keys():
            if callable(self.data[key]):
                continue
            elif (isinstance(self.data[key], JSWrapper) and
                  self.data[key].value == self):
                output_dict[key] = u"(self)"
            elif self.data[key] is None:
                output_dict[key] = u"(None)"
            else:
                output_dict[key] = self.data[key].output()

        # Pop from the recursion buster.
        self.recursing = False

        return unicode(output_dict)

    def __str__(self):
        return self.output()

    def delete(self, member):
        if member not in self.data:
            return
        del self.data[member]


class JSGlobal(JSObject):

    def __init__(self, global_data, traverser=None):
        self.global_data = utils.evaluate_lambdas(traverser, global_data)
        super(JSGlobal, self).__init__(traverser=traverser)

        if "typeof" in self.global_data:
            self.TYPEOF = self.global_data["typeof"]

    def _get_contents(self, traverser):
        if "value" not in self.global_data:
            return None
        directory = utils.evaluate_lambdas(
            traverser, self.global_data["value"])
        if directory and callable(self.global_data["value"]):
            self.global_data["value"] = directory
        return directory

    def get(self, traverser, name, instantiate=False):
        if name in self.data or instantiate:
            traverser._debug("Global member found in set data: %s" % name)
            return super(JSGlobal, self).get(
                traverser, name, instantiate=instantiate)

        directory = self._get_contents(traverser)
        if directory and isinstance(directory, dict) and name in directory:
            traverser._debug("GETTING (%s) FROM GLOBAL" % name)
            value = utils.evaluate_lambdas(traverser, directory[name])
            if "literal" in value:
                lit = utils.evaluate_lambdas(traverser, value["literal"])
                return JSWrapper(JSLiteral(lit), traverser=traverser)
            return traverser._build_global(name=name, entity=value)

        traverser._debug("JSObject fallback for member %s in %s" %
                             (name, directory))
        return super(JSGlobal, self).get(traverser, name)

    def set(self, name, value, traverser=None):
        directory = self._get_contents(traverser)
        if directory and isinstance(directory, dict) and name in directory:
            traverser._debug("Setting global member %s" % name)
            self.get(traverser, name).value._set_to(value, traverser=traverser)
        return super(JSGlobal, self).set(name, value, traverser=traverser)

    def _set_to(self, value, traverser=None):
        "This is called when the value of this glboal node is set directly."

        traverser._debug("Assigning direct global value")
        self._get_contents(traverser)  # We don't care about the output.
        if self.global_data.get("readonly"):
            traverser.err.notice(
                err_id=("js", "global", "readonly"),
                notice="Read-only JS global modified",
                description=["A read-only JS global was modified by some "
                             "code. This may cause issues and usually "
                             "indicates other problems with the code.",
                             "Modified global: %s" %
                                 self.global_data.get("name", "(unknown)")],
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context)

    def has_var(self, name, traverser=None):
        directory = self._get_contents(traverser)
        if directory and name in directory:
            return True
        return super(JSGlobal, self).has_var(name, traverser=traverser)

    def get_literal_value(self, traverser=None):
        if "literal" in self.global_data:
            lit = self.global_data["literal"]
            return lit(traverser or self.traverser) if callable(lit) else lit

        directory = self._get_contents(traverser)
        if directory and not isinstance(directory, dict):
            return directory.get_literal_value(traverser=traverser)

        return super(JSGlobal, self).get_literal_value(traverser)

    def output(self):
        return "[global %s]{%s}%s" % (
            getattr(self, "name", "Unnamed"),
            ",".join("%s:%s" % (repr(k), repr(v)) for
                     k, v in self.global_data.items()),
            super(JSGlobal, self).output())


class JSContext(JSObject):
    """A variable context"""

    def __init__(self, context_type, traverser=None):
        super(JSContext, self).__init__(traverser=traverser)
        self.type_ = context_type
        self.data = {}


class JSWrapper(object):
    """Wraps a JS value and handles contextual functions for it."""

    def __init__(self, value=None, traverser=None, callable_=False):

        if traverser is not None:
            traverser.debug_level += 1
            traverser._debug("-----New JSWrapper-----")
            if isinstance(value, JSWrapper):
                traverser._debug(">>> Rewrap <<<")
            traverser.debug_level -= 1

        self.const = False
        self.traverser = traverser
        self.value = None  # Instantiate the placeholder value

        self.set_value(value, overwrite_const=True)
        self.callable = callable_

    @property
    def is_global(self):
        return isinstance(self.value, JSGlobal)

    def set_value(self, value, traverser=None, overwrite_const=False):
        """Assigns a value to the wrapper"""

        # Use a global traverser if it's present.
        if traverser is None:
            traverser = self.traverser

        if self.const and not overwrite_const:
            traverser.err.warning(
                err_id=("js", "JSWrapper_set_value", "const_overwrite"),
                warning="Overwritten constant value",
                description="A variable declared as constant has been "
                            "overwritten in some JS code.",
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context)

        if value == self.value:
            return self

        if isinstance(value, (bool, str, int, float, long, unicode)):
            value = JSLiteral(value)
        # If the value being assigned is a wrapper as well, copy it in
        elif isinstance(value, JSWrapper):
            self.value = value.value
            # `const` does not carry over on reassignment.
            return self
        elif callable(value):
            value = utils.evaluate_lambdas(traverser, value)

        self.value = value
        return self

    def has_var(self, prop):
        """Returns a boolean value representing the presence of a property"""
        return (getattr(self.value, "has_var") and
                self.value.has_var(prop))

    def get(self, traverser, name, instantiate=False):
        """Retrieve a property from the variable."""

        # Process any getters that are present for the current property.
        modifier = instanceproperties.get_operation("get", name)
        if modifier:
            modifier(traverser)

        if self.value is not None:
            output = self.value.get(traverser, name, instantiate=instantiate)
        else:
            output = None

        return output

    def del_value(self, member):
        """The member `member` will be deleted from the value of the wrapper"""
        self.value.delete(member)

    def has_var(self, value, traverser=None):
        return self.value.has_var(value, traverser=traverser or self.traverser)

    def is_literal(self):
        """Returns whether the content is a literal"""
        return isinstance(self.value, JSLiteral)

    def get_literal_value(self, traverser=None):
        """Returns the literal value of the wrapper"""
        if self.value is None:
            return None

        return self.value.get_literal_value(self.traverser)

    def output(self):
        if self.value is self:
            return "(recursing)"
        return self.value.output() if self.value else "(None)"

    def __str__(self):
        return unicode(self.value)


LITERAL_TYPEOF = {
    int: "number",
    float: "number",
    long: "number",
    str: "string",
    unicode: "string",
    bool: "boolean",
}

class JSLiteral(JSObject):
    """Represents a literal JavaScript value."""

    def __init__(self, value=None, traverser=None):
        super(JSLiteral, self).__init__(traverser=traverser)
        self.value = value
        self.TYPEOF = LITERAL_TYPEOF.get(type(value), self.TYPEOF)

    def set_value(self, value):
        self.value = value

    def __str__(self):
        if isinstance(self.value, bool):
            return str(self.output()).lower()
        return str(self.output())

    def output(self):
        return self.value

    def get_literal_value(self, traverser=None):
        "Returns the literal value of a this literal. Heh."
        return self.value

    def has_var(self, name, traverser=None):
        return False

    def delete(self, member):
        pass


class JSArray(JSObject):
    """A class that represents both a JS Array and a JS list."""

    def __init__(self, elements=None, traverser=None):
        super(JSArray, self).__init__(traverser=traverser)
        self.elements = elements or []

    def get(self, traverser, index, instantiate=False):
        if index == "length":
            return len(self.elements)

        # Courtesy of Ian Bicking: http://bit.ly/hxv6qt
        try:
            return self.elements[int(index.strip().split()[0])]
        except (ValueError, IndexError, KeyError):
            return super(JSArray, self).get(traverser, index, instantiate)

    def has_var(self, name, traverser=None):
        print name, type(name)
        index = None
        if isinstance(name, types.StringTypes) and name.isdigit():
            index = utils.get_as_num(name, traverser)
        elif isinstance(name, int):
            index = name

        if index is not None and len(self.elements) > index >= 0:
            return True

        return super(JSArray, self).has_var(name, traverser=traverser)

    def get_literal_value(self, traverser=None):
        """Arrays return a comma-delimited version of themselves."""

        if self.recursing:
            return u"(recursion)"

        self.recursing = True

        # Interestingly enough, this allows for things like:
        # x = [4]
        # y = x * 3 // y = 12 since x equals "4"

        output = u",".join(
            unicode(w.get_literal_value(traverser=self.traverser) if
                    w is not None else u"") for
            w in self.elements if
            not (isinstance(w, JSWrapper) and w.value == self))

        self.recursing = False
        return output

    def set(self, index, value, traverser=None):
        try:
            index = int(index)
            f_index = float(index)
            # Ignore floating point indexes
            if index != float(index) or index < 0:
                return super(JSArray, self).set(value, traverser)
        except ValueError:
            return super(JSArray, self).set(index, value, traverser)

        if len(self.elements) > index:
            self.elements[index] = JSWrapper(value=value, traverser=traverser)
        else:
            # Max out the array size at 100000
            index = min(index, 100000)
            # Assigning to an index higher than the top of the list pads the
            # list with nulls
            while len(self.elements) < index:
                self.elements.append(None)
            self.elements.append(JSWrapper(value=value, traverser=traverser))

    def delete(self, member):
        if member.isdigit() and self.has_var(member):
            index = int(member)
            if index == len(self.elements) - 1:
                self.elements.pop()
            else:
                self.elements[member] = None
        else:
            super(JSArray, self).delete(member)

    def output(self):
        return u"[%s]" % self.get_literal_value()
