from nose.tools import eq_

import appvalidator.testcases.markup.markuptester as markuptester

from ..helper import TestCase
from js_helper import TestCase as JSTestCase


class TestCSPTags(TestCase):

    def analyze(self, snippet, app_type="web"):
        self.setup_err()
        self.err.save_resource("app_type", app_type)
        markuptester.MarkupParser(self.err, debug=True).process("", snippet)

    def test_script_not_js(self):
        markup = """
        <script type="text/x-jquery-tmpl">foo</script>
        """

        self.analyze(markup)
        self.assert_silent()

        self.analyze(markup, "privileged")
        self.assert_silent()

    def test_script(self):
        markup = """<script>foo</script>"""

        self.analyze(markup)
        self.assert_failed(with_warnings=True)

        self.analyze(markup, "privileged")
        self.assert_failed(with_errors=True)

    def test_script_attrs(self):
        markup = """<button onclick="foo();"></button>"""

        self.analyze(markup)
        self.assert_failed(with_warnings=True)

        self.analyze(markup, "privileged")
        self.assert_failed(with_errors=True)

    def test_script_remote(self):
        markup = """<script src="http://foo.bar/zip.js"></script>"""

        self.analyze(markup)
        self.assert_failed(with_warnings=True)

        self.analyze(markup, "privileged")
        self.assert_failed(with_errors=True)


class TestCSP(JSTestCase):

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

    def test_timeouts_less_noisy(self):
        self.run_script("var f = function() {};x = setInterval(f, 0);")
        self.run_script("var f = function() {};x = setTimeout(f, 0);")
        self.assert_silent()


class TestCreateElement(JSTestCase):

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

    def test_createElement_var_pass(self):
        self.run_script("var a = 'asdf', x = document.createElement(a);")
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
