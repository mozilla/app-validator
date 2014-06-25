import re
import sys
import types

import appvalidator.unicodehelper as unicodehelper
from . import csstester
from appvalidator.contextgenerator import ContextGenerator
from appvalidator.constants import *
from appvalidator.csp import warn as message_csp
from appvalidator.python.HTMLParser import HTMLParser, HTMLParseError


DEBUG = False

UNSAFE_TAGS = ("script", "object", "embed", "base", )
SELF_CLOSING_TAGS = ("area", "base", "basefont", "br", "col", "frame", "hr",
                     "img", "input", "li", "link", "meta", "p", "param", )
TAG_NOT_OPENED = "Tag (%s) being closed before it is opened."
REMOTE_URL_PATTERN = re.compile("((ht|f)tps?:)?//")

DOM_MUTATION_HANDLERS = set([
        "ondomattrmodified", "ondomattributenamechanged",
        "ondomcharacterdatamodified", "ondomelementnamechanged",
        "ondomnodeinserted", "ondomnodeinsertedintodocument", "ondomnoderemoved",
        "ondomnoderemovedfromdocument", "ondomsubtreemodified", ])


class MarkupParser(HTMLParser):
    """Parse and analyze the versious components of markup files."""

    def __init__(self, err, strict=True, debug=False):
        HTMLParser.__init__(self)
        self.err = err
        self.is_jetpack = "is_jetpack" in err.metadata  # Cache this value.
        self.line = 0
        self.strict = strict
        self.debug = debug

        self.context = None

        self.xml_state = []
        self.xml_line_stack = []
        self.xml_buffer = []

        self.reported = set()

    def process(self, filename, data, extension="html"):
        """Processes data by splitting it into individual lines, then
        incrementally feeding each line into the parser, increasing the
        value of the line number with each line."""

        self.line = 0
        self.filename = filename
        self.extension = extension.lower()

        self.reported = set()

        self.context = ContextGenerator(data)

        lines = data.split("\n")

        buffering = False
        pline = 0
        for line in lines:
            self.line += 1

            search_line = line
            while True:
                # If a CDATA element is found, push it and its contents to the
                # buffer. Push everything previous to it to the parser.
                if "<![CDATA[" in search_line and not buffering:
                    # Find the CDATA element.
                    cdatapos = search_line.find("<![CDATA[")

                    # If the element isn't at the start of the line, pass
                    # everything before it to the parser.
                    if cdatapos:
                        self._feed_parser(search_line[:cdatapos])
                    # Collect the rest of the line to send it to the buffer.
                    search_line = search_line[cdatapos:]
                    buffering = True
                    continue

                elif "]]>" in search_line and buffering:
                    # If we find the end element on the line being scanned,
                    # buffer everything up to the end of it, and let the rest
                    # of the line pass through for further processing.
                    end_cdatapos = search_line.find("]]>") + 3
                    self._save_to_buffer(search_line[:end_cdatapos])
                    search_line = search_line[end_cdatapos:]
                    buffering = False
                break

            if buffering:
                self._save_to_buffer(search_line + "\n")
            else:
                self._feed_parser(search_line)

    def _feed_parser(self, line):
        """Feed incoming data into the underlying HTMLParser."""

        line = unicodehelper.decode(line)

        try:
            self.feed(line + u"\n")
        except UnicodeDecodeError, exc_instance:
            # There's no recovering from a unicode error here. We've got the
            # unicodehelper; if that doesn't help us, nothing will.
            return
        except HTMLParseError as inst:
            if DEBUG:  # pragma: no cover
                print self.xml_state, inst

            if "markup" in self.reported:
                return

            if ("script" in self.xml_state or
                self.debug and "testscript" in self.xml_state):
                if "script_comments" in self.reported or not self.strict:
                    return
                self.err.notice(
                    err_id=("testcases_markup_markuptester", "_feed",
                            "missing_script_comments"),
                    notice="Missing comments in <script> tag",
                    description="Markup parsing errors occurred while trying "
                                "to parse the file. This would likely be "
                                "mitigated by wrapping <script> tag contents "
                                "in HTML comment tags (<!-- -->)",
                    filename=self.filename,
                    line=self.line,
                    context=self.context,
                    tier=2)
                self.reported.add("script_comments")
                return

            if self.strict:
                self.err.warning(
                    err_id=("testcases_markup_markuptester", "_feed",
                            "parse_error"),
                    warning="Markup parsing error",
                    description=["There was an error parsing a markup file.",
                                 str(inst)],
                    filename=self.filename,
                    line=self.line,
                    context=self.context)
            self.reported.add("markup")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, True)
        self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs, self_closing=False):

        # Normalize!
        tag = tag.lower()

        # Be extra sure it's not a self-closing tag.
        if not self_closing:
            self_closing = tag in SELF_CLOSING_TAGS

        if DEBUG:  # pragma: no cover
            print "S: ", self.xml_state, tag, self_closing

        attr_dict = dict([(a[0].lower(), a[1]) for a in attrs if a[1]])

        if "style" in attr_dict:
            csstester.test_css_snippet(
                self.err, self.filename, attr_dict["style"], self.line)

        event_attribute = lambda k: k.startswith("on") and "-" not in k
        script_attributes = dict(
            (k, v) for k, v in attr_dict.iteritems() if event_attribute(k))
        if script_attributes:
            if any(k in DOM_MUTATION_HANDLERS for k in script_attributes):
                self.err.error(
                    err_id=("testcases_markup_markuptester",
                            "handle_starttag", "dom_manipulation_handler"),
                    error="DOM Mutation Events Prohibited",
                    description="DOM mutation events are flagged because of "
                                "their deprecated status, as well as thier "
                                "extreme inefficiency. Consider using a "
                                "different event.",
                    filename=self.filename,
                    line=self.line,
                    context=self.context)

            message_csp(err=self.err, filename=self.filename,
                        line=self.line, column=None, context=self.context,
                        violation_type="script_attribute", severity="error")

        # When the dev forgets their <!-- --> on a script tag, bad
        # things happen.
        if "script" in self.xml_state and tag != "script":
            self._save_to_buffer("<" + tag + self._format_args(attrs) + ">")
            return

        elif (tag == "script" and
              ("type" not in attr_dict or
               any(a[0] == "type" and "javascript" in a[1].lower() for
                   a in attrs))):
            # Inspect scripts which either have no type or have a type which
            # is JS.

            if "src" not in attr_dict:
                # CSP warnings for inline scripts
                message_csp(err=self.err, filename=self.filename,
                            line=self.line, column=None,
                            context=self.context,
                            violation_type="inline_script",
                            severity="error")

            elif not self._is_url_local(attr_dict.get("src", "")):
                # If there's a remote SRC, then that's a CSP violation.
                message_csp(err=self.err, filename=self.filename,
                            line=self.line, column=None, context=self.context,
                            violation_type="remote_script", severity="error")

        self.xml_state.append(tag)
        self.xml_line_stack.append(self.line)
        self.xml_buffer.append(u"")

    def handle_endtag(self, tag):

        tag = tag.lower()

        if DEBUG:  # pragma: no cover
            print "E: ", tag, self.xml_state

        if not self.xml_state:
            if "closing_tags" in self.reported or not self.strict:
                if DEBUG:
                    print "Unstrict; extra closing tags ------"
                return
            self.err.warning(
                err_id=("markup", "handle_endtag", "extra_closing_tags"),
                warning="Markup parsing error",
                description="The markup file has more closing tags than it "
                            "has opening tags.",
                filename=self.filename,
                line=self.line,
                context=self.context,
                tier=2)

            self.reported.add("closing_tags")
            if DEBUG:  # pragma: no cover
                print "Too many closing tags ------"
            return

        elif "script" in self.xml_state[:-1]:
            # If we're in a script tag, nothing else matters. Just rush
            # everything possible into the xml buffer.

            self._save_to_buffer("</%s>" % tag)
            if DEBUG:
                print "Markup as text in script ------"
            return

        elif tag not in self.xml_state:
            # If the tag we're processing isn't on the stack, then
            # something is wrong.
            self.err.warning(
                err_id=("markup", "handle_endtag", "extra_closing_tags"),
                warning="Parse error: tag closed before opened",
                description=["Markup tags cannot be closed before they are "
                             "opened. Perhaps you were just a little "
                             "overzealous with forward-slashes?",
                             'Tag `%s` closed before it was opened' % tag],
                filename=self.filename,
                line=self.line,
                context=self.context,
                tier=2)

            if DEBUG:  # pragma: no cover
                print "Tag closed before opened ------"
            return

        data_buffer = self.xml_buffer.pop()
        old_state = self.xml_state.pop()
        old_line = self.xml_line_stack.pop()

        # If the tag on the stack isn't what's being closed and it also
        # classifies as a self-closing tag, we just recursively close
        # down to the level of the tag we're actualy closing.
        if old_state != tag and old_state in SELF_CLOSING_TAGS:
            if DEBUG:
                print "Self closing tag cascading down ------"
            return self.handle_endtag(tag)

        # If this is an XML-derived language, everything must nest
        # properly. No overlapping tags.
        if (old_state != tag and self.extension[0] == 'x' and not self.strict):
            self.err.warning(
                err_id=("testcases_markup_markuptester", "handle_endtag",
                        "invalid_nesting"),
                warning="Markup invalidly nested",
                description="It has been determined that the document "
                            "invalidly nests its tags. This is not permitted "
                            "in the specified document type.",
                filename=self.filename,
                line=self.line,
                context=self.context,
                tier=2)
            if DEBUG:  # pragma: no cover
                print "Invalid markup nesting ------"

        data_buffer = data_buffer.strip()

        # Perform analysis on collected data.
        if data_buffer and tag == "style":
            csstester.test_css_file(self.err, self.filename, data_buffer,
                                    old_line)

    def handle_data(self, data):
        self._save_to_buffer(data)

    def handle_comment(self, data):
        self._save_to_buffer(data)

    def parse_marked_section(self, i, report=0):
        rawdata = self.rawdata
        _markedsectionclose = re.compile(r']\s*]\s*>')

        assert rawdata[i:i + 3] == '<![', \
               "unexpected call to parse_marked_section()"

        sectName, j = self._scan_name(i + 3, i)
        if j < 0:  # pragma: no cover
            return j
        if sectName in ("temp", "cdata", "ignore", "include", "rcdata"):
            # look for standard ]]> ending
            match = _markedsectionclose.search(rawdata, i + 3)
        else:  # pragma: no cover
            self.error('unknown status keyword %r in marked section' %
                       rawdata[i + 3:j])
        if not match:  # pragma: no cover
            return -1
        if report:  # pragma: no cover
            j = match.start(0)
            self.unknown_decl(rawdata[i + 3: j])
        return match.end(0)

    def _save_to_buffer(self, data):
        """Save data to the XML buffer for the current tag."""

        # We're not interested in data that isn't in a tag.
        if not self.xml_buffer:
            return

        self.xml_buffer[-1] += unicodehelper.decode(data)

    def _format_args(self, args):
        """Formats a dict of HTML attributes to be in HTML attribute
        format."""

        if not args:
            return ""

        return " " + " ".join('%s="%s"' % a for a in args)

    def _is_url_local(self, url):
        return not REMOTE_URL_PATTERN.match(url)
