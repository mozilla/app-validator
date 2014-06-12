import math

from js_helper import TestCase


INFINITY = float('inf')
NEG_INFINITY = float('-inf')


class TestMathFuncs(TestCase):

    def do_func(self, func):
        def wrap(params, output):
            expr = "Math.%s(%s)" % (func, params)
            print 'Testing `%s`' % expr
            self.do_expr(expr, output)
        return wrap

    def do_expr(self, expr, output):
        self.setUp()
        self.run_script("var x = %s" % expr)
        self.assert_var_eq("x", output)

    def test_abs(self):
        """Test that the abs() function works properly."""

        yield self.do_func("abs"), "-5", 5
        yield self.do_func("abs"), "5", 5
        yield self.do_func("abs"), "-Infinity", INFINITY

    def test_exp(self):
        """Test that the exp() function works properly."""

        yield self.do_func("exp"), "null", 1
        yield self.do_func("exp"), "false", 1
        yield self.do_expr, "Math.exp(1) == Math.E", True
        yield self.do_expr, "Math.exp('1') == Math.E", True
        yield self.do_func("exp"), "'0'", 1
        yield self.do_func("exp"), "0", 1
        yield self.do_func("exp"), "-0", 1
        yield self.do_expr, "Math.exp(Infinity) == Infinity", True
        yield self.do_expr, "Math.exp(-Infinity) == 0", True

    def test_ceil(self):
        """Test that the ceil() function works properly."""

        yield self.do_func("ceil"), "null", 0
        yield self.do_func("ceil"), "void 0", 0
        yield self.do_func("ceil"), "true", 1
        yield self.do_func("ceil"), "false", 0
        yield self.do_func("ceil"), "'1.1'", 2
        yield self.do_func("ceil"), "'-1.1'", -1
        yield self.do_func("ceil"), "'0.1'", 1
        yield self.do_func("ceil"), "'-0.1'", 0
        yield self.do_func("ceil"), "0", 0
        # "j": -0,
        yield self.do_expr, "Math.ceil(-0) == -Math.floor(0)", True
        yield self.do_func("ceil"), "Infinity", INFINITY
        yield (self.do_expr, "Math.ceil(Infinity) == -Math.floor(-Infinity)",
               True)
        yield self.do_func("ceil"), "-Infinity", NEG_INFINITY
        yield self.do_func("ceil"), "0.0000001", 1
        yield self.do_func("ceil"), "-0.0000001", 0

    def test_floor(self):
        """Test that the floor() function works properly."""

        yield self.do_func("floor"), "null", 0
        yield self.do_func("floor"), "void 0", 0
        yield self.do_func("floor"), "true", 1
        yield self.do_func("floor"), "false", 0
        yield self.do_func("floor"), "'1.1'", 1
        yield self.do_func("floor"), "'-1.1'", -2
        yield self.do_func("floor"), "'0.1'", 0
        yield self.do_func("floor"), "'-0.1'", -1
        yield self.do_func("floor"), "0", 0
        # "j": -0,
        yield self.do_expr, "Math.floor(-0) == -Math.ceil(0)", True
        yield self.do_func("floor"), "Infinity", INFINITY
        yield (self.do_expr, "Math.floor(Infinity) == -Math.ceil(-Infinity)",
               True)
        yield self.do_func("floor"), "-Infinity", NEG_INFINITY
        yield self.do_func("floor"), "0.0000001", 0
        yield self.do_func("floor"), "-0.0000001", -1

    def test_trig(self):
        """Test the trigonometric functions."""

        yield self.do_func("cos"), "0", 1
        yield self.do_func("cos"), "Math.PI", -1
        yield self.do_func("sin"), "0", 0
        yield self.do_func("sin"), "Math.PI", 0
        yield self.do_func("tan"), "0", 0
        yield self.do_func("tan"), "Math.PI / 4", 1

        yield self.do_func("acos"), "1", 0
        yield self.do_func("asin"), "0", 0
        yield self.do_func("atan"), "0", 0

        yield self.do_expr, "Math.acos(0) == Math.PI / 2", True
        yield self.do_expr, "Math.acos(-1) == Math.PI", True
        yield self.do_expr, "Math.asin(1) == Math.PI / 2", True
        yield self.do_expr, "Math.asin(-1) == Math.PI / -2", True
        yield self.do_expr, "Math.atan(1) == Math.PI / 4", True
        yield self.do_expr, "Math.atan(Infinity) == Math.PI / 2", True

        yield self.do_expr, "Math.atan2(1, 0) == Math.PI / 2", True
        yield self.do_func("atan2"), "0, 0", 0
        yield self.do_expr, "Math.atan2(0, -1) == Math.PI", True

    def test_sqrt(self):
        """Test that the sqrt() function works properly."""

        yield self.do_func("sqrt"), "10", round(math.sqrt(10), 5)
        yield self.do_func("sqrt"), "4", 2
        yield self.do_func("sqrt"), "3 * 3 + 4 * 4", 5

    def test_round(self):
        """Test that the round() function works properly."""

        yield self.do_func("round"), "'0.99999'", 1
        yield self.do_func("round"), "0", 0
        yield self.do_func("round"), "0.49", 0
        yield self.do_func("round"), "0.5", 1
        yield self.do_func("round"), "0.51", 1
        yield self.do_func("round"), "-0.49", 0
        yield self.do_func("round"), "-0.5", 0
        yield self.do_func("round"), "-0.51", -1
        yield self.do_expr, "Math.round(Infinity) == Infinity", True
        yield self.do_expr, "Math.round(-Infinity) == -Infinity", True

    def test_random(self):
        """Test that the random() function works "properly"."""

        yield self.do_func("random"), "", 0.5

    def test_pow(self):
        """Test that the pow() function works properly."""

        yield self.do_func("pow"), "true, false", 1
        yield self.do_func("pow"), "2, 32", 4294967296
        yield self.do_func("pow"), "1.0000001, Infinity", INFINITY
        yield self.do_func("pow"), "1.0000001, -Infinity", 0
        yield self.do_func("pow"), "123, 0", 1

    def test_log(self):
        """Test that the log() function works properly."""

        yield self.do_func("log"), "1", 0
        yield self.do_func("log"), "0", NEG_INFINITY
        yield self.do_func("log"), "Infinity", INFINITY
        yield self.do_func("log"), "-1", None

    def test_min_max(self):
        """Test that the min() and max() function works properly."""

        yield self.do_func("min"), "Infinity, -Infinity", NEG_INFINITY
        yield self.do_func("min"), "1, -1", -1
        yield self.do_func("max"), "Infinity, -Infinity", INFINITY
        yield self.do_func("max"), "1, -1", 1

    def test_math_infinity(self):
        """Test for known tracebacks regarding math."""

        self.run_script("""
        var x = Infinity;
        x >>= 10;
        var y = Infinity;
        var z = 10 >> y;
        """)

        # We really don't care about the output here.

    def test_bit_shifting(self):
        """Test for bit shifting operators."""
        self.setUp()
        self.run_script("""
            var x = 1;
            x >>= 0;""")
        self.assert_var_eq("x", 1)
        self.run_script("""
            var x = 1;
            x >>= 1""")
        self.assert_var_eq("x", 0)
        self.run_script("""
            var x = -1;
            x >>= 0;""")
        self.assert_var_eq("x", -1)
        self.run_script("""
            var x = -1;
            x >>>= 0.2""")
        self.assert_var_eq("x", 0xFFFFFFFF)
