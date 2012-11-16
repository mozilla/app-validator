import json
import sys
from StringIO import StringIO

from mock import patch
from nose.tools import eq_

from helper import TestCase

from appvalidator.errorbundle import ErrorBundle
from appvalidator.contextgenerator import ContextGenerator


class TestErrorBundle(TestCase):
    pass


def test_message_completeness():
    """Test we're fully expecting all of the values for a message."""

    bundle = ErrorBundle()

    bundle.error(
        ("id", ),
        "error",
        "description",
        "file",
        123,  # line
        456  # column
    )

    results = json.loads(bundle.render_json())
    eq_(len(results["messages"]), 1, "Unexpected number of messages.")

    message = results["messages"][0]
    eq_(message["id"], ["id"])
    eq_(message["message"], "error")
    eq_(message["description"], "description")
    eq_(message["file"], "file")
    eq_(message["line"], 123)
    eq_(message["column"], 456)


def test_json():
    """Test the JSON output capability of the error bundler."""

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle() # No color since no output
    bundle.set_tier(4)
    bundle.set_tier(3)

    bundle.error((), "error", "description")
    bundle.warning((), "warning", "description")
    bundle.notice((), "notice", "description")

    results = json.loads(bundle.render_json())

    eq_(len(results["messages"]), 3)
    assert not results["success"]
    eq_(results["ending_tier"], 4)


@patch("sys.stdout", StringIO())
def test_boring():
    """Test that boring output strips out color sequences."""

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()
    bundle.error((), "<<BLUE>><<GREEN>><<YELLOW>>")
    bundle.print_summary(no_color=True)

    sys.stdout.seek(0)
    eq_(sys.stdout.getvalue().count("<<GREEN>>"), 0)


def test_file_structure():
    """
    Test the means by which file names and line numbers are stored in errors,
    warnings, and messages.
    """

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()

    # Populate the bundle with some test data.
    bundle.error((), "error", "", "file1", 123)
    bundle.error((), "error", "", "file2")

    bundle.warning((), "warning", "", "file4", 123)
    bundle.warning((), "warning", "", "file5")
    bundle.warning((), "warning")

    # Load the JSON output as an object.
    output = json.loads(bundle.render_json())

    # Do the same for friendly output
    output2 = bundle.print_summary(verbose=False)

    # Do the same for verbose friendly output
    output3 = bundle.print_summary(verbose=True)

    # Run some basic tests
    eq_(len(output["messages"]), 5)
    assert len(output2) < len(output3)

    messages = ["file1", "file2", "", "file4", "file5"]

    for message in output["messages"]:
        print message

        assert message["file"] in messages
        messages.remove(message["file"])

        if isinstance(message["file"], list):
            pattern = message["file"][:]
            pattern.pop()
            pattern.append("")
            file_merge = " > ".join(pattern)
            print file_merge
            assert output3.count(file_merge)
        else:
            assert output3.count(message["file"])

    assert not messages


def test_notice():
    """Test notice-related functions of the error bundler."""

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()

    bundle.notice((), "")

    # Load the JSON output as an object.
    output = json.loads(bundle.render_json())

    # Run some basic tests
    assert len(output["messages"]) == 1

    print output

    has_ = False

    for message in output["messages"]:
        print message

        if message["type"] == "notice":
            has_ = True

    assert has_
    assert not bundle.failed()
    assert not bundle.failed(True)


def test_notice_friendly():
    """
    Test notice-related human-friendly text output functions of the error
    bundler.
    """

    # Use the StringIO as an output buffer.
    bundle = ErrorBundle()

    bundle.notice((), "foobar")

    # Load the JSON output as an object.
    output = bundle.print_summary(verbose=True, no_color=True)
    print output

    assert output.count("foobar")


def test_initializer():
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


def test_json_constructs():
    """This tests some of the internal JSON stuff so we don't break zamboni."""

    e = ErrorBundle()
    e.error(("a", "b", "c"), "Test")
    e.error(("a", "b", "foo"), "Test")
    e.error(("a", "foo", "c"), "Test")
    e.error(("a", "foo", "c"), "Test")
    e.error(("b", "foo", "bar"), "Test")
    e.warning((), "Context test",
              context=ContextGenerator("x\ny\nz\n"),
              line=2, column=0)
    e.notice((), "none")
    e.notice((), "line", line=1)
    e.notice((), "column", column=0)
    e.notice((), "line column", line=1, column=1)

    results = e.render_json()
    print results
    j = json.loads(results)

    assert "messages" in j
    for m in j["messages"]:
        if m["type"] == "warning":
            assert m["context"] == ["x", "y", "z"]

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
