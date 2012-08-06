from js_helper import TestCase


class TestBasicStrings(TestCase):
    """Test that strings and their related functions are handled properly."""

    def test_basic_concatenation(self):
        """
        Tests that contexts work and that basic concat ops are executed
        properly.
        """

        self.run_script("""
        var x = "foo";
        var y = "bar";
        var z = x + y; // foobar

        var a = "5";
        var b = "6";
        var c = a + b; // 56
        var d = b - a; // 1
        var e = b * a; // 30
        var f = "10" / "2"; // 5
        """)
        self.assert_silent()
        self.assert_var_eq("x", "foo")
        self.assert_var_eq("y", "bar")
        self.assert_var_eq("z", "foobar")
        self.assert_var_eq("a", "5")
        self.assert_var_eq("b", "6")
        self.assert_var_eq("c", "56")
        self.assert_var_eq("d", 1)
        self.assert_var_eq("e", 30)
        self.assert_var_eq("f", 5)

    def test_augconcat(self):
        """Tests augmented concatenation operators."""

        self.run_script("""
        var x = "foo";
        x += "bar";
        """)
        self.assert_silent()
        self.assert_var_eq("x", "foobar")

    def test_ref_augconcat(self):
        """
        Test that augmented concatenation happens even within referenced
        variable placeholders.
        """

        self.run_script("""
        var x = {"xyz":"foo"};
        x["xyz"] += "bar";
        var y = x.xyz;
        """)
        self.assert_silent()
        self.assert_var_eq("y", "foobar")

    def test_typecasting(self):
        """Tests that strings are treated as numbers when necessary."""

        self.run_script("""
        var x = "4" + 4; // "44"
        var y = "4" * 4; // 16
        """)
        self.assert_silent()
        self.assert_var_eq("x", "44")
        self.assert_var_eq("y", 16)
