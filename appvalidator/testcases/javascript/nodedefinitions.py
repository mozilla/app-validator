import types

from appvalidator.constants import MAX_STR_SIZE
from appvalidator.python.copy import deepcopy

import instanceactions
import utils
from jstypes import (JSArray, JSContext, JSGlobal, JSLiteral, JSObject,
                     JSWrapper)


NUMERIC_TYPES = (int, long, float, complex)

# None of these operations (or their augmented assignment counterparts) should
# be performed on non-numeric data. Any time we get non-numeric data for these
# guys, we just return window.NaN.
NUMERIC_OPERATORS = ("-", "*", "/", "%", "<<", ">>", ">>>", "|", "^", "&")
NUMERIC_OPERATORS += tuple("%s=" % op for op in NUMERIC_OPERATORS)


def ExpressionStatement(traverser, node):
    return traverser.traverse_node(node["expression"])


def WithStatement(traverser, node):
    obj = traverser.traverse_node(node["object"])
    if not isinstance(obj.value, dict):
        traverser.contexts[-1] = obj.value
        traverser.contexts.append(JSContext("block"))


def _function(traverser, node):
    """
    A helper function that traverses and instantiates function declarations and
    function expressions.
    """

    def wrap(traverser, node):
        me = JSObject()

        traverser.function_collection.append([])

        # Replace the current context with a prototypeable JS object.
        traverser._pop_context()
        me.type_ = "default"  # Treat the function as a normal object.
        traverser._push_context(me)
        traverser._debug("THIS_PUSH")
        traverser.this_stack.append(me)  # Allow references to "this"

        # Declare parameters in the local scope
        params = []
        for param in node["params"]:
            if param["type"] == "Identifier":
                params.append(param["name"])
            elif param["type"] == "ArrayPattern":
                for element in param["elements"]:
                    # Array destructuring in function prototypes? LOL!
                    if element is None or element["type"] != "Identifier":
                        continue
                    params.append(element["name"])

        local_context = traverser._peek_context(1)
        for param in params:
            var = JSWrapper(JSObject(), traverser=traverser)

            # We can assume that the params are static because we don't care
            # about what calls the function. We want to know whether the
            # function solely returns static values. If so, it is a static
            # function.
            local_context.set(param, var)

        traverser.traverse_node(node["body"])

        # Since we need to manually manage the "this" stack, pop off that
        # context.
        traverser._debug("THIS_POP")
        traverser.this_stack.pop()

        # Call all of the function collection's members to traverse all of the
        # child functions.
        func_coll = traverser.function_collection.pop()
        for func in func_coll:
            func()

    # Put the function off for traversal at the end of the current block scope.
    traverser.function_collection[-1].append(lambda: wrap(traverser, node))

    return JSWrapper(JSObject(), traverser=traverser, callable_=True)


def FunctionDeclaration(traverser, node):
    me = _function(traverser, node)
    traverser._peek_context(2).set(node["id"]["name"], me)
    return me

# It's just an alias.
FunctionExpression = _function


