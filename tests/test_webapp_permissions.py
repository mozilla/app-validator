from nose.tools import eq_

from helper import TestCase
import appvalidator.testcases.webappbase as appbase


CERT_PERM = "cellbroadcast"
PRIV_PERM = "tcp-socket"
WEB_PERM = "fmradio"
PRE_PERM = "moz-attention"


class TestWebappPermissions(TestCase):
    """Test that apps can't request permissions that are unavailable to them.

    """

    def setUp(self):
        super(TestWebappPermissions, self).setUp()

        self.manifest = {"permissions": {}}

        self.setup_err()
        self.err.save_resource("manifest", self.manifest)

    def analyze(self):
        self.err.save_resource(
            "permissions", self.manifest.get("permissions", {}).keys())
        self.err.save_resource(
            "app_type", self.manifest.get("type", "web"))
        appbase.test_permissions(self.err, None)

    def test_no_perms(self):
        self.analyze()
        self.assert_silent()

    def test_certified_perms(self):
        self.manifest["permissions"][CERT_PERM] = True
        self.manifest["type"] = "certified"
        self.analyze()
        self.assert_silent()
        eq_(self.err.get_resource("app_type"), "certified")

    def test_certified_perms_priv(self):
        self.manifest["permissions"][CERT_PERM] = True
        self.manifest["type"] = "privileged"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_certified_perms_web(self):
        self.manifest["permissions"][CERT_PERM] = True
        self.manifest["type"] = "web"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_certified_perms_web_implicit(self):
        self.manifest["permissions"][CERT_PERM] = True
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_privileged_perms(self):
        self.manifest["permissions"][PRIV_PERM] = True
        self.manifest["type"] = "privileged"
        self.analyze()
        self.assert_silent()
        eq_(self.err.get_resource("app_type"), "privileged")

    def test_privileged_perms_cert(self):
        self.manifest["permissions"][PRIV_PERM] = True
        self.manifest["type"] = "certified"
        self.analyze()
        self.assert_silent()

    def test_privileged_perms_web(self):
        self.manifest["permissions"][PRIV_PERM] = True
        self.manifest["type"] = "web"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_privileged_perms_web_implicit(self):
        self.manifest["permissions"][PRIV_PERM] = True
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_web_perms_cert(self):
        self.manifest["permissions"][WEB_PERM] = True
        self.manifest["type"] = "certified"
        self.analyze()
        self.assert_silent()

    def test_web_perms_priv(self):
        self.manifest["permissions"][WEB_PERM] = True
        self.manifest["type"] = "privileged"
        self.analyze()
        self.assert_silent()

    def test_web_perms_web(self):
        self.manifest["permissions"][WEB_PERM] = True
        self.manifest["type"] = "web"
        self.analyze()
        self.assert_silent()
        eq_(self.err.get_resource("app_type"), "web")

    def test_web_perms_web_implicit(self):
        self.manifest["permissions"][WEB_PERM] = True
        self.analyze()
        self.assert_silent()
        eq_(self.err.get_resource("app_type"), "web")

    def test_prerelease_perms_web(self):
        self.manifest["permissions"][PRE_PERM] = True
        self.manifest["type"] = "web"
        self.analyze()
        self.assert_failed(with_errors=True)

    def test_prerelease_perms_priv(self):
        self.manifest["permissions"][PRE_PERM] = True
        self.manifest["type"] = "privileged"
        self.analyze()
        self.assert_failed(with_errors=False)

    def test_prerelease_perms_cert(self):
        self.manifest["permissions"][PRE_PERM] = True
        self.manifest["type"] = "certified"
        self.analyze()
        self.assert_silent()
