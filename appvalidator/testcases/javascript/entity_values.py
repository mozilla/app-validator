ENTITIES = {}
def register_entity(name):
    """Allow an entity's modifier to be registered for use."""
    def wrap(function):
        ENTITIES[name] = function
        return function
    return wrap


def entity(name, result=None):
    ent = ENTITIES[name]
    if callable(ent):
        ent = ent()
        ENTITIES[name] = ent
    return ent or {"value": {}}


@register_entity("Function")
@register_entity("eval")
def csp_warning_function():
    def call_wrap(*args, **kwargs):
        traverser = kwargs.get("traverser") or args[-1]
        from appvalidator.csp import warn
        warn(err=traverser.err,
             filename=traverser.filename,
             line=traverser.line,
             column=traverser.position,
             context=traverser.context,
             violation_type="script")

    return {
        "new": call_wrap,
        "return": call_wrap,
        "value": call_wrap,
    }


@register_entity("setTimeout")
@register_entity("setInterval")
def csp_warning_timeout():
    def wrap(wrapper, arguments, traverser):
        if arguments and not arguments[0].callable:
            from appvalidator.csp import warn
            warn(err=traverser.err,
                 filename=traverser.filename,
                 line=traverser.line,
                 column=traverser.position,
                 context=traverser.context,
                 violation_type="set*")

    return {"return": wrap}


GUM_FEATURES = {
    "video": "CAMERA",
    "picture": "CAMERA",
    "audio": "MIC",
}

@register_entity("getUserMedia")
def getUserMedia():
    def method(wrapper, arguments, traverser):
        if not arguments:
            return False
        options = arguments[0]
        for feature in GUM_FEATURES:
            if (options.has_var(feature) and
                options.get(traverser, feature).get_literal_value() == True):
                traverser.log_feature(GUM_FEATURES[feature])

        if (options.has_var("video") and
            options.get(traverser, "video").has_var("mandatory") and
            options.get(traverser, "video").get(traverser, "mandatory") and
            options.get(traverser, "video").get(traverser, "mandatory"
                ).get(traverser, "chromeMediaSource"
                ).get_literal_value() == "screen"):
            traverser.log_feature("SCREEN_CAPTURE")

    return {"return": method}


@register_entity("XMLHttpRequest")
def XMLHttpRequest():
    def return_(wrapper, arguments, traverser):
        if (arguments and len(arguments) >= 3 and
            not arguments[2].get_literal_value()):
            traverser.err.warning(
                err_id=("javascript", "xhr", "sync"),
                warning="Synchronous XHR should not be used",
                description="Synchronous HTTP requests can cause serious UI "
                            "performance problems, especially to users with "
                            "slow network connections.",
                filename=traverser.filename,
                line=traverser.line,
                column=traverser.position,
                context=traverser.context)
        return wrapper

    def new(node, arguments, traverser):
        if not node["arguments"]:  # Ignore XHR without args
            return
        arg = traverser.traverse_node(node["arguments"][0])
        if (arg.has_var("mozSystem") and
            arg.get(traverser, "mozSystem").get_literal_value()):
            traverser.log_feature("SYSTEMXHR")

    return {
        "value": {u"open": {"return": return_}},
        "new": new,
    }
