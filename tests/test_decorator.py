from mock import patch
from nose.tools import eq_

import appvalidator.testcases as testcases


@patch("appvalidator.testcases.TEST_TIERS", {})
def test_tiers():
    """
    Tests to make sure that the decorator module is properly registering test
    functions.
    """
    testcases.register_test(tier=1)(lambda: None)
    testcases.register_test(tier=2)(lambda: None)
    testcases.register_test(tier=2, simple=True)(lambda: None)

    tiers = testcases._get_tiers()
    print tiers
    eq_(len(tiers), 2)