def VariableDeclaration(traverser, node):
    traverser._debug("VARIABLE_DECLARATION")
    traverser.debug_level += 1

    for declaration in node["declarations"]:

        # It could be deconstruction of variables :(
        if declaration["id"]["type"] == "ArrayPattern":

            vars = []
            for element in declaration["id"]["elements"]:
                # NOTE : Multi-level array destructuring sucks. Maybe implement
                # it someday if you're bored, but it's so rarely used and it's
                # so utterly complex, there's probably no need to ever code it
                # up.
                if element is None or element["type"] != "Identifier":
                    vars.append(None)
                    continue
                vars.append(element["name"])

            # The variables are not initialized
            if declaration["init"] is None:
                # Simple instantiation; no initialization
                for var in filter(None, vars):
                    traverser._declare_variable(
                        var, JSWrapper(JSObject(), traverser=traverser))

            # The variables are declared inline
            elif declaration["init"]["type"] == "ArrayPattern":
                # TODO : Test to make sure len(values) == len(vars)
                for value in declaration["init"]["elements"]:
                    if vars[0]:
                        traverser._declare_variable(
                            vars[0], traverser.traverse_node(value))
                    vars = vars[1:]  # Pop off the first value

            # It's being assigned by a JSArray (presumably)
            elif declaration["init"]["type"] == "ArrayExpression":
                assigner = traverser.traverse_node(declaration["init"])
                for value, var in zip(assigner.value.elements, vars):
                    traverser._declare_variable(var, value)

        elif declaration["id"]["type"] == "ObjectPattern":

            init = traverser.traverse_node(declaration["init"])

            def _proc_objpattern(init_obj, properties):
                for prop in properties:
                    # Get the name of the init obj's member
                    if prop["key"]["type"] == "Literal":
                        prop_name = prop["key"]["value"]
                    elif prop["key"]["type"] == "Identifier":
                        prop_name = prop["key"]["name"]
                    else:
                        continue

                    if prop["value"]["type"] == "Identifier":
                        traverser._declare_variable(
                            prop["value"]["name"],
                            init_obj.get(traverser, prop_name))
                    elif prop["value"]["type"] == "ObjectPattern":
                        _proc_objpattern(init_obj.get(traverser, prop_name),
                                         prop["value"]["properties"])

            if init is not None:
                _proc_objpattern(init_obj=init,
                                 properties=declaration["id"]["properties"])

        else:
            var_name = declaration["id"]["name"]
            traverser._debug("NAME>>%s" % var_name)

            var = traverser.traverse_node(declaration["init"])
            var.const = node["kind"] == "const"
            traverser._declare_variable(var_name, var, type_=node["kind"])

    traverser.debug_level -= 1

    # The "Declarations" branch contains custom elements.
    return True


def ThisExpression(traverser, node):
    "Returns the `this` object"
    if not traverser.this_stack:
        from predefinedentities import global_identity
        return traverser._build_global("window", global_identity)
    return traverser.this_stack[-1]


def ArrayExpression(traverser, node):
    return JSArray([traverser.traverse_node(x) for x in node["elements"]])


def ObjectExpression(traverser, node):
    var = JSObject(traverser=traverser)
    for prop in node["properties"]:
        key = prop["key"]
        var.set(key["value" if key["type"] == "Literal" else "name"],
                traverser.traverse_node(prop["value"]), traverser)
        # TODO: Observe "kind"

    return var


def _expr_unary_typeof(wrapper):
    """Evaluate the "typeof" value for a JSWrapper object."""
    if wrapper.callable:
        return "function"
    elif wrapper.is_global:
        if "typeof" in wrapper.value.global_data:
            return wrapper.value.global_data["typeof"]
        if ("return" in wrapper.value.global_data and
            "value" not in wrapper.value.global_data):
            return "function"

    if wrapper.is_global and "undefined" in wrapper.value.global_data:
        return "undefined"

    return wrapper.value.TYPEOF


UNARY_OPERATORS = {
    "-": lambda e: -1 * utils.get_as_num(e.get_literal_value()),
    "+": lambda e: utils.get_as_num(e.get_literal_value()),
    "!": lambda e: not e.get_literal_value(),
    "~": lambda e: -1 * (utils.get_as_num(e.get_literal_value()) + 1),
    "typeof": _expr_unary_typeof,
}

def UnaryExpression(traverser, node):
    if node["operator"] in UNARY_OPERATORS:
        output = UNARY_OPERATORS[node["operator"]](
            traverser.traverse_node(node["argument"]))
    elif node["operator"] == "void":
        from predefinedentities import get_wrapped_global
        output = get_wrapped_global(traverser, "undefined")
    else:
        output = None

    return JSWrapper(output, traverser=traverser)


