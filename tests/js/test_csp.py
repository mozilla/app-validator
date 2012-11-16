from nose.tools import eq_

from js_helper import TestCase


class TestCSP(TestCase):

    def test_function(self):
        self.run_script("var x = Function('foo');")
        self.assert_failed(with_warnings=True)

    def test_function_new(self):
        self.run_script("var x = new Function('foo');")
        self.assert_failed(with_warnings=True)

    def test_eval(self):
        self.run_script("var x = eval('foo');")
        self.assert_failed(with_warnings=True)

    def test_setTimeout(self):
        self.run_script("var x = setTimeout('foo', 0);")
        self.assert_failed(with_warnings=True)

    def test_setTimeout_pass(self):
        self.run_script("var x = setTimeout(function() {}, 0);")
        self.assert_silent()

    def test_setInterval(self):
        self.run_script("var x = setInterval('foo', 0);")
        self.assert_failed(with_warnings=True)

    def test_setInterval_pass(self):
        self.run_script("var x = setInterval(function() {}, 0);")
        self.assert_silent()


class TestCreateElement(TestCase):

    def test_pass(self):
        "Tests that createElement and createElementNS throw errors."

        self.run_script("""
        var x = foo;
        foo.bar.whateverElement("script");
        """)
        self.assert_silent()

    def test_createElement_pass(self):
        self.run_script("var x = document.createElement('b');")
        self.assert_silent()

    def test_createElement(self):
        self.run_script("var x = document.createElement('script');")
        self.assert_failed(with_warnings=True)

    def test_createElementNS_pass(self):
        self.run_script("var x = document.createElementNS('ns', 'b');")
        self.assert_silent()

    def test_createElementNS(self):
        self.run_script("var x = document.createElementNS('ns', 'script');")
        self.assert_failed(with_warnings=True)

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
        self.run_script("document.createElement();")
