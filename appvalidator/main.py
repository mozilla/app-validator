import argparse
import json
import os
import sys
import zipfile
from StringIO import StringIO

from . import validate_app, validate_packaged_app
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

    try:
        timeout = int(args.timeout)
    except ValueError:
        print "Invalid timeout. Integer expected."
        sys.exit(1)

    error_bundle = validate_packaged_app(
        args.package, listed=not args.selfhosted, format=None, timeout=timeout)

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
