import types

import instanceproperties
import utils


def fake(traverser, **kw):
    return JSObject(traverser=traverser, **kw)


BASE_MEMBERS = ["const", "traverser", "type_", "callable", "recursing",
                "data", "TYPEOF"]


class JSObject(object):
    """
    Mimics a JS object (function) and is capable of serving as an active
    context to enable static analysis of `with` statements.
    """

    __slots__ = BASE_MEMBERS

    def __init__(self, data=None, traverser=None, callable_=False, const=False):
        self.const = False
        self.traverser = traverser
        self.type_ = "object"  # For use when an object is pushed as a context.
        self.TYPEOF = "object"
        self.data = {}
        if data:
            self.data.update(data)

        self.callable = callable_
        self.const = const
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

    def set(self, name, value, traverser=None, ignore_setters=False):
        traverser = self.traverser or traverser
        if traverser and not ignore_setters:
            modifier = instanceproperties.get_operation("set", name)
            if modifier:
                modified_value = modifier(value, traverser)
                if modified_value is not None:
                    value = modified_value

        if traverser:
            if (self.has_var(name, traverser) and
                self.get(traverser, name).const):

                traverser.err.warning(
                    err_id=("js", "JSWrapper_set_value", "const_overwrite"),
                    warning="Overwritten constant value",
                    description="A variable declared as constant has been "
                                "overwritten in some JS code.",
                    filename=traverser.filename,
                    line=traverser.line,
                    column=traverser.position,
                    context=traverser.context)
                return

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
            elif self.data[key] == self:
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

    __slots__ = BASE_MEMBERS + ["name", "global_data"]

    def __init__(self, global_data, traverser=None, **kw):
        self.global_data = utils.evaluate_lambdas(traverser, global_data)
        super(JSGlobal, self).__init__(traverser=traverser, **kw)

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
                return JSLiteral(lit, traverser=traverser)
            return traverser._build_global(name=name, entity=value)

        traverser._debug("JSObject fallback for member %s in %s" %
                             (name, directory))
        return super(JSGlobal, self).get(traverser, name)

    def set(self, name, value, traverser=None):
        directory = self._get_contents(traverser)
        if directory and isinstance(directory, dict) and name in directory:
            traverser._debug("Setting global member %s" % name)
            obj = self.get(traverser, name)
            if not isinstance(obj, JSLiteral):
                obj._set_to(value, traverser=traverser)
            else:
                modified_global = self.global_data.get("name", "(unknown)")
                traverser.warning(
                    err_id=("js", "global", "literal_assignment"),
                    warning="Assignment to JS literal",
                    description=[
                        "A JS literal was overwritten. This may cause issues "
                        "and usually indicates other problems with the code.",
                        "Modified global: %s.%s" % (modified_global, name)])
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
        traverser = traverser or self.traverser
        if "literal" in self.global_data:
            return utils.evaluate_lambdas(
                traverser, self.global_data["literal"])

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

    __slots__ = BASE_MEMBERS

    def __init__(self, context_type="default", traverser=None, **kw):
        super(JSContext, self).__init__(traverser=traverser, **kw)
        self.type_ = context_type
        self.data = kw.get("data", {})

    def get(self, traverser, name, instantiate=False):
        "Returns the value associated with a property name"
        name = unicode(name)
        output = None

        if name in self.data:
            output = self.data[name]
            if callable(output):
                output = output()

        if output is None:
            return fake(traverser)

        return output


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

    __slots__ = BASE_MEMBERS + ["value"]

    def __init__(self, value=None, traverser=None, **kw):
        super(JSLiteral, self).__init__(traverser=traverser, **kw)
        if isinstance(value, JSLiteral):
            self.value = value.value
        else:
            self.value = value
        self.TYPEOF = LITERAL_TYPEOF.get(type(value), "object")

    def __str__(self):
        if isinstance(self.value, bool):
            return unicode(self.output()).lower()
        return unicode(self.output())

    def __repr__(self):
        return u'<JSLiteral %r>' % self.value

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

    __slots__ = BASE_MEMBERS + ["elements"]

    def __init__(self, elements=None, traverser=None, **kw):
        super(JSArray, self).__init__(traverser=traverser, **kw)
        self.elements = elements or []

    def get(self, traverser, index, instantiate=False):
        if index == "length":
            return JSLiteral(len(self.elements), traverser=traverser)

        # Courtesy of Ian Bicking: http://bit.ly/hxv6qt
        try:
            el = self.elements[int(index.strip().split()[0])]
            if el is None:
                el = JSLiteral(None, traverser=traverser)
            return el
        except (ValueError, IndexError, KeyError):
            return super(JSArray, self).get(traverser, index, instantiate)

    def has_var(self, name, traverser=None):
        index = None
        if isinstance(name, types.StringTypes) and name.isdigit():
            index = utils.get_as_num(name)
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
            unicode(w.get_literal_value(traverser=traverser or
                                                  self.traverser) if
                    w is not None and w is not self else u"") for
                    w in self.elements)

        self.recursing = False
        return output

    def set(self, index, value, traverser=None):
        if index.isdigit():
            try:
                i_index = min(int(index), 100000)
                # Ignore floating point indexes
                if i_index != float(index) or i_index < 0:
                    return super(JSArray, self).set(index, value, traverser)
                if len(self.elements) <= i_index:
                    for i in xrange(i_index - len(self.elements) + 1):
                        self.elements.append(None)
                self.elements[i_index] = value
                return value
            except ValueError:
                return super(JSArray, self).set(index, value, traverser)
        else:
            return super(JSArray, self).set(index, value, traverser)

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
