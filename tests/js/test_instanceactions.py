from js_helper import TestCase


class TestCreateElement(TestCase):

    def test_createElement_pass(self):
        """Tests that createElement calls are filtered properly"""

        self.run_script("""
        var x = "foo";
        x.createElement();
        x.createElement("foo");
        """)
        self.assert_silent()

    def test_createElement_script(self):
        self.run_script("""
        var x = "foo";
        x.createElement("script");
        """)
        self.assert_failed()

    def test_createElement_variable(self):
        self.run_script("""
        var x = "foo";
        x.createElement(bar);
        """)
        self.assert_failed()


class TestCreateElementNS(TestCase):

    def test_createElementNS(self):
        """Tests that createElementNS calls are filtered properly"""

        self.run_script("""
        var x = "foo";
        x.createElementNS();
        x.createElementNS("foo");
        x.createElementNS("foo", "bar");
        """)
        self.assert_silent()

    def test_createElementNS_script(self):
        self.run_script("""
        var x = "foo";
        x.createElementNS("foo", "script");
        """)
        self.assert_failed()

    def test_createElementNS_script(self):
        self.run_script("""
        var x = "foo";
        x.createElementNS("foo", bar);
        """)
        self.assert_failed()


class TestSetAttribute(TestCase):

    def test_setAttribute(self):
        """Tests that setAttribute calls are blocked successfully"""

        self.run_script("""
        var x = "foo";
        x.setAttribute();
        x.setAttribute("foo");
        x.setAttribute("foo", "bar");
        """)
        self.assert_silent()

    def test_setAttribute_onevent(self):
        self.run_script("""
        var x = "foo";
        x.setAttribute("onfoo", "bar");
        """)
        self.assert_failed()


class TestCallExpression(TestCase):

    def test_callexpression_argument_traversal(self):
        """
        This makes sure that unknown function calls still have their arguments
        traversed.
        """

        self.run_script("""
        function foo(x){}
        foo({"bar":function(){
            bar();
        }});
        """)
        self.assert_silent()

    def test_callexpression_argument_evil(self):
        self.run_script("""
        function foo(x){}
        foo({"bar":function(){
            eval("evil");
        }});
        """)
        self.assert_failed()


class TestInsertAdjacentHTML(TestCase):

    def test_insertAdjacentHTML(self):
        """Test that insertAdjacentHTML works the same as innerHTML."""

        self.run_script("""
        var x = foo();
        x.insertAdjacentHTML("foo bar", "<div></div>");
        """)
        self.assert_silent()

    def test_insertAdjacentHTML_onevent_decl(self):
        self.run_script("""
        var x = foo();
        x.insertAdjacentHTML("foo bar", "<div onclick=\\"foo\\"></div>");
        """)
        self.assert_failed()

    def test_insertAdjacentHTML_onevent(self):
        # Test without declaration
        self.run_script("""
        x.insertAdjacentHTML("foo bar", "<div onclick=\\"foo\\"></div>");
        """)
        self.assert_failed()
