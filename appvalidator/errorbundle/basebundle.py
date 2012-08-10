import json
import sys
import uuid
from StringIO import StringIO

from .outputhandlers.shellcolors import OutputHandler
from .. import unicodehelper


class BaseErrorBundle(object):
    """This class does all sorts of cool things. It gets passed around
    from test to test and collects up all the errors like the candy man
    'separating the sorrow and collecting up all the cream.' It's
    borderline magical.

    Keyword Arguments:

    **determined**
        Whether the validator should continue after a tier fails
    **listed**
        True if the add-on is destined for AMO, false if not
    **instant**
        Who knows what this does
    **spidermonkey**
        Optional path to the local spidermonkey installation
    """

    def __init__(self, determined=True, instant=False, *args, **kwargs):

        self.handler = None

        self.errors = []
        self.warnings = []
        self.notices = []
        self.message_count = 0

        self.ending_tier = self.tier = 1

        self.unfinished = False

        self.instant = instant
        self.determined = determined

        super(BaseErrorBundle, self).__init__(*args, **kwargs)

    def error(self, err_id, error,
              description='', filename='', line=None, column=None,
              context=None, tier=None):
        "Stores an error message for the validation process"
        self._save_message(self.errors,
                           "errors",
                           {"id": err_id, "message": error, "description": description,
                            "file": filename,
                            "line": line,
                            "column": column,
                            "tier": tier},
                           context=context)
        return self

    def warning(self, err_id, warning,
                description='', filename='', line=None, column=None,
                context=None, tier=None):
        "Stores a warning message for the validation process"
        self._save_message(self.warnings,
                           "warnings",
                           {"id": err_id,
                            "message": warning,
                            "description": description,
                            "file": filename,
                            "line": line,
                            "column": column,
                            "tier": tier},
                           context=context)
        return self

    def notice(self, err_id, notice,
               description="", filename="", line=None, column=None,
               context=None, tier=None):
        "Stores an informational message about the validation"
        self._save_message(self.notices,
                           "notices",
                           {"id": err_id,
                            "message": notice,
                            "description": description,
                            "file": filename,
                            "line": line,
                            "column": column,
                            "tier": tier},
                           context=context)
        return self

    def set_tier(self, tier):
        "Updates the tier and ending tier"
        self.tier = tier
        if tier > self.ending_tier:
            self.ending_tier = tier

    def _save_message(self, stack, type_, message, context=None):
        "Stores a message in the appropriate message stack."

        self.message_count += 1

        uid = uuid.uuid4().hex
        message["uid"] = uid

        # Get the context for the message (if there's a context available)
        if context is not None:
            if isinstance(context, tuple):
                message["context"] = context
            else:
                message["context"] = context.get_context(
                    line=message["line"], column=message["column"])
        else:
            message["context"] = None

        message["message"] = unicodehelper.decode(message["message"])
        message["description"] = unicodehelper.decode(message["description"])

        # Save the message to the stack.
        stack.append(message)

        # Mark the tier that the error occurred at.
        if message["tier"] is None:
            message["tier"] = self.tier

        # If instant mode is turned on, output the message immediately.
        if self.instant:
            self._print_message(type_, message, verbose=True)

    def failed(self, fail_on_warnings=True):
        """Returns a boolean value describing whether the validation
        succeeded or not."""

        return bool(self.errors) or (fail_on_warnings and bool(self.warnings))

    def render_json(self):
        "Returns a JSON summary of the validation operation."

        types = {0: "unknown",
                 1: "extension",
                 2: "theme",
                 3: "dictionary",
                 4: "langpack",
                 5: "search",
                 8: "webapp"}
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

        ext_output = self._extend_json()
        output.update(ext_output)

        # Output the JSON.
        return json.dumps(output)

    def print_summary(self, verbose=False, no_color=False):
        "Prints a summary of the validation process so far."

        types = {0: "Unknown",
                 8: "App"}

        buffer = StringIO()
        self.handler = OutputHandler(buffer, no_color)

        # Make a neat little printout.
        self.handler.write("\n<<GREEN>>Summary:") \
            .write("-" * 30)

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
        if isinstance(data, (str, unicode)):
            return data
        elif isinstance(data, (list, tuple)):
            return "\n".join(self._flatten_list(x) for x in data)

    def _print_message(self, prefix, message, verbose=True):
        "Prints a message and takes care of all sorts of nasty code"

        # Load up the standard output.
        output = ["\n",
                  prefix,
                  message["message"],
                  "\n"]

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
                verbose_output.extend([("\t> %s" % x
                                        if x is not None
                                        else "\t>" + ("-" * 20))
                                       for x
                                       in message["context"]])

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

        stacks = [self.errors, self.warnings, self.notices]
        for stack in stacks:
            for message in stack:
                if message["tier"] > ending_tier:
                    stack.remove(message)
