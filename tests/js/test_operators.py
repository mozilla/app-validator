from nose.tools import eq_

from js_helper import TestCase


class TestMath(TestCase):

    def test_basic_math(self):
        "Tests that contexts work and that basic math is executed properly"

        self.run_script("""
        var x = 1;
        var y = 2;
        var z = x + y;

        var dbz = 1;
        var dbz1 = 1;
        dbz = dbz / 0;
        dbz1 = dbz1 % 0;

        var dbz2 = 1;
        var dbz3 = 1;
        dbz2 /= 0;
        dbz3 %= 0;

        var a = 2 + 3;
        var b = a - 1;
        var c = b * 2;
        """)
        self.assert_silent()

        self.assert_var_eq("x", 1)
        self.assert_var_eq("y", 2)
        self.assert_var_eq("z", 3)

        self.assert_var_eq("dbz", 0)  # Spidermonkey does this.
        self.assert_var_eq("dbz1", 0)  # ...and this.
        self.assert_var_eq("dbz2", 0)
        self.assert_var_eq("dbz3", 0)

        self.assert_var_eq("a", 5)
        self.assert_var_eq("b", 4)
        self.assert_var_eq("c", 8)

    def test_in_operator(self):
        "Tests the 'in' operator."

        self.run_script("""
        var list = ["a",1,2,3,"foo"];
        var dict = {"abc":123, "foo":"bar"};

        // Must be true
        var x = 0 in list;
        var y = "abc" in dict;

        // Must be false
        var a = 5 in list;
        var b = "asdf" in dict;
        """)
        self.assert_silent()

        self.assert_var_eq("x", True)
        self.assert_var_eq("y", True)
        self.assert_var_eq("a", False)
        self.assert_var_eq("b", False)

    def test_function_instanceof(self):
        self.run_script("""
        var x = foo();
        print(x instanceof Function);
        """)
        self.assert_silent()

    def test_unary_typeof(self):
        """Test that the typeof operator does good."""

        self.run_script("""
        var a = typeof void 0,
            b = typeof null,
            c = typeof true,
            d = typeof false,
            e = typeof new Boolean(),
            f = typeof new Boolean(true),
            g = typeof Boolean(),
            h = typeof Boolean(false),
            i = typeof Boolean(true),
            j = typeof NaN,
            k = typeof Infinity,
            l = typeof -Infinity,
            m = typeof Math.PI,
            n = typeof 0,
            o = typeof 1,
            p = typeof -1,
            q = typeof '0',
            r = typeof Number(),
            s = typeof Number(0),
            t = typeof new Number(),
            u = typeof new Number(0),
            v = typeof new Number(1),
            x = typeof function() {},
            y = typeof Math.abs;
        """)
        self.assert_var_eq("a", "undefined")
        self.assert_var_eq("b", "object")
        self.assert_var_eq("c", "boolean")
        self.assert_var_eq("d", "boolean")
        self.assert_var_eq("e", "object")
        self.assert_var_eq("f", "object")
        self.assert_var_eq("g", "boolean")
        self.assert_var_eq("h", "boolean")
        self.assert_var_eq("i", "boolean")
        # TODO: Implement "typeof" for predefined entities
        # self.assert_var_eq("j", "number")
        # self.assert_var_eq("k", "number")
        # self.assert_var_eq("l", "number")
        self.assert_var_eq("m", "number")
        self.assert_var_eq("n", "number")
        self.assert_var_eq("o", "number")
        self.assert_var_eq("p", "number")
        self.assert_var_eq("q", "string")
        self.assert_var_eq("r", "number")
        self.assert_var_eq("s", "number")
        self.assert_var_eq("t", "object")
        self.assert_var_eq("u", "object")
        self.assert_var_eq("v", "object")
        self.assert_var_eq("x", "function")
        self.assert_var_eq("y", "function")

    # TODO(basta): Still working on the delete operator...should be done soon.

    #def test_delete_operator(self):
    #    """Test that the delete operator works correctly."""
    #
    #    # Test that array elements can be destroyed.
    #    eq_(_get_var(_do_test_raw("""
    #    var x = [1, 2, 3];
    #    delete(x[2]);
    #    var value = x.length;
    #    """), "value"), 2)
    #
    #    # Test that hte right array elements are destroyed.
    #    eq_(_get_var(_do_test_raw("""
    #    var x = [1, 2, 3];
    #    delete(x[2]);
    #    var value = x.toString();
    #    """), "value"), "1,2")
    #
    #    eq_(_get_var(_do_test_raw("""
    #    var x = "asdf";
    #    delete x;
    #    var value = x;
    #    """), "value"), None)
    #
    #    assert _do_test_raw("""
    #    delete(Math.PI);
    #    """).failed()

    def test_logical_not(self):
        """Test that logical not is evaluated properly."""

        self.run_script("""
        var a = !(null),
            // b = !(var x),
            c = !(void 0),
            d = !(false),
            e = !(true),
            // f = !(),
            g = !(0),
            h = !(-0),
            i = !(NaN),
            j = !(Infinity),
            k = !(-Infinity),
            l = !(Math.PI),
            m = !(1),
            n = !(-1),
            o = !(''),
            p = !('\\t'),
            q = !('0'),
            r = !('string'),
            s = !(new String('')); // This should cover all type globals.
        """)
        self.assert_var_eq("a", True)
        # self.assert_var_eq("b", True)
        self.assert_var_eq("c", True)
        self.assert_var_eq("d", True)
        self.assert_var_eq("e", False)
        # self.assert_var_eq("f", True)
        self.assert_var_eq("g", True)
        self.assert_var_eq("h", True)
        # self.assert_var_eq("i", True)
        self.assert_var_eq("j", False)
        self.assert_var_eq("k", False)
        self.assert_var_eq("l", False)
        self.assert_var_eq("m", False)
        self.assert_var_eq("n", False)
        self.assert_var_eq("o", True)
        self.assert_var_eq("p", False)
        self.assert_var_eq("q", False)
        self.assert_var_eq("r", False)
        self.assert_var_eq("s", False)

    def test_concat_plus_infinity(self):
        """Test that Infinity is concatenated properly."""

        self.run_script("""
        var a = Infinity + "foo",
            b = (-Infinity) + "foo",
            c = "foo" + Infinity,
            d = "foo" + (-Infinity);
        """)
        self.assert_var_eq("a", "Infinityfoo")
        self.assert_var_eq("b", "-Infinityfoo")
        self.assert_var_eq("c", "fooInfinity")
        self.assert_var_eq("d", "foo-Infinity")

    def test_simple_operators_when_dirty(self):
        """
        Test that when we're dealing with dirty objects, binary operations don't
        cave in the roof.

        Note that this test (if it fails) may cause some ugly crashes.
        """

        self.run_script("""
        var x = foo();  // x is now a dirty object.
        y = foo();  // y is now a dirty object as well.
        """ +
        """y += y + x;""" * 100)  # This bit makes the validator's head explode.

    def test_wrapped_python_exceptions(self):
        """
        Test that OverflowErrors in traversal don't crash the validation
        process.
        """

        self.run_script("""
        var x = Math.exp(-4*1000000*-0.0641515994108);
        """)
