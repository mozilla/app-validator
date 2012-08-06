from nose.tools import eq_

from helper import TestCase

from appvalidator.contextgenerator import ContextGenerator


class TestContextGenerator(TestCase):

    def test_load_data(self):
        """Test that data is loaded properly into the CG."""

        d = """abc
        def
        ghi"""
        c = ContextGenerator(d)
        eq_(len(c.data), 3)

        # Through inductive reasoning, we can assert that every other line
        # is imported properly.
        eq_(c.data[0].strip(), "abc")
        eq_(c.data[1].strip(), "def")

    def test_get_context(self):
        """Test that contexts are generated properly."""

        d = open("tests/resources/contextgenerator/data.txt").read()
        c = ContextGenerator(d)

        c_start = c.get_context(line=1, column=0)
        c_end = c.get_context(line=11, column=0)

        # Contexts are always length 3
        eq_(len(c_start), 3)
        eq_(c_start[0], None)
        eq_(len(c_end), 3)
        eq_(c_end[2], None)

        eq_(c_start[1], "0123456789")
        eq_(c_end[0], "9012345678")
        eq_(c_end[1], "")

        c_mid = c.get_context(line=5)
        eq_(len(c_mid), 3)
        eq_(c_mid[0], "3456789012")
        eq_(c_mid[2], "5678901234")

    def test_get_context_trimming(self):
        """
        Test that contexts are generated properly when lines are >140
        characters.
        """

        d = open("tests/resources/contextgenerator/longdata.txt").read()
        c = ContextGenerator(d)

        trimmed = c.get_context(line=2, column=89)
        proper_lengths = (140, 148, 140)

        for i, length in enumerate([140, 148, 140]):
            eq_(len(trimmed[i]), length)

    def test_get_context_trimming_inverse(self):
        """
        Tests that surrounding lines are trimmed properly; the error line is
        ignored if it is less than 140 characters.
        """

        d = open("tests/resources/contextgenerator/longdata.txt").read()
        c = ContextGenerator(d)

        trimmed = c.get_context(line=6, column=0)

        eq_(trimmed[1], "This line should be entirely visible.")
        assert trimmed[0][0] != "X"
        assert trimmed[2][-1] != "X"

    def test_get_line(self):
        """Test that the context generator returns the proper line."""

        d = open("tests/resources/contextgenerator/data.txt").read()
        c = ContextGenerator(d)

        eq_(c.get_line(30), 3)
        eq_(c.get_line(11), 2)
        eq_(c.get_line(10000), 11)

    def test_leading_whitespace(self):
        """Test that leading whitespace is trimmed properly."""

        def run(data, expectation, line=2):
            # Strip blank lines.
            data = '\n'.join(filter(None, data.split('\n')))
            # Get the context and assert its equality.
            c = ContextGenerator(data)
            eq_(c.get_context(line), expectation)

        run(' One space\n'
            '  Two spaces\n'
            '   Three spaces',
            ('One space', ' Two spaces', '  Three spaces'))
        run('\n  \n   ',
            ('', '', ''))
        run('  Two\n'
            ' One\n'
            '   Three',
            (' Two', 'One', '  Three'))
        run('None\n'
            ' One\n'
            ' One',
            ('None', ' One', ' One'))
