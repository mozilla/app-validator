import re
import types

from .jstypes import *
from .nodedefinitions import DEFINITIONS
from .predefinedentities import GLOBAL_ENTITIES


DEBUG = False


class Traverser(object):
    """Traverses the AST Tree and determines problems with a chunk of JS."""

    def __init__(self, err, filename, start_line=0, context=None):
        self.err = err

        self.contexts = []
        self.block_contexts = []
        self.filename = filename
        self.start_line = start_line
        self.line = 1  # Line number
        self.position = 0  # Column number
        self.context = context

        # Can use the `this` object
        self.can_use_this = False
        self.this_stack = []

        # For ordering of function traversal.
        self.function_collection = []

        # For debugging
        self.debug_level = 0

        # If we're not debugging, don't waste more cycles than we need to.
        if not DEBUG:
            self._debug = lambda *args, **kwargs: None

    def _debug(self, data, indent=0):
        """Write a message to the console if debugging is enabled."""
        if DEBUG:
            output = data
            if isinstance(data, JSObject) or isinstance(data, JSContext):
                output = data.output()

            output = unicode(output)
            print (". " * (self.debug_level + indent) +
                   output.encode("ascii", "replace"))

    def run(self, data):
        if DEBUG:
            x = open("/tmp/output.js", "w")
            x.write(unicode(data))
            x.close()

        self._debug("START>>")
        try:
            self.function_collection.append([])
            self.traverse_node(data)

            func_coll = self.function_collection.pop()
            for func in func_coll:
                func()
        except Exception:
            print "Exception in JS traversal; %s (%d;%d)" % (
                      self.filename, self.line, self.position)
            raise
        self._debug("END>>")

        if self.contexts:
            # If we're in debug mode, save a copy of the global context for
            # analysis during unit tests.
            if DEBUG:
                self.err.final_context = self.contexts[0]

    def traverse_node(self, node):
        "Finds a node's internal blocks and helps manage state."

        if node is None:
            return JSObject(traverser=self)

        # Simple caching to prevent retraversal
        if "__traversal" in node and node["__traversal"] is not None:
            return node["__traversal"]

        if isinstance(node, types.StringTypes):
            return JSLiteral(node, traverser=self)
        elif "type" not in node or node["type"] not in DEFINITIONS:
            return JSObject(traverser=self)

        self._debug("TRAVERSE>>%s" % node["type"])
        self.debug_level += 1

        # Extract location information if it's available
        if "loc" in node and node["loc"] is not None:
            self.line = self.start_line + int(node["loc"]["start"]["line"])
            self.position = int(node["loc"]["start"]["column"])

        # Extract properties about the node that we're traversing
        (branches, establish_context, action, returns,
             block_level) = DEFINITIONS[node["type"]]

        # If we're supposed to establish a context, do it now
        if establish_context:
            self._push_context()
        elif block_level:
            self._push_block_context()

        # An action allows the traverser to make intelligent decisions based
        # on the function of the code, rather than just the content. If an
        # action is availble, run it and store the output.
        action_result = None
        if action is not None:
            action_result = action(self, node)

            if DEBUG:
                self._debug("ACTION>>%s (%s)" % (repr(action_result), node["type"]))

        if action_result is None:
            self.debug_level += 1
            # Use the node definition to determine and subsequently traverse
            # each of the branches.
            for branch in branches:
                if branch in node:
                    self._debug("BRANCH>>%s" % branch)
                    self.debug_level += 1
                    b = node[branch]
                    if isinstance(b, list):
                        for branch in b:
                            self.traverse_node(branch)
                    else:
                        self.traverse_node(b)
                    self.debug_level -= 1
            self.debug_level -= 1

        # If we defined a context, pop it.
        if establish_context or block_level:
            self._pop_context()
            # WithStatements declare two blocks: one for the block and one for
            # the object that's being withed. We need both because of `let`s.
            if node["type"] == "WithStatement":
                self._pop_context()

        self.debug_level -= 1

        # If there is an action and the action returned a value, it should be
        # returned to the node traversal that initiated this node's traversal.
        if returns:
            node["__traversal"] = action_result
            return action_result

        node["__traversal"] = None
        return JSObject(traverser=self)

    def _push_block_context(self):
        "Adds a block context to the current interpretation frame"
        self.contexts.append(JSContext("block"))

    def _push_context(self, default=None):
        "Adds a variable context to the current interpretation frame"

        if default is None:
            default = JSContext("default")
        self.contexts.append(default)

        self.debug_level += 1
        self._debug("CONTEXT>>%d" % len(self.contexts))

    def _pop_context(self):
        "Adds a variable context to the current interpretation frame"

        # Keep the global scope on the stack.
        if len(self.contexts) == 1:
            self._debug("CONTEXT>>ROOT POP ABORTED")
            return
        popped_context = self.contexts.pop()

        self.debug_level -= 1
        self._debug("POP_CONTEXT>>%d" % len(self.contexts))
        self._debug(popped_context)

    def _peek_context(self, depth=1):
        """
        Returns the most recent context. Note that this should NOT be used
        for variable lookups.
        """
        return self.contexts[len(self.contexts) - depth]

    def _seek_variable(self, variable):
        "Returns the value of a variable that has been declared in a context"

        self._debug("SEEK>>%s" % variable)

        # Look for the variable in the local contexts first
        local_variable = self._seek_local_variable(variable)
        if local_variable is not None:
            return local_variable

        # Seek in globals for the variable instead.
        self._debug("SEEK_GLOBAL>>%s" % variable)
        if self._is_global(variable):
            self._debug("SEEK_GLOBAL>>FOUND>>%s" % variable)
            return self._build_global(variable, GLOBAL_ENTITIES[variable])

        self._debug("SEEK_GLOBAL>>FAILED")
        # If we can't find a variable, we always return a dummy object.
        return JSObject(traverser=self)

    def _is_defined(self, variable):
        return variable in GLOBAL_ENTITIES or self._is_local_variable(variable)

    def _is_local_variable(self, variable):
        """Return whether a variable is defined in the current scope."""
        return any(ctx.has_var(variable, traverser=self) for
                   ctx in self.contexts)

    def _seek_local_variable(self, variable):
        # Loop through each context in reverse order looking for the defined
        # variable.
        for context in reversed(self.contexts):
            # If it has the variable, return it
            if context.has_var(variable, traverser=self):
                self._debug("SEEK>>FOUND")
                return context.get(self, variable)

    def _is_global(self, name):
        "Returns whether a name is a global entity"
        return not self._is_local_variable(name) and name in GLOBAL_ENTITIES

    def _build_global(self, name, entity):
        if isinstance(entity, dict):
            entity.setdefault("name", name)

        # Build out the wrapper object from the global definition.
        result = JSGlobal(entity, traverser=self)
        return result

    def _declare_variable(self, name, value, type_="var"):
        context = self.contexts[0]
        if type_ == "let":
            context = self.contexts[-1]
        elif type_ in ("var", "const", ):
            contexts = (
                [self.contexts[0]] +
                filter(lambda c: c.type_ == "default", self.contexts[1:]))
            context = contexts[-1]
        elif type_ == "glob":
            # Look down through the lexical scope. If the variable being
            # assigned is present in one of those objects, use that as the
            # target context.
            for ctx in reversed(self.contexts[1:]):
                if ctx.has_var(name, traverser=self):
                    context = ctx
                    break

        context.set(name, value, traverser=self)
        return value

    def log_feature(self, feature):
        self.err.feature_profile.add(feature)
        self.err.feature_usage[feature].append({
            'file': self.filename,
            'line': self.line,
            'col': self.position,
        })
