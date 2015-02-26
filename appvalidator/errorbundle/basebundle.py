import sys
import types
import uuid
from StringIO import StringIO

import json

from .outputhandlers.shellcolors import OutputHandler
from .. import unicodehelper


class BaseErrorBundle(object):
    """Keyword Arguments:

    **determined**
        Whether the validator should continue after a tier fails
    **instant**
        Who knows what this does

    """

    def __init__(self, determined=True, instant=False, *args, **kwargs):

        self.handler = None

        self.errors = []
        self.warnings = []
        self.notices = []

        self.ending_tier = self.tier = 1

        self.unfinished = False

        self.instant = instant
        self.determined = determined

        super(BaseErrorBundle, self).__init__(*args, **kwargs)

    def _message(type_, message_type):
        def wrap(self, *args, **kwargs):
            arg_len = len(args)
            message = {
                "uid": uuid.uuid4().hex,
                "id": kwargs.get("err_id") or args[0],
                "message": unicodehelper.decode(
                    kwargs.get(message_type) or args[1]),
                "description": unicodehelper.decode(
                    kwargs.get("description", args[2] if
                               arg_len > 2 else None)),
                # Filename is never None.
                "file": kwargs.get("filename",
                                   args[3] if arg_len > 3 else ""),
                "line": kwargs.get("line",
                                   args[4] if arg_len > 4 else None),
                "column": kwargs.get("column",
                                     args[5] if arg_len > 5 else None),
                "tier": kwargs.get("tier", self.tier),
                "context": None,
            }

            destination = getattr(self, type_)
            # Don't show duplicate messages.
            if any(x["id"] == message["id"] and
                   x["file"] == message["file"] and
                   x["line"] == message["line"] and
                   x["column"] == message["column"] for x in destination):
                return self

            context = kwargs.get("context")
            if context is not None:
                if isinstance(context, tuple):
                    message["context"] = context
                else:
                    message["context"] = context.get_context(
                        line=message["line"], column=message["column"])

            # Append the message to the right stack.
            destination.append(message)

            # If instant mode is turned on, output the message immediately.
            if self.instant:
                self._print_message(type_, message, verbose=True)

            return self
        return wrap

    # And then all the real functions. Ahh, how clean!
    error = _message("errors", "error")
    warning = _message("warnings", "warning")
    notice = _message("notices", "notice")

    def set_tier(self, tier):
        "Updates the tier and ending tier"
        self.tier = tier
        if tier > self.ending_tier:
            self.ending_tier = tier

    @property
    def message_count(self):
        return len(self.errors) + len(self.warnings) + len(self.notices)

    def failed(self, fail_on_warnings=True):
        """Returns a boolean value describing whether the validation
        succeeded or not."""

        return bool(self.errors) or (fail_on_warnings and bool(self.warnings))

    def render_json(self):
        "Returns a JSON summary of the validation operation."

        types = {0: "unknown", 8: "webapp"}
        output = {"ending_tier": self.ending_tier,
                  "success": not self.failed(),
                  "messages": [],
                  "errors": len(self.errors),
                  "warnings": len(self.warnings),
                  "notices": len(self.notices)}

        messages = output["messages"]

        # Copy messages to the JSON output
        for error in self.errors:
            error["type"] = "error"
            messages.append(error)

        for warning in self.warnings:
            warning["type"] = "warning"
            messages.append(warning)

        for notice in self.notices:
            notice["type"] = "notice"
            messages.append(notice)

        output.update(self._extend_json())

        # Output the JSON.
        return json.dumps(output, ensure_ascii=True)

    def _extend_json(self):
        """Override this method to extend the JSON produced by the bundle."""
        pass

    def print_summary(self, verbose=False, no_color=False):
        "Prints a summary of the validation process so far."

        buffer = StringIO()
        self.handler = OutputHandler(buffer, no_color)

        # Make a neat little printout.
        self.handler.write("\n<<GREEN>>Summary:").write("-" * 30)
        self.handler.write("%s Errors, %s Warnings, %s Notices" %
            (len(self.errors), len(self.warnings), len(self.notices)))


        if self.failed():
            self.handler.write("<<BLUE>>Test failed! Errors:")

            # Print out all the errors/warnings:
            for error in self.errors:
                self._print_message("<<RED>>Error:<<NORMAL>>\t",
                                    error, verbose)
            for warning in self.warnings:
                self._print_message("<<YELLOW>>Warning:<<NORMAL>> ",
                                    warning, verbose)
        else:
            self.handler.write("<<GREEN>>All tests succeeded!")

        if self.notices:
            for notice in self.notices:
                self._print_message(prefix="<<WHITE>>Notice:<<NORMAL>>\t",
                                    message=notice,
                                    verbose=verbose)

        self.handler.write("\n")
        if self.unfinished:
            self.handler.write("<<RED>>Validation terminated early")
            self.handler.write("Errors during validation are preventing"
                               "the validation proecss from completing.")
            self.handler.write("Use the <<YELLOW>>--determined<<NORMAL>> "
                               "flag to ignore these errors.")
            self.handler.write("\n")

        return buffer.getvalue()

    def _flatten_list(self, data):
        "Flattens nested lists into strings."

        if data is None:
            return ""
        if isinstance(data, types.StringTypes):
            return data
        elif isinstance(data, (list, tuple)):
            return "\n".join(map(self._flatten_list, data))

    def _print_message(self, prefix, message, verbose=True):
        "Prints a message and takes care of all sorts of nasty code"

        # Load up the standard output.
        output = ["\n", prefix, message["message"]]

        # We have some extra stuff for verbose mode.
        if verbose:
            verbose_output = []

            # Detailed problem description.
            if message["description"]:
                verbose_output.append(
                    self._flatten_list(message["description"]))

            # Show the user what tier we're on
            verbose_output.append("\tTier:\t%d" % message["tier"])

            # If file information is available, output that as well.
            files = message["file"]
            if files is not None and files != "":
                fmsg = "\tFile:\t%s"

                # Nested files (subpackes) are stored in a list.
                if type(files) is list:
                    if files[-1] == "":
                        files[-1] = "(none)"
                    verbose_output.append(fmsg % ' > '.join(files))
                else:
                    verbose_output.append(fmsg % files)

            # If there is a line number, that gets put on the end.
            if message["line"]:
                verbose_output.append("\tLine:\t%s" % message["line"])
            if message["column"] and message["column"] != 0:
                verbose_output.append("\tColumn:\t%d" % message["column"])

            if "context" in message and message["context"]:
                verbose_output.append("\tContext:")
                verbose_output.extend(
                    [("\t> %s" % ("-" * 20 if x is None else x)) for
                     x in message.get("context", [])])

            # Stick it in with the standard items.
            output.append("\n")
            output.append("\n".join(verbose_output))

        # Send the final output to the handler to be rendered.
        self.handler.write(u''.join(map(unicodehelper.decode, output)))

    def discard_unused_messages(self, ending_tier):
        """
        Delete messages from errors, warnings, and notices whose tier is
        greater than the ending tier.
        """

        for stack in [self.errors, self.warnings, self.notices]:
            for message in stack:
                if message["tier"] > ending_tier:
                    stack.remove(message)
