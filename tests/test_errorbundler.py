import sys
from StringIO import StringIO

import json
from mock import patch
from nose.tools import eq_

from helper import TestCase

from appvalidator.contextgenerator import ContextGenerator
from appvalidator.errorbundle import ErrorBundle


class ErrorBundleTestCase(TestCase):

    def setUp(self):
        super(ErrorBundleTestCase, self).setUp()
        self.setup_err()

    def get_json_results(self):
        return json.loads(self.err.render_json())


class TestErrorBundle(ErrorBundleTestCase):

    def test_message_completeness(self):
        """Test we're fully expecting all of the values for a message."""

        self.err.error(
            ("id", ),
            "error",
            "description",
            "file",
            123,  # line
            456  # column
        )

        results = self.get_json_results()
        eq_(len(results["messages"]), 1, "Unexpected number of messages.")

        message = results["messages"][0]
        eq_(message["id"], ["id"])
        eq_(message["message"], "error")
        eq_(message["description"], "description")
        eq_(message["file"], "file")
        eq_(message["line"], 123)
        eq_(message["column"], 456)

    def test_json(self):
        """Test the JSON output capability of the error bundler."""

        self.err.set_tier(4)
        self.err.set_tier(3)

        self.err.error((), "error", "description")
        self.err.warning((), "warning", "description")
        self.err.notice((), "notice", "description")

        results = self.get_json_results()

        eq_(len(results["messages"]), 3)
        assert not results["success"]
        eq_(results["ending_tier"], 4)

    @patch("sys.stdout", StringIO())
    def test_boring(self):
        """Test that boring output strips out color sequences."""

        self.err.error((), "<<BLUE>><<GREEN>><<YELLOW>>")
        self.err.print_summary(no_color=True)
        eq_(sys.stdout.getvalue().count("<<GREEN>>"), 0)

    def test_file_structure(self):
        """
        Test the means by which file names and line numbers are stored in
        errors, warnings, and notices.
        """

        # Populate the bundle with some test data.
        self.err.error((), "error", "", "file1", 123)
        self.err.error((), "error", "", "file2")

        self.err.warning((), "warning", "", "file4", 123)
        self.err.warning((), "warning", "", "file5")
        self.err.warning((), "warning")

        # Load the JSON output as an object.
        output = self.get_json_results()

        # Do the same for friendly output
        output2 = self.err.print_summary(verbose=False)

        # Do the same for verbose friendly output
        output3 = self.err.print_summary(verbose=True)

        # Run some basic tests
        eq_(len(output["messages"]), 5)
        assert len(output2) < len(output3)

        messages = ["file1", "file2", "", "file4", "file5"]

        for message in output["messages"]:
            assert message["file"] in messages
            messages.remove(message["file"])

            if isinstance(message["file"], list):
                pattern = message["file"][:]
                pattern.pop()
                pattern.append("")
                file_merge = " > ".join(pattern)
                assert output3.count(file_merge)
            else:
                assert output3.count(message["file"])

        assert not messages

    def test_notice(self):
        """Test notice-related functions of the error bundler."""

        self.err.notice((), "")

        # Load the JSON output as an object.
        output = json.loads(self.err.render_json())

        # Run some basic tests
        eq_(len(output["messages"]), 1)

        assert any(m["type"] == "notice" for m in output["messages"]), (
            "Notices were not found.")

        assert not self.err.failed()
        assert not self.err.failed(True)

    def test_notice_friendly(self):
        """
        Test notice-related human-friendly text output functions of the error
        bundler.
        """

        self.err.notice((), "foobar")

        output = self.err.print_summary(verbose=True, no_color=True)
        assert output.count("foobar")

    def test_initializer(self):
        """Test that the __init__ paramaters are doing their jobs."""

        e = ErrorBundle()
        assert e.determined
        assert e.get_resource("listed")

        e = ErrorBundle(determined=False)
        assert not e.determined
        assert e.get_resource("listed")

        e = ErrorBundle(listed=False)
        assert e.determined
        assert not e.get_resource("listed")

    def test_json_constructs(self):
        """This tests some of the internal JSON stuff so we don't break zamboni."""

        self.err.warning((), "Context test",
                         context=ContextGenerator("x\ny\nz\n"),
                         line=2, column=0)
        self.err.notice((), "none")
        self.err.notice((), "line", line=1)
        self.err.notice((), "column", column=0)
        self.err.notice((), "line column", line=1, column=1)

        j = self.get_json_results()

        assert "messages" in j
        assert all(m["context"] == ["x", "y", "z"] for m in j["messages"] if
                   m["type"] == "warning"), "Warning had wrong context."

        for m in (m for m in j["messages"] if m["type"] == "notice"):
            if "line" in m["message"]:
                assert m["line"] is not None
                assert isinstance(m["line"], int)
                assert m["line"] > 0
            else:
                assert m["line"] is None

            if "column" in m["message"]:
                assert m["column"] is not None
                assert isinstance(m["column"], int)
                assert m["column"] > -1
            else:
                assert m["column"] is None
