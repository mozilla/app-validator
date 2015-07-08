from nose.tools import eq_

from js_helper import skip_on_acorn, TestCase


class TestProtoAssignment(TestCase):

    @skip_on_acorn
    def test__proto__asignment(self):
        """
        Make sure that setting __proto__ doesn't traceback.
        """

        self.setUp()
        self.run_script('''
            var obj = {foo: 'bar', __proto__: null};
        ''')
        self.assert_silent()