BINARY_OPERATORS = {
    "==": lambda l, r, gl, gr: l == r or gl == gr,
    "!=": lambda l, r, *a: l != r,
    "===": lambda l, r, *a: l == r,  # Be flexible.
    "!==": lambda l, r, *a: type(l) != type(r) or l != r,
    ">": lambda l, r, *a: l > r,
    "<": lambda l, r, *a: l < r,
    "<=": lambda l, r, *a: l <= r,
    ">=": lambda l, r, *a: l >= r,
    "<<": lambda l, r, gl, gr: int(gl) << int(gr),
    ">>": lambda l, r, gl, gr: int(gl) >> int(gr),
    ">>>": lambda l, r, gl, gr: float(abs(int(gl)) >> int(gr)),
    "+": lambda l, r, *a: l + r,
    "-": lambda l, r, gl, gr: gl - gr,
    "*": lambda l, r, gl, gr: gl * gr,
    "/": lambda l, r, gl, gr: 0 if gr == 0 else (gl / gr),
    "%": lambda l, r, gl, gr: 0 if gr == 0 else (gl % gr),
}

def BinaryExpression(traverser, node):
    traverser.debug_level += 1

    # Select the proper operator.
    operator = node["operator"]
    traverser._debug("BIN_OPERATOR>>%s" % operator)

    # Traverse the left half of the binary expression.
    traverser._debug("BIN_EXP>>l-value")
    traverser.debug_level += 1

    if (node["left"]["type"] == "BinaryExpression" and
        "__traversal" not in node["left"]):
        # Process the left branch of the binary expression directly. This keeps
        # the recursion cap in line and speeds up processing of large chains
        # of binary expressions.
        left = BinaryExpression(traverser, node["left"])
        node["left"]["__traversal"] = left
    else:
        left = traverser.traverse_node(node["left"])

    # Traverse the right half of the binary expression.
    traverser._debug("BIN_EXP>>r-value", -1)

    if (operator == "instanceof" and
            node["right"]["type"] == "Identifier" and
            node["right"]["name"] == "Function"):
        # We make an exception for instanceof's r-value if it's a dangerous
        # global, specifically Function.
        traverser.debug_level -= 1
        return JSWrapper(True, traverser=traverser)
    else:
        right = traverser.traverse_node(node["right"])

    traverser.debug_level -= 1

    # Binary expressions are only executed on literals.
    left = left.get_literal_value()
    right_wrap = right
    right = right.get_literal_value()

    # Coerce the literals to numbers for numeric operations.
    gleft = utils.get_as_num(left)
    gright = utils.get_as_num(right)

    if operator in (">>", "<<", ">>>"):
        if left is None or right is None or gright < 0:
            return JSWrapper(False, traverser=traverser)
        elif abs(gleft) == float('inf') or abs(gright) == float('inf'):
            return utils.get_NaN(traverser)

    if operator in BINARY_OPERATORS:
        # Concatenation can be silly, so always turn undefineds into empty
        # strings and if there are strings, make everything strings.
        if operator == "+":
            if left is None:
                left = ""
            if right is None:
                right = ""
            if (isinstance(left, types.StringTypes) or
                    isinstance(right, types.StringTypes)):
                left = utils.get_as_str(left)
                right = utils.get_as_str(right)

        output = BINARY_OPERATORS[operator](left, right, gleft, gright)
    elif operator == "in":
        output = right_wrap.has_var(left, traverser=traverser)
    #TODO: `delete` operator

    # Cap the length of analyzed strings.
    if isinstance(output, types.StringTypes) and len(output) > MAX_STR_SIZE:
        output = output[:MAX_STR_SIZE]

    return JSWrapper(output, traverser=traverser)


ASSIGNMENT_OPERATORS = {
    "=": lambda l, r, *a: r,
    "+=": lambda l, r, gl, gr: l + r,
    "-=": lambda l, r, gl, gr: gl - gr,
    "*=": lambda l, r, gl, gr: gl * gr,
    "/=": lambda l, r, gl, gr: 0 if gr == 0 else (gl / gr),
    "%=": lambda l, r, gl, gr: 0 if gr == 0 else (gl % gr),
    "<<=": lambda l, r, gl, gr: int(gl) << int(gr),
    ">>=": lambda l, r, gl, gr: int(gl) >> int(gr),
    ">>>=": lambda l, r, gl, gr: float(abs(int(gl)) >> gr),
    "|=": lambda l, r, gl, gr: int(gl) | int(gr),
    "^=": lambda l, r, gl, gr: int(gl) ^ int(gr),
    "&=": lambda l, r, gl, gr: int(gl) & int(gr),
}

