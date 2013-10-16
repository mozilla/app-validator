from js_helper import must_assert, errors, silent, TestCase


class TestScope(TestCase):
    """
    Test that various forms of scoping work as expected during the validation
    process. This should test that variables move both in and out of scope
    properly.
    """

    @silent
    @must_assert
    def test_local_scope(self):
        self.run_script("""
        x = false;
        while(1) {
            __assert(!x);
        }
        """)

    @errors()
    @must_assert
    def test_local_scope_lazy(self):
        self.run_script("""
        while(1) {
            __assert(!x);
        }
        """)

    @silent
    @must_assert
    def test_block_scope(self):
        self.run_script("""
        var x = false;
        while(1) {
            let x = true;
        }
        __assert(!x); // Should be a lazy object.
        """)

    @errors()
    @must_assert
    def test_block_scope_not_block(self):
        self.run_script("""
        var x = false;
        while(1) {
            x = true;
        }
        __assert(!x); // Should be a lazy object.
        """)

    @silent
    @must_assert
    def test_function_scope(self):
        self.run_script("""
        function foo() {
            var x = false;
            (function() {
                __assert(!x);
            })()
        }
        """)

    @silent
    @must_assert
    def test_function_scope_block(self):
        self.run_script("""
        function foo() {
            let x = false;
            (function() {
                __assert(!x);
            })()
        }
        """)

    @silent
    @must_assert
    def test_function_scope_recursive(self):
        self.run_script("""
        function foo() {
            __callable(foo);
        }
        """)

    @silent
    @must_assert
    def test_anonymous_function_scope_recursive(self):
        self.run_script("""
        foo = function() {
            __callable(foo);
        }
        """)
