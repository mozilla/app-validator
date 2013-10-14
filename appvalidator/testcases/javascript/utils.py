import types


def get_as_num(value):
    """Return the JS numeric equivalent for a value."""
    if hasattr(value, 'get_literal_value'):
        value = value.get_literal_value()

    if value is None:
        return 0

    try:
        if isinstance(value, types.StringTypes):
            if value.startswith("0x"):
                return int(value, 16)
            else:
                return float(value)
        elif isinstance(value, (int, float, long)):
            return value
        else:
            return int(value)
    except (ValueError, TypeError):
        return 0


def get_as_str(value):
    """Return the JS string equivalent for a literal value."""
    if hasattr(value, 'get_literal_value'):
        value = value.get_literal_value()

    if value is None:
        return ""

    if isinstance(value, bool):
        return u"true" if value else u"false"
    elif isinstance(value, (int, float, long)):
        if value == float('inf'):
            return u"Infinity"
        elif value == float('-inf'):
            return u"-Infinity"

        # Try to see if we can shave off some trailing significant figures.
        try:
            if int(value) == value:
                return unicode(int(value))
        except (ValueError, TypeError):
            pass
    return unicode(value)


def get_NaN(traverser):
    # If we've cached the traverser's NaN instance, just use that.
    ncache = getattr(traverser, "NAN_CACHE", None)
    if ncache is not None:
        return ncache

    # Otherwise, we need to import GLOBAL_ENTITIES and build a raw copy.
    from predefinedentities import GLOBAL_ENTITIES
    ncache = traverser._build_global("NaN", GLOBAL_ENTITIES[u"NaN"])
    # Cache it so we don't need to do this again.
    traverser.NAN_CACHE = ncache
    return ncache


def evaluate_lambdas(traverser, node):
    if callable(node):
        return evaluate_lambdas(traverser, node(traverser))
    else:
        return node
