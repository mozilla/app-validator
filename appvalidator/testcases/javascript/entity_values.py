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
        return output or {"value": {}}
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

    return {
        "dangerous": call_wrap,
        "return": call_wrap,
        "value": call_wrap,
    }


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


GUM_FEATURES = {
    "video": "CAMERA",
    "picture": "CAMERA",
    "audio": "MIC",
}

@register_entity("getUserMedia")
def getUserMedia(traverser):
    def method(wrapper, arguments, traverser):
        if not arguments:
            return False
        options = traverser.traverse_node(arguments[0])
        for feature in GUM_FEATURES:
            if (options.has_property(feature) and
                options.get(traverser, feature).get_literal_value() == True):
                traverser.log_feature(GUM_FEATURES[feature])

        if (options.has_property("video") and
            options.get(traverser, "video").has_property("mandatory") and
            options.get(traverser, "video").get(traverser, "mandatory") and
            options.get(traverser, "video").get(traverser, "mandatory"
                ).get(traverser, "chromeMediaSource"
                ).get_literal_value() == "screen"):
            traverser.log_feature("SCREEN_CAPTURE")

    return {"return": method}


@register_entity("XMLHttpRequest")
def XMLHttpRequest(traverser):
    def dangerous(a, t, e):
        print a, e
        if a and len(a) >= 3 and not t(a[2]).get_literal_value():
            return ("Synchronous HTTP requests can cause serious UI "
                    "performance problems, especially to users with "
                    "slow network connections.")

    def new(traverser, node, elem):
        if not node["arguments"]:  # Ignore XHR without args
            return elem
        arg = traverser.traverse_node(node["arguments"][0])
        if (arg.has_property("mozSystem") and
            arg.get(traverser, "mozSystem").get_literal_value()):
            traverser.log_feature("SYSTEMXHR")
        return elem

    return {
        "value": {u"open": {"dangerous": dangerous}},
        "new": new,
    }