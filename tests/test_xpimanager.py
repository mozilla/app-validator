# -*- coding: utf8 -*-
import os
import tempfile

from nose.tools import eq_, raises

from helper import TestCase

from appvalidator.zip import ZipPackage

RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resources')


def get_path(fn):
    return os.path.join(RESOURCES_PATH, fn)


class TestZipManager(TestCase):
    def setUp(self):
        self.z = ZipPackage(get_path('xpi/install_rdf_only.xpi'))
        super(TestZipManager, self).setUp()

    def test_open(self):
        """Test that the manager will open the package."""
        assert self.z is not None

    def test_get_list(self):
        """Test that the manager can read the file listing."""
        assert not self.z.contents_cache
        assert self.z.package_contents()
        assert self.z.contents_cache  # Spelling check!
        self.z.contents_cache = 'foo'
        eq_(self.z.package_contents(), 'foo')

    def test_get_list_broken_fail(self):
        """
        Test that the manager will generate a new package listing when broken
        files have been detecetd.
        """
        assert not self.z.contents_cache
        assert self.z.package_contents()
        assert self.z.contents_cache  # Spelling check!
        self.z.broken_files.add("foo")
        self.z.contents_cache = "foo"
        assert self.z.package_contents() != "foo"

    def test_valid_name(self):
        "Test that the manager can retrieve the correct file name."
        assert 'install.rdf' in self.z.package_contents()

    def test_read_file(self):
        """Test that a file can be read from the package."""
        assert self.z.read('install.rdf') is not None


class TestWriteZip(TestCase):
    def test_write_file(self):
        """Test that a file can be written in UTF-8 to the package."""
        with tempfile.NamedTemporaryFile(delete=False) as t:
            temp_fn = t.name
            try:
                z = ZipPackage(temp_fn, mode='w')
                f, d = 'install.rdf', '注目のコレクション'.decode('utf-8')
                z.write(f, d)
                eq_(z.read(f), d.encode('utf-8'))
            finally:
                os.unlink(temp_fn)


class TestBadZipFile(TestCase):
    @raises(IOError)
    def test_missing_file(self):
        """Tests that the XPI manager correctly reports a missing XPI file."""
        ZipPackage("foo.bar")

    def test_corrupt_zip(self):
        """Tests that the XPI manager correctly reports a missing XPI file."""
        x = ZipPackage(get_path("corrupt.xpi"))
        try:
            x.read("install.rdf")
        except Exception:
            pass
        else:
            raise "Exception should have been raised on corrupt file access."

        assert "install.rdf" in x.broken_files
