# -*- coding: utf-8 -*-
from nose.tools import eq_

from test_errorbundler import ErrorBundleTestCase


class TestManifestMixin(ErrorBundleTestCase):

    def test_manifest(self):
        self.err.save_resource("manifest", {"foo": "bar"})

        results = self.get_json_results()
        assert "manifest" in results, results.keys()
        eq_(results["manifest"]["foo"], "bar")

    def test_manifest_unicode(self):
        self.err.save_resource("manifest", {"foo": u"bär"})

        results = self.get_json_results()
        assert "manifest" in results, results.keys()
        eq_(results["manifest"]["foo"], u"bär")

    def test_permissions(self):
        perms = ["alarms", "systemXHR"]
        self.err.save_resource("permissions", perms)

        results = self.get_json_results()
        assert "permissions" in results, results.keys()
        eq_(results["permissions"], perms)
