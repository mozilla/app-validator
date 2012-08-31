from js_helper import _do_test_raw, TestCase


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
            yield test, self, decl, '"x" + y', True

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
            yield test, self, decl, '"x" + y', True

    def test_complex_innerHTML(self):
        """
        Tests that innerHTML can't be assigned an HTML chunk with bad code.
        """

        self.run_script("""
        var x = foo();
        x.innerHTML = "<script src=\\"http://foo.bar/\\"></script>";
        """)
        self.assert_failed(with_errors=True)


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

    def test_on_event_handleEvent_fail(self):
        """
        Objects with `handleEvent` methods should be flagged as errors when
        add-ons target Gecko version 18.
        """

        self.run_script("""
        foo.onclick = {handleEvent: function() {alert("bar");}};
        """)
        self.assert_failed(with_errors=True)
