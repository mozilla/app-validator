from nose.tools import eq_

from js_helper import TestCase
from test_features import uses_feature


class TestXHR(TestCase):

    def test_synchronous_xhr(self):
        "Tests that syncrhonous AJAX requests are marked as dangerous"

        self.run_script("""
        var x = new XMLHttpRequest();
        x.open("GET", "http://foo/bar", true);
        x.send(null);
        """)
        self.assert_silent()

    def test_async_xhr(self):
        self.run_script("""
        var x = new XMLHttpRequest();
        x.open("GET", "http://foo/bar", false);
        x.send(null);
        """)
        self.assert_failed()

    @uses_feature("SYSTEMXHR")
    def test_moz_system(self):
        self.run_script("""
        var x = new XMLHttpRequest({mozSystem: true});
        """)
        self.assert_silent();

    @uses_feature("SYSTEMXHR")
    def test_moz_system_sync(self):
        self.run_script("""
        var x = new XMLHttpRequest({mozSystem: true});
        x.open("GET", "http://foo/bar", false);
        x.send(null);
        """)
        self.assert_failed();


class TestScope(TestCase):

    def test_extraneous_globals(self):
        """Globals should not be registered from function parameters."""

        self.run_script("""
        var f = function(foo, bar) {
            foo = "asdf";
            bar = 123;
        };
        """)
        self.assert_silent()

        assert "foo" not in self.final_context.data
        assert "bar" not in self.final_context.data

    def do_expr(self, expr, output):
        self.setUp()
        self.run_script("var x = %s" % expr)
        self.assert_var_eq("x", output)

    def test_number_global_conversions(self):
        """Test that the Number global constructor functions properly."""

        yield self.do_expr, "Number()", 0
        yield self.do_expr, "Number(123)", 123
        yield self.do_expr, "Number(123.123)", 123.123
        yield self.do_expr, 'Number("123")', 123
        yield self.do_expr, 'Number("123.456")', 123.456
        yield self.do_expr, 'Number("foo") == window.NaN', True
        yield self.do_expr, "Number(null) == window.NaN", True