def AssignmentExpression(traverser, node):
    traverser._debug("ASSIGNMENT_EXPRESSION")
    traverser.debug_level += 1

    traverser._debug("ASSIGNMENT>>PARSING RIGHT")
    right = traverser.traverse_node(node["right"])

    operator = node["operator"]

    # Treat direct assignment different than augmented assignment.
    if operator == "=":

        global_overwrite = False
        readonly_value = True

        node_left = node["left"]
        traverser._debug("ASSIGNMENT:DIRECT(%s)" % node_left["type"])

        if node_left["type"] == "Identifier":
            # Identifiers just need the ID name and a value to push.
            # Raise a global overwrite issue if the identifier is global.
            global_overwrite = traverser._is_global(node_left["name"])

            # Get the readonly attribute and store its value if is_global
            if global_overwrite:
                from predefinedentities import GLOBAL_ENTITIES
                global_dict = GLOBAL_ENTITIES[node_left["name"]]
                readonly_value = global_dict.get("readonly", False)

            traverser._declare_variable(node_left["name"], right, type_="glob")

        # TODO: WTF does this even do?
        elif node_left["type"] == "MemberExpression":
            member_object = MemberExpression(traverser, node_left["object"],
                                             instantiate=True)
            member_property = _get_member_exp_property(traverser, node_left)
            traverser._debug("ASSIGNMENT:MEMBER_PROPERTY(%s)" % member_property)

            if member_object.value is None:
                member_object.value = JSObject()

            member_object.value.set(member_property, right, traverser)

        if callable(readonly_value):
            readonly_value(traverser, right, node["right"])

        return right

    elif operator not in ASSIGNMENT_OPERATORS:
        # We don't support that operator. (yet?)
        traverser._debug("ASSIGNMENT>>OPERATOR NOT FOUND", 1)
        return left

    traverser._debug("ASSIGNMENT>>PARSING LEFT")
    orig_left = left = traverser.traverse_node(node["left"])
    traverser._debug("ASSIGNMENT>>DONE PARSING LEFT")
    traverser.debug_level -= 1

    # If we're modifying a non-numeric type with a numeric operator, return
    # NaN.
    if (operator in NUMERIC_OPERATORS and
        not isinstance(left.get_literal_value() or 0, NUMERIC_TYPES)):
        left.set_value(utils.get_NaN(traverser), traverser=traverser)
        return left

    gleft, gright = utils.get_as_num(left), utils.get_as_num(right)

    traverser._debug("ASSIGNMENT>>OPERATION:%s" % operator)
    if operator in ("<<=", ">>=", ">>>=") and gright < 0:
        # The user is doing weird bitshifting that will return 0 in JS but
        # not in Python.
        left.set_value(0, traverser=traverser)
        return left
    elif (operator in ("<<=", ">>=", ">>>=", "|=", "^=", "&=") and
          (abs(gleft) == float('inf') or abs(gright) == float('inf'))):
        # Don't bother handling infinity for integer-converted operations.
        left.set_value(utils.get_NaN(traverser), traverser=traverser)
        return left

    if operator == '+=':
        lit_left = left.get_literal_value()
        lit_right = right.get_literal_value()
        # Don't perform an operation on None. Python freaks out.
        if lit_left is None:
            lit_left = 0
        if lit_right is None:
            lit_right = 0

        # If either side of the assignment operator is a string, both sides
        # need to be cast to strings first.
        if (isinstance(lit_left, types.StringTypes) or
            isinstance(lit_right, types.StringTypes)):
            left = utils.get_as_str(lit_left)
            right = utils.get_as_str(lit_right)
        else:
            left, right = lit_left, lit_right

    output = ASSIGNMENT_OPERATORS[operator](left, right, gleft, gright)

    # Cap the length of analyzed strings.
    if isinstance(output, types.StringTypes) and len(output) > MAX_STR_SIZE:
        output = output[:MAX_STR_SIZE]

    traverser._debug("ASSIGNMENT::New value >> %s" % output, 1)
    orig_left.set_value(output, traverser=traverser)
    return orig_left


