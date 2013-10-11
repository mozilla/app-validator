import appvalidator.testcases.javascript.jstypes as jstypes
from js_helper import TestCase


def test_jsarray_output():
    """Test that the output function for JSArray doesn't bork."""

    ja = jstypes.JSArray()
    ja.elements = [None, None]
    ja.output()  # Used to throw tracebacks.
    ja.get_literal_value()  # Also used to throw tracebacks.


def test_jsobject_output():
    """Test that the output function for JSObject doesn't bork."""

    jso = jstypes.JSObject()
    jso.data = {"first": None}
    jso.output()  # Used to throw tracebacks


def test_jsobject_recursion():
    """Test that circular references don't cause recursion errors."""

    jso = jstypes.JSObject()
    jso2 = jstypes.JSObject()

    jso.data = {"first": jso2}
    jso2.data = {"second": jso}

    print jso.output()
    assert "(recursion)" in jso.output()


def test_jsarray_recursion():
    """Test that circular references don't cause recursion errors."""

    ja = jstypes.JSArray()
    ja2 = jstypes.JSArray()

    ja.elements = [ja2]
    ja2.elements = [ja]

    print ja.output()
    assert "(recursion)" in ja.output()

    print ja.get_literal_value()
    assert "(recursion)" in ja.get_literal_value()


class TestTracebacks(TestCase):
    """Run all the things that use to make stuff crash."""

    def test_jsliteral_regex(self):
        """
        Test that there aren't tracebacks from JSLiterals that perform raw binary
        operations.
        """
        self.run_script("""
        var x = /foo/gi;
        var y = x + " ";
        var z = /bar/i + 0;
        """)
        self.assert_silent()


    def test_jsarray_contsructor(self):
        """
        Test for tracebacks that were caused by JSArray not calling it's parent's
        constructor.
        """
        self.run_script("""
        var x = [];
        x.foo = "bar";
        x["zap"] = "foo";
        baz("zap" in x);
        """)
        self.assert_silent()

    def test_jsobject_set_get(self):
        """
        Test that values fetched from a JSObject are the correct types.
        """
        jso = jstypes.JSObject()
        jso.set('foo', jstypes.JSLiteral(123))
        assert isinstance(jso.get(None, 'foo'), jstypes.JSLiteral)
        assert isinstance(jso.get(None, 'prototype'), jstypes.JSObject)
