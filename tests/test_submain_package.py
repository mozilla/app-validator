from mock import patch
from nose.tools import eq_

from helper import TestCase

import appvalidator.submain as submain


class TestSubmainPackage(TestCase):
    @patch("appvalidator.submain.test_inner_package",
           lambda x, z: "success")
    def test_package_pass(self):
        "Tests the test_package function with simple data"

        self.setup_err()

        name = "tests/resources/submain/install_rdf.xpi"
        with open(name) as pack:
            result = submain.test_package(self.err, pack, name)

        self.assert_silent()
        eq_(result, "success")

    @patch("appvalidator.submain.test_inner_package",
           lambda x, z: "success")
    def test_package_corrupt(self):
        "Tests the test_package function fails with a non-zip"

        self.setup_err()

        name = "tests/resources/junk.xpi"
        with open(name) as pack:
            result = submain.test_package(self.err, pack, name)

        self.assert_failed()

    def test_package_corrupt(self):
        "Tests the test_package function fails with a corrupt file"

        self.setup_err()

        name = "tests/resources/corrupt.xpi"
        result = submain.test_package(self.err, name, name)

        self.assert_failed(with_errors=True, with_warnings=True)
