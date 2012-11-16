from appvalidator.constants import BUGZILLA_BUG


ENTITIES = {}


def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(function):
        ENTITIES[name] = function
        return function
    return wrap


def entity(name, result=None):
    def return_wrap(t):
        output = ENTITIES[name](traverser=t)
        if result is not None:
            return result
        elif output is not None:
            return output
        else:
            return {"value": {}}
    return {"value": return_wrap}


@register_entity("Function")
@register_entity("eval")
def csp_warning_function(traverser):
    def call_wrap(*args, **kwargs):
        from appvalidator.csp import warn
        warn(err=traverser.err,
             filename=traverser.filename,
             line=traverser.line,
             column=traverser.position,
             context=traverser.context,
             violation_type="script")
        return False

    return {"dangerous": call_wrap,
            "return": call_wrap,
            "value": call_wrap, }


@register_entity("createElement")
def csp_warning_createElement(traverser):
    def wrap(a, t, e):
        if not a or "script" in _get_as_str(t(a[0])).lower():
            from appvalidator.csp import warn
            warn(err=traverser.err,
                 filename=traverser.filename,
                 line=traverser.line,
                 column=traverser.position,
                 context=traverser.context,
                 violation_type="createElement")
        return False

    return {"return": wrap}


@register_entity("createElementNS")
def csp_warning_createElementNS(traverser):
    def wrap(a, t, e):
        if not a or "script" in _get_as_str(t(a[1])).lower():
            from appvalidator.csp import warn
            warn(err=traverser.err,
                 filename=traverser.filename,
                 line=traverser.line,
                 column=traverser.position,
                 context=traverser.context,
                 violation_type="createElementNS")
        return False

    return {"return": wrap}


@register_entity("setTimeout")
@register_entity("setInterval")
def csp_warning_timeout(traverser):
    def wrap(a, t, e):
        if a and a[0]["type"] != "FunctionExpression":
            from appvalidator.csp import warn
            warn(err=traverser.err,
                 filename=traverser.filename,
                 line=traverser.line,
                 column=traverser.position,
                 context=traverser.context,
                 violation_type="set*")
        return False

    return {"dangerous": wrap}
