import argparse
import json
import os
import sys
import zipfile
from StringIO import StringIO

from .validate import validate
from constants import *


def main():
    "Main function. Handles delegation to other functions."

    expectations = {"any": PACKAGE_ANY,
                    "webapp": PACKAGE_WEBAPP}

    # Parse the arguments that
    parser = argparse.ArgumentParser(
        description="Run tests on a Mozilla-type addon.")

    parser.add_argument("package",
                        help="The path of the package you're testing")
    parser.add_argument("-o",
                        "--output",
                        default="text",
                        choices=("text", "json"),
                        help="The output format that you expect",
                        required=False)
    parser.add_argument("-v",
                        "--verbose",
                        action="store_const",
                        const=True,
                        help="""If the output format supports it, makes
                        the analysis summary include extra info.""")
    parser.add_argument("--boring",
                        action="store_const",
                        const=True,
                        help="""Activating this flag will remove color
                        support from the terminal.""")
    parser.add_argument("--determined",
                        action="store_const",
                        const=True,
                        help="""This flag will continue running tests in
                        successive tests even if a lower tier fails.""")
    parser.add_argument("--selfhosted",
                        action="store_const",
                        const=True,
                        help="""Indicates that the addon will not be
                        hosted on addons.mozilla.org. This allows the
                        <em:updateURL> element to be set.""")
    parser.add_argument("--timeout",
                        help="The amount of time before validation is "
                             "terminated with a timeout exception.",
                        default="60")

    args = parser.parse_args()

    # We want to make sure that the output is expected. Parse out the expected
    # type for the add-on and pass it in for validation.
    if args.type not in expectations:
        # Fail if the user provided invalid input.
        print "Given expectation (%s) not valid. See --help for details" % \
                args.type
        sys.exit(1)

    try:
        timeout = int(args.timeout)
    except ValueError:
        print "Invalid timeout. Integer expected."
        sys.exit(1)

    expectation = expectations[args.type]
    error_bundle = validate(args.package,
                            format=None,
                            determined=args.determined,
                            listed=not args.selfhosted,
                            timeout=timeout)

    # Print the output of the tests based on the requested format.
    if args.output == "text":
        print error_bundle.print_summary(verbose=args.verbose,
                                         no_color=args.boring).encode("utf-8")
    elif args.output == "json":
        sys.stdout.write(error_bundle.render_json())

    if error_bundle.failed():
        sys.exit(1)
    else:
        sys.exit(0)

# Start up the testing and return the output.
if __name__ == '__main__':
    main()
