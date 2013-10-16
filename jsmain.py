#!/usr/bin/env python

import sys

import appvalidator.testcases.scripting as scripting
import appvalidator.testcases.javascript.traverser
from appvalidator.constants import SPIDERMONKEY_INSTALLATION
from appvalidator.errorbundle import ErrorBundle
from appvalidator.errorbundle.outputhandlers.shellcolors import OutputHandler
from appvalidator.testcases.javascript.predefinedentities import GLOBAL_ENTITIES
from appvalidator.testcases.scripting import get_tree
appvalidator.testcases.javascript.traverser.JS_DEBUG = True

if __name__ == '__main__':
    err = ErrorBundle(instant=True)
    err.handler = OutputHandler(sys.stdout, False)
    err.supported_versions = {}
    if len(sys.argv) > 1:
        path = sys.argv[1]
        script = open(path).read()
        scripting.test_js_file(err=err,
                               filename=path,
                               data=script)
    else:
        trav = appvalidator.testcases.javascript.traverser.Traverser(err, "stdin")

        def do_callable(wrapper, arguments, traverser):
            for arg in arguments:
                print arg, arg.callable

        def do_inspect(wrapper, arguments, traverser):
            print "~" * 50
            for arg in arguments:
                print arg.output()
            print "~" * 50

        def do_exit(wrapper, arguments, traverser):
            print "Goodbye!"
            sys.exit()

        GLOBAL_ENTITIES[u"callable"] = {"return": do_callable}
        GLOBAL_ENTITIES[u"inspect"] = {"return": do_inspect}
        GLOBAL_ENTITIES[u"exit"] = {"return": do_exit}

        while True:
            line = raw_input("js> ")
            trav.debug_level = 0
            if line == "enable bootstrap\n":
                err.save_resource("em:bootstrap", True)
                continue
            elif line == "disable bootstrap\n":
                err.save_resource("em:bootstrap", False)
                continue
            elif line.startswith(("inspect ", "type ")):
                actions = {"inspect": lambda wrap: wrap.output(),
                           "type": lambda wrap: type(wrap.value)}
                vars = line.split()
                final_context = trav.contexts[-1]
                for var in vars[1:]:
                    if var not in final_context.data:
                        print "%s not found." % var
                        continue
                    wrap = final_context.data[var]
                    print actions[vars[0]](wrap)
                continue

            tree = get_tree(line, err, shell=SPIDERMONKEY_INSTALLATION)
            if tree is None:
                continue
            tree = tree["body"]
            for branch in tree:
                output = trav.traverse_node(branch)
                if output is not None:
                    print output.output()

            while trav.function_collection[0]:
                trav.function_collection[0].pop()()