def NewExpression(traverser, node):
    args = [traverser.traverse_node(arg) for arg in node["arguments"]]
    elem = traverser.traverse_node(node["callee"])
    if elem.is_global:
        traverser._debug("Making overwritable")
        global_data = dict(elem.value.global_data)
        global_data.update(overwritable=True, readonly=False)
        temp = JSGlobal(global_data, traverser=traverser)
        temp.data = deepcopy(elem.value.data) if elem.value.data else {}
        if "new" in temp.global_data:
            new_temp = temp.global_data["new"](node, args, traverser)
            if new_temp is not None:
                # typeof new Boolean() === "object"
                traverser._debug("Stripping global typeof")
                new_temp.value.TYPEOF = "object"
                return new_temp
        elif "return" in temp.global_data:
            new_temp = temp.global_data["return"](
                wrapper=node, arguments=args, traverser=traverser)
            if new_temp is not None:
                return new_temp
        elem.value = temp
    return elem


def CallExpression(traverser, node):
    args = [traverser.traverse_node(a) for a in node["arguments"]]

    member = traverser.traverse_node(node["callee"])

    if (node["callee"]["type"] == "MemberExpression" and
          node["callee"]["property"]["type"] == "Identifier"):

        # If we can identify the function being called on any member of any
        # instance, we can use that to either generate an output value or test
        # for additional conditions.
        identifier_name = node["callee"]["property"]["name"]
        if identifier_name in instanceactions.INSTANCE_DEFINITIONS:
            traverser._debug('Calling instance action...')
            result = instanceactions.INSTANCE_DEFINITIONS[identifier_name](
                        args, traverser, node, wrapper=member)
            return result

    if member.is_global and "return" in member.value.global_data:
        traverser._debug("EVALUATING RETURN...")
        output = member.value.global_data["return"](
            wrapper=member, arguments=args, traverser=traverser)
        if output is not None:
            return output
    return JSObject(traverser=traverser)


def _get_member_exp_property(traverser, node):
    """Return the string value of a member expression's property."""

    if node["property"]["type"] == "Identifier" and not node["computed"]:
        return unicode(node["property"]["name"])
    else:
        eval_exp = traverser.traverse_node(node["property"])
        return utils.get_as_str(eval_exp.get_literal_value())


def MemberExpression(traverser, node, instantiate=False):
    "Traces a MemberExpression and returns the appropriate object"

    traverser._debug("TESTING>>%s" % node["type"])
    if node["type"] == "MemberExpression":
        # x.y or x[y]
        # x = base
        base = MemberExpression(traverser, node["object"], instantiate)
        identifier = _get_member_exp_property(traverser, node)

        traverser._debug("MEMBER_EXP>>PROPERTY (%s)" % identifier)
        return base.get(traverser, identifier, instantiate=instantiate)

    elif node["type"] == "Identifier":
        traverser._debug("MEMBER_EXP>>ROOT:IDENTIFIER (%s)" % node["name"])

        # If we're supposed to instantiate the object and it doesn't already
        # exist, instantitate the object.
        if instantiate and not traverser._is_defined(node["name"]):
            output = JSWrapper(JSObject(), traverser=traverser)
            traverser.contexts[0].set(node["name"], output)
        else:
            output = traverser._seek_variable(node["name"])

        return output
    else:
        traverser._debug("MEMBER_EXP>>ROOT:EXPRESSION")
        # It's an expression, so just try your damndest.
        return traverser.traverse_node(node)


def Literal(traverser, node):
    """
    Convert a literal node in the parse tree to its corresponding
    interpreted value.
    """
    value = node["value"]
    if isinstance(value, dict):
        return JSObject(traverser=traverser)
    return JSLiteral(value, traverser=traverser)


def Identifier(traverser, node):
    "Initiates an object lookup on the traverser based on an identifier token"

    name = node["name"]
    if traverser._is_defined(name):
        return traverser._seek_variable(name)

    return JSObject(traverser=traverser)


