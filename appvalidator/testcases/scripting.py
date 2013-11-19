import javascript.traverser as traverser
import javascript.acorn as acorn
import javascript.spidermonkey as spidermonkey
from appvalidator.constants import SPIDERMONKEY_INSTALLATION
from ..contextgenerator import ContextGenerator


def test_js_file(err, filename, data, line=0, context=None):
    "Tests a JS file by parsing and analyzing its tokens"

    # Don't even try to run files bigger than 1MB.
    if len(data) > 1024 * 1024:
        err.warning(
            err_id=("js", "skip", "didnt_even_try"),
            warning="Didn't even try to validate large JS file.",
            description="A very large JS file was skipped in the validation "
                        "process. It's over a megabyte.",
            filename=filename)
        return

    # Set the tier to 4 (Security Tests)
    if err is not None:
        before_tier = err.tier
        err.set_tier(3)

    tree = None

    get_tree = spidermonkey.get_tree
    spidermonkey_path = (err and err.get_resource("SPIDERMONKEY") or
                         SPIDERMONKEY_INSTALLATION)
    if err.get_resource("acorn") or not spidermonkey_path:
        get_tree = acorn.get_tree

    try:
        tree = get_tree(data, err, filename, spidermonkey_path)
    except RuntimeError as exc:
        warning ="JS: Unknown runtime error"
        if "out of memory" in str(exc):
            warning = "JS: Out of memory exception"
        err.warning(
            err_id=("js", "parse", "runtimeerror"),
            warning=warning,
            description="An error was encountered while trying to validate a "
                        "JS file.",
            filename=filename)

    if not tree:
        err.metadata["ran_js_tests"] = "no;missing ast"
        if err is not None:
            err.set_tier(before_tier)
        return

    trav = traverser.Traverser(
        err, filename, line, context=context or ContextGenerator(data))
    trav.run(tree)

    err.metadata["ran_js_tests"] = "yes"

    # Reset the tier so we don't break the world
    if err is not None:
        err.set_tier(before_tier)
