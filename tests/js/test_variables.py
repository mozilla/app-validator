from nose.tools import eq_

from js_helper import skip_on_acorn, TestCase


class TestAssignments(TestCase):

    def test_multiple_assignments(self):
        """Tests that multiple variables can be assigned in one sitting."""

        self.run_script("""
        var x = 1, y = 2, z = 3;
        """)
        self.assert_silent()
        self.assert_var_eq("x", 1)
        self.assert_var_eq("y", 2)
        self.assert_var_eq("z", 3)

    @skip_on_acorn
    def test_arraypattern_assignment(self):
        """Tests that array patterns can be used to assign variables."""

        self.run_script("""
        var [x, y, z] = [1, 2, 3];
        """)
        self.assert_silent()
        self.assert_var_eq("x", 1)
        self.assert_var_eq("y", 2)
        self.assert_var_eq("z", 3)

    @skip_on_acorn
    def test_objectpattern_assignment(self):
        """Tests that ObjectPatterns are respected."""

        self.run_script("""
        var foo = {a:3,b:4,c:5};
        var {a:x, b:y, c:z} = foo;
        """)
        self.assert_silent()
        self.assert_var_eq("x", 3)
        self.assert_var_eq("y", 4)
        self.assert_var_eq("z", 5)

    @skip_on_acorn
    def test_objectpattern_nested(self):
        """Test that nested ObjectPattern assignments are respected."""

        self.run_script("""
        var foo = {
            a:1,
            b:2,
            c:{
                d:4
            }
        };
        var {a:x, c:{d:y}} = foo;
        """)
        self.assert_silent()
        self.assert_var_eq("x", 1)
        self.assert_var_eq("y", 4)


class TestNestedAssignments(TestCase):

    def test_lazy_object_member_assgt(self):
        """
        Test that members of lazy objects can be assigned, even if the lazy
        object hasn't yet been created.
        """

        self.run_script("""
        foo.bar = "asdf";
        zap.fizz.buzz = 123;
        var a = foo.bar,
            b = zap.fizz.buzz;
        """)
        self.assert_silent()
        self.assert_var_eq("a", "asdf")
        self.assert_var_eq("b", 123)

    def test_prototype_array_instantiation(self):
        """
        Test that JSPrototypes and JSArrays handle deep instantiation properly.
        """

        self.run_script("""
        var x = {};
        x.prototype.foo.bar = "asdf";
        var y = [];
        y.a.b.c.d = 123;
        """)
        # Don't care about the output, just testing for tracebacks.

    def test_this_tracebacks(self):
        """Test to make sure `this` doesn't generate tracebacks."""

        self.run_script("""
        var x = this;
        """);
        # The output is irrelevant for now.
