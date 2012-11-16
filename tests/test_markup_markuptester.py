# -*- coding: utf-8 -*-
from mock import patch
from nose.tools import eq_

import appvalidator.testcases.markup.markuptester as markuptester
from appvalidator.errorbundle import ErrorBundle
from appvalidator.constants import *

from js.js_helper import uses_js


def _test_xul(path, should_fail=False, type_=None):
    return _test_xul_raw(open(path).read(),
                        path,
                        should_fail,
                        type_)


def _test_xul_raw(data, path, should_fail=False, should_fail_csp=None,
                  type_=None):
    filename = path.split("/")[-1]
    extension = filename.split(".")[-1]

    err = ErrorBundle()
    if type_:
        err.set_type(type_)

    parser = markuptester.MarkupParser(err, debug=True)
    parser.process(filename, data, extension)

    print err.print_summary(verbose=True)

    if should_fail:
        assert any(m for m in (err.errors + err.warnings) if
                   m["id"][0] != "csp")
    else:
        assert not any(m for m in (err.errors + err.warnings) if
                       m["id"][0] != "csp")

    if should_fail_csp == True:
        assert any(m for m in (err.errors + err.warnings) if
                   m["id"][0] == "csp")
    elif should_fail_csp == False:
        assert not any(m for m in (err.errors + err.warnings) if
                       m["id"][0] == "csp")

    return err


def test_local_url_detector():
    "Tests that local URLs can be detected."

    err = ErrorBundle()
    mp = markuptester.MarkupParser(err)
    tester = mp._is_url_local

    assert tester("chrome://xyz/content/abc")
    assert tester("chrome://whatever/")
    assert tester("local.xul")
    assert not tester("http://foo.bar/")
    assert not tester("https://abc.def/")

    assert tester(u"chrome://xyz/content/abc")
    assert tester(u"chrome://whatever/")
    assert tester(u"local.xul")
    assert not tester(u"http://foo.bar/")
    assert not tester(u"https://abc.def/")


def test_html_file():
    "Tests a package with a valid HTML file."

    _test_xul("tests/resources/markup/markuptester/pass.html")


def test_xml_file():
    "Tests a package with a valid XML file."

    _test_xul("tests/resources/markup/markuptester/pass.xml")


def test_xml_bad_nesting():
    "Tests an XML file that has badly nested elements."
    _test_xul("tests/resources/markup/markuptester/bad_nesting.xml", True)


def test_has_cdata():
    "Tests that CDATA is good to go."
    _test_xul("tests/resources/markup/markuptester/cdata.xml")


def test_cdata_properly():
    """CDATA should be treated as text and be ignored by the parser."""

    err = _test_xul_raw("""<foo>
    <script type="text/x-jquery-tmpl">
    <![CDATA[
    <button><p><span><foo>
    </bar></zap>
    <selfclosing />
    <><><><""><!><
    ]]>
    </script>
    </foo>""", "foo.xul", should_fail=False)

    # Test that there are no problems if the CDATA element starts or ends on
    # the same line as the parent tag.
    err = _test_xul_raw("""<foo>
    <script><![CDATA[
    <button><p><span><foo>
    </bar></zap>
    <selfclosing />
    <><><><""><!><
    ]]></script>
    </foo>""", "foo.xul", should_fail=False)

    # Test that there are no problems if multiple CDATA elements open and
    # close on the same line.
    err = _test_xul_raw("""<foo>
    <foo><![CDATA[</bar></foo>]]></foo><![CDATA[
    <![CDATA[ <-- Should be ignored since we're buffering.</bar><zap>
    ]]>
    </foo>""", "foo.xul", should_fail=False)

    err = _test_xul_raw("""<foo>
    <![CDATA[
    <button><p><span><foo>
    </bar></zap>
    <selfclosing />
    <><><><""><!><
    ]]>
    </foo>""", "foo.xul", should_fail=False)

    err = _test_xul_raw("""
    <![CDATA[
    <button><p><span><foo>
    </bar></zap>
    <selfclosing />
    <><><><""><!><
    ]]>""", "foo.xul", should_fail=False)


def test_xml_overclosing():
    "Tests an XML file that has overclosed elements"
    _test_xul("tests/resources/markup/markuptester/overclose.xml", True)


def test_xml_extraclosing():
    "Tests an XML file that has extraclosed elements"
    _test_xul("tests/resources/markup/markuptester/extraclose.xml", True)


def test_html_ignore_comment():
    "Tests that HTML comment values are ignored"
    _test_xul("tests/resources/markup/markuptester/ignore_comments.html")


def test_invalid_markup():
    "Tests an markup file that is simply broken."

    result = _test_xul("tests/resources/markup/markuptester/bad.xml", True)
    assert result.warnings
    result = _test_xul("tests/resources/markup/markuptester/bad_script.xml",
                       False)
    assert result.notices


def test_bad_encoding():
    """Test that bad encodings don't cause the parser to fail."""
    _test_xul("tests/resources/markup/encoding.txt")


def test_self_closing_scripts():
    """Tests that self-closing script tags are not deletrious to parsing."""
    _test_xul_raw("""
    <foo>
        <script type="text/javascript"/>
        <list_item undecodable=" _ " />
        <list_item />
        <list_item />
    </foo>
    """, "foo.xul")


def test_script_attrs():
    """Test that script attributes are warned against."""

    _test_xul_raw("""
    <foo><bar onzap="" /></foo>
    """, "foo.xul", should_fail_csp=True)


def test_dom_mutation():
    """Test that DOM mutation events are warned against. This should fail both
    the standard tests as well as the CSP tests."""
    _test_xul_raw("""
    <foo><bar ondomattrmodified="" /></foo>
    """, "foo.xul", should_fail=True, should_fail_csp=True)


@uses_js
def test_proper_line_numbers():
    """Test that the proper line numbers are passed to test_js_snippet."""

    err = _test_xul_raw("""<foo>
    <script>
    eval("OWOWOWOWOWOWOWOW");
    </script>
    </foo>""", "foo.xul", should_fail_csp=True)

    assert err.errors
    error = err.errors[0]
    eq_(error["file"], "foo.xul")
    # 4 because it detects the script when it gets closed.
    eq_(error["line"], 4)


def test_script_scraping():
    """Test that the scripts in a document are collected properly."""

    err = ErrorBundle()
    parser = markuptester.MarkupParser(err, debug=True)
    parser.process("foo.xul", """
    <doc>
    <!-- One to be ignored -->
    <script type="text/javascript">
    eval("asdf");
    </script>
    </doc>
    """, "xul")

    assert err.errors