#(branches,
# explicitly_dynamic,
# estab_context,
# action,
# returns, # as in yielding a value, not breaking execution
# block_statement,
#)

def node(branches=None, dynamic=False, action=None, returns=False,
         is_block=False):
    if branches is None:
        branches = ()
    return branches, dynamic, action, returns, is_block


DEFINITIONS = {
    "EmptyStatement": node(),
    "DebuggerStatement": node(),

    "Program": node(branches=("body", ), is_block=True),
    "BlockStatement": node(branches=("body", ), is_block=True),
    "ExpressionStatement": node(branches=("expression", ),
                                action=ExpressionStatement,
                                returns=True),
    "IfStatement": node(branches=("test", "alternate", "consequent"),
                        is_block=True),
    "LabeledStatement": node(branches=("body", )),
    "BreakStatement": node(),
    "ContinueStatement": node(),
    "WithStatement": node(branches=("body", "object"), action=WithStatement,
                          is_block=True),
    "SwitchStatement": node(branches=("test", "cases"), is_block=True),
    "ReturnStatement": node(branches=("argument", )),
    "ThrowStatement": node(branches=("argument", )),
    "TryStatement": node(branches=("block", "handler", "finalizer",
                                   "guardedHandlers"),
                         is_block=True),
    "WhileStatement": node(branches=("test", "body"), is_block=True),
    "DoWhileStatement": node(branches=("test", "body"), is_block=True),
    "ForStatement": node(branches=("init", "test", "update", "body"),
                         is_block=True),
    "ForInStatement": node(branches=("left", "right", "body"), is_block=True),
    "ForOfStatement": node(branches=("left", "right", "body"), is_block=True),

    "FunctionDeclaration": node(branches=("body", ), dynamic=True,
                                action=FunctionDeclaration, is_block=True),
    "VariableDeclaration": node(branches=("declarations", ),
                                action=VariableDeclaration),

    "ThisExpression": node(action=ThisExpression, returns=True),
    "ArrayExpression": node(branches=("elements", ), action=ArrayExpression,
                            returns=True),
    "ObjectExpression": node(branches=("properties", ),
                             action=ObjectExpression, returns=True),
    "FunctionExpression": node(branches=("body", ), dynamic=True,
                               action=FunctionExpression, returns=True,
                               is_block=True),
    "SequenceExpression": node(branches=("expressions", ), returns=True),
    "UnaryExpression": node(branches=("argument", ), action=UnaryExpression,
                            returns=True),
    "BinaryExpression": node(branches=("left", "right"),
                             action=BinaryExpression, returns=True),
    "AssignmentExpression": node(branches=("left", "right"),
                                 action=AssignmentExpression, returns=True),
    "UpdateExpression": node(branches=("argument", ), returns=True),
    "LogicalExpression": node(branches=("left", "right"), returns=True),
    "ConditionalExpression": node(branches=("test", "alternate", "consequent"),
                                  returns=True),
    "NewExpression": node(branches=("constructor", "arguments"),
                          action=NewExpression, returns=True),
    "CallExpression": node(branches=("callee", "arguments"),
                           action=CallExpression, returns=True),
    "MemberExpression": node(branches=("object", "property"),
                             action=MemberExpression, returns=True),
    "YieldExpression": node(branches=("argument"), returns=True),
    "ComprehensionExpression": node(branches=("body", "filter"), returns=True),
    "GeneratorExpression": node(branches=("body", "filter"), returns=True),

    "ObjectPattern": node(),
    "ArrayPattern": node(),

    "SwitchCase": node(branches=("test", "consequent")),
    "CatchClause": node(branches=("param", "guard", "body"), returns=True),
    "ComprehensionBlock": node(branches=("left", "right"), returns=True),

    "Literal": node(action=Literal, returns=True),
    "Identifier": node(action=Identifier, returns=True),
    "UnaryOperator": node(returns=True),
    "BinaryOperator": node(returns=True),
    "LogicalOperator": node(returns=True),
    "AssignmentOperator": node(returns=True),
    "UpdateOperator": node(returns=True),
}
