import re
import subprocess
import tempfile
from cStringIO import StringIO

import javascript.traverser as traverser
from javascript.spidermonkey import get_tree, JSReflectException
from appvalidator.constants import PACKAGE_THEME, SPIDERMONKEY_INSTALLATION
from ..contextgenerator import ContextGenerator
from ..textfilter import *


JS_ESCAPE = re.compile(r"\\+[ux]", re.I)


def test_js_file(err, filename, data, line=0, context=None, pollutable=False):
    "Tests a JS file by parsing and analyzing its tokens"

    if SPIDERMONKEY_INSTALLATION is None or \
       err.get_resource("SPIDERMONKEY") is None:  # Default value is False
        return

    before_tier = None
    # Set the tier to 4 (Security Tests)
    if err is not None:
        before_tier = err.tier
        err.set_tier(3)

    tree = get_tree(data,
                    filename=filename,
                    shell=(err and err.get_resource("SPIDERMONKEY")) or
                          SPIDERMONKEY_INSTALLATION,
                    err=err)
    if not tree:
        if before_tier:
            err.set_tier(before_tier)
        return

    # Generate a context if one is not available.
    if context is None:
        context = ContextGenerator(data)

    t = traverser.Traverser(err, filename, line, context=context)
    t.pollutable = pollutable
    t.run(tree)

    # Reset the tier so we don't break the world
    if err is not None:
        err.set_tier(before_tier)


def test_js_snippet(err, data, filename, line=0, context=None):
    "Process a JS snippet by passing it through to the file tester."

    if not data:
        return

    # Wrap snippets in a function to prevent the parser from freaking out
    # when return statements exist without a corresponding function.
    data = "(function(){%s\n})()" % data

    # NOTE: pollutable is set to True...for now
    test_js_file(err, filename, data, line, context, pollutable=True)

