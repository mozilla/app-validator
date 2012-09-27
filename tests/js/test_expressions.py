from nose.tools import eq_

from js_helper import TestCase


class TestBinaryOperators(TestCase):
    """Test that all of the binary operators in JS work as expected."""

    def do_expr(self, expr, output):
        self.setUp()
        self.run_script("var x = %s" % expr)
        self.assert_var_eq("x", output)

    def test_boolean_comp(self):

        yield self.do_expr, "false < true", True
        yield self.do_expr, "true > false", True
        yield self.do_expr, "false > true", False
        yield self.do_expr, "true < false", False
        yield self.do_expr, "false < false", False
        yield self.do_expr, "true < true", False
        yield self.do_expr, "true == true", True
        yield self.do_expr, "false == false", True
        yield self.do_expr, "true > 0", True
        yield self.do_expr, "true == 1", True
        yield self.do_expr, "false < 1", True
        yield self.do_expr, "false == 0", True

    def test_string_comp(self):
        yield self.do_expr, '"string" < "string"', False
        yield self.do_expr, '"astring" < "string"', True
        yield self.do_expr, '"strings" < "stringy"', True
        yield self.do_expr, '"strings" < "stringier"', False
        yield self.do_expr, '"string" < "astring"', False
        yield self.do_expr, '"string" < "strings"', True

        # We can assume that the converses are true; Spidermonkey makes that
        # easy.

    def test_signed_zero_comp(self):
        yield self.do_expr, "false < true", True
        yield self.do_expr, "true > false", True
        yield self.do_expr, "false > true", False

    def test_signed_zero(self):
        yield self.do_expr, "0 == 0", True
        yield self.do_expr, "0 != 0", False
        yield self.do_expr, "0 == -0", True
        yield self.do_expr, "0 != -0", False
        yield self.do_expr, "-0 == 0", True
        yield self.do_expr, "-0 != 0", False

    def test_typecasting(self):
        yield self.do_expr, "1 == '1'", True
        yield self.do_expr, "255 == '0xff'", True
        yield self.do_expr, "0 == '\\r'", True

    def test_additive_typecasting(self):
        self.run_script("""
        var first = true,
            second = "foo",
            third = 345;
        var a = first + second,
            b = second + first,
            c = Boolean(true) + String("foo"),
            d = String("foo") + Boolean(false),
            e = second + third,
            f = String("foo") + Number(-100);
        """)
        self.assert_var_eq("a", "truefoo")
        self.assert_var_eq("b", "footrue")
        self.assert_var_eq("c", "truefoo")
        self.assert_var_eq("d", "foofalse")
        self.assert_var_eq("e", "foo345")
        self.assert_var_eq("f", "foo-100")

    def test_addition_expressions(self):
        self.run_script("""
        var a = true + false,
            b = Boolean(true) + Boolean(false);
        var x = 100,
            y = -1;
        var c = x + y,
            d = Number(x) + Number(y);
        """)
        self.assert_var_eq("a", 1)
        self.assert_var_eq("b", 1)
        self.assert_var_eq("c", 99)
        self.assert_var_eq("d", 99)
