from nose.tools import eq_

from js_helper import TestCase


class TestCreateElement(TestCase):

    def test_pass(self):
        "Tests that createElement and createElementNS throw errors."

        self.run_script("""
        var x = foo;
        foo.bar.whateverElement("script");
        """)
        self.assert_silent()

    def test_create_split(self):
        self.run_script("""
        var x = foo;
        foo.bar.createElement("scr"+"ipt");
        """)
        self.assert_failed(with_warnings=True)

    def test_create_case(self):
        # Part of bug 636835
        self.run_script("""
        var x = foo;
        foo.bar.createElement("scRipt");
        """)
        self.assert_failed(with_warnings=True)

    def test_create_ns(self):
        self.run_script("""
        var x = foo;
        foo.bar.createElementNS("http://foo.bar/", "asdf:" +"scr"+"ipt");
        """)
        self.assert_failed(with_warnings=True)

    def test_create_compiled(self):
        self.run_script("""
        let scr = "scr";
        scr += "ipt";
        foo.bar.createElement(scr);
        """)
        self.assert_failed(with_warnings=True)

    def test_create_other(self):
        self.run_script("""
        document.createElement("style");
        function x(doc) {
            doc.createElement("style");
        }""")
        self.assert_silent()

    def test_create_split_other(self):
        self.run_script("""
        document.createElement("sty"+"le");
        var x = "sty";
        x += "le";
        document.createElement(x);
        """)
        self.assert_silent()

    def test_create_noop(self):
        # Also test an empty call (tests for tracebacks)
        self.run_script("""
        document.createElement();
        """)


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


class TestLoadOverlay(TestCase):

    def test_empty(self):
        self.run_script("""document.loadOverlay();""")
        self.assert_failed()

    def test_name(self):
        self.run_script("""document.loadOverlay("foobar");""")
        self.assert_failed()

    def test_chrome(self):
        self.run_script("""document.loadOverlay("chrome:foo/bar/");""")
        self.assert_silent()

    def test_compiled_chrome(self):
        self.run_script("""document.loadOverlay("chr" + "ome:foo/bar/");""")
        self.assert_silent()

    def test_resource(self):
        self.run_script("""document.loadOverlay("resource:foo/bar/");""")
        self.assert_silent()


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
