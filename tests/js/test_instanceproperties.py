from mock import patch

from js_helper import TestCase


def _mock_html_error(self, *args, **kwargs):
    self.err.error(("foo", "bar"), "Does not pass validation.")


class TestHTML(TestCase):

    def test_innerHTML(self):
        """Tests that the dev can't define event handlers in innerHTML."""

        def test(self, declaration, script, fails):
            self.setUp()
            self.run_script(("var x = foo();" if declaration else "") +
                             "x.innerHTML = %s;" % script)
            if fails:
                self.assert_failed()
            else:
                self.assert_silent()

        for decl in (True, False, ):
            yield test, self, decl, '"<div></div>"', False
            yield test, self, decl, '"<div onclick=\\"foo\\"></div>"', True
            yield test, self, decl, '<a href="javascript:alert();">', True
            yield test, self, decl, '"<script>"', True

    def test_outerHTML(self):
        """Test that the dev can't define event handler in outerHTML."""

        def test(self, declaration, script, fails):
            self.setUp()
            self.run_script(("var x = foo();" if declaration else "") +
                             "x.outerHTML = %s;" % script)
            if fails:
                self.assert_failed()
            else:
                self.assert_silent()

        for decl in (True, False, ):
            yield test, self, decl, '"<div></div>"', False
            yield test, self, decl, '"<div onclick=\\"foo\\"></div>"', True

    @patch("appvalidator.testcases.markup.markuptester.MarkupParser.process",
           _mock_html_error)
    def test_complex_innerHTML(self):
        """
        Tests that innerHTML can't be assigned an HTML chunk with bad code.
        """

        self.run_script("""
        var x = foo();
        x.innerHTML = "<b></b>";
        """)
        self.assert_failed(with_errors=True)

    def test_function_return(self):
        """
        Test that the return value of a function is considered a dynamic value.
        """

        self.run_script("""
        x.innerHTML = foo();
        """)
        self.assert_silent()


class TestOnProperties(TestCase):

    def test_on_event(self):
        """Tests that on* properties are not assigned strings."""

        def test(self, declaration, script, prefix, fails):
            self.setUp()
            self.run_script(("var x = foo();" if declaration else "") +
                             "x.%s = %s;" % (script, prefix))
            if fails:
                self.assert_failed()
            else:
                self.assert_silent()

        for decl in (True, False, ):
            yield test, self, decl, 'fooclick', '"bar"', False
            yield test, self, decl, 'onclick', 'function() {}', False
            yield test, self, decl, 'onclick', '"bar"', True

    def test_on_event_null(self):
        """Null should not trigger on* events."""

        self.run_script("""
        var x = foo(),
            y = null;
        x.onclick = y;
        """)
        self.assert_silent()
