from js_helper import TestCase


class TestDoubleEscape(TestCase):

    def test_double_escaped(self):
        """Test that escaped characters don't result in errors."""

        self.run_script("""
        var x = "\u1234\x12"
        var y = "\\u1234\\x12"
        """)
        self.assert_silent()
