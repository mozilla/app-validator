import sys

import argparse
import requests

from . import validate_app, validate_packaged_app


def main():
    "Main function. Handles delegation to other functions."

    # Parse the arguments that
    parser = argparse.ArgumentParser(
        description="Run tests on a web app.")

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
    parser.add_argument("--unlisted",
                        action="store_const",
                        const=True,
                        help="Indicates that the app will not be listed on "
                             "the Firefox Marketplace.")
    parser.add_argument("--timeout",
                        help="The amount of time before validation is "
                             "terminated with a timeout exception.",
                        default="60")
    parser.add_argument("--acorn",
                        action="store_const",
                        const=True,
                        help="Uses Acorn instead of Spidermonkey for JS "
                             "parsing. Requirees Node and Acorn.")

    args = parser.parse_args()

    try:
        timeout = int(args.timeout)
    except ValueError:
        print "Invalid timeout. Integer expected."
        sys.exit(1)

    if "://" in args.package:
        error_bundle = validate_app(
            requests.get(args.package).content, listed=not args.unlisted,
            format=None, url=args.package, acorn=args.acorn)

    elif args.package.endswith(".webapp"):
        with open(args.package) as f:
            error_bundle = validate_app(
                f.read(), listed=not args.unlisted, format=None,
                acorn=args.acorn)

    else:
        error_bundle = validate_packaged_app(
            args.package, listed=not args.unlisted, format=None,
            timeout=timeout, acorn=args.acorn)

    # Print the output of the tests based on the requested format.
    if args.output == "text":
        print error_bundle.print_summary(
            verbose=args.verbose, no_color=args.boring).encode("utf-8")
    elif args.output == "json":
        sys.stdout.write(error_bundle.render_json())

    if error_bundle.failed():
        sys.exit(1)
    else:
        sys.exit(0)

# Start up the testing and return the output.
if __name__ == "__main__":
    main()
