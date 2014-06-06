# -*- coding: utf-8 -*-
import nose
import appvalidator.unicodehelper as unicodehelper


COMPARISON = u"täst"

def _do_test(path, result=COMPARISON, **kwargs):
    "Performs a test on a JS file"

    text = open(path).read()
    utext = unicodehelper.decode(text, **kwargs)

    print utext.encode("ascii", "backslashreplace")
    nose.tools.eq_(utext, result)


def test_latin1():
    "Tests utf-8 encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/latin_1.txt")


def test_utf8():
    "Tests utf-8 w/o BOM encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/utf-8.txt")


def test_utf8():
    "Tests utf-8 with BOM encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/utf-8-bom.txt")


def test_utf16le():
    "Tests utf-16 Little Endian encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/utf-16le.txt")


def test_utf16be():
    "Tests utf-16 Big Endian encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/utf-16be.txt")


def test_utf32le():
    "Tests utf-32 Little Endian encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/utf-32le.txt")


def test_utf32be():
    "Tests utf-32 Big Endian encoding is properly decoded"
    _do_test("tests/resources/unicodehelper/utf-32be.txt")


def test_js_safe():
    _do_test("tests/resources/unicodehelper/unsafe_js.txt",
             result=u'?',
             js_safe=True)

def test_js_safe_already_unicode():
    udata = unicodehelper.decode(u'\u0115', js_safe=True)
    nose.tools.eq_(udata, u'?')
