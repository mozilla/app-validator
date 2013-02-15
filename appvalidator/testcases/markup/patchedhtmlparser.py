import re

try:
    import HTMLParser as htmlparser
except ImportError:  # pragma: no cover
    import html.parser as htmlparser

interesting_cdata = re.compile(r'<(/|\Z)')


class PatchedHTMLParser(htmlparser.HTMLParser):
    """
    A version of the Python HTML parser that includes the fixes bundled with
    the latest versions of Python.
    """

    def __init__(self, *args, **kwargs):
        htmlparser.HTMLParser.__init__(self, *args, **kwargs)
        # Added as a patch for various Python HTMLParser issues.
        self.cdata_tag = None

    # Code to fix for Python issue 670664
    def parse_starttag(self, i):
        self.__starttag_text = None
        endpos = self.check_for_whole_start_tag(i)
        if endpos < 0:
            return endpos
        rawdata = self.rawdata
        self.__starttag_text = rawdata[i:endpos]

        # Now parse the data between i+1 and j into a tag and attrs
        attrs = []
        match = htmlparser.tagfind.match(rawdata, i+1)
        assert match, 'unexpected call to parse_starttag()'
        k = match.end()
        self.lasttag = tag = rawdata[i+1:k].lower()

        while k < endpos:
            m = htmlparser.attrfind.match(rawdata, k)
            if not m:
                break
            attrname, rest, attrvalue = m.group(1, 2, 3)
            if not rest:
                attrvalue = None
            elif attrvalue[:1] == '\'' == attrvalue[-1:] or \
                 attrvalue[:1] == '"' == attrvalue[-1:]:
                attrvalue = attrvalue[1:-1]
                attrvalue = self.unescape(attrvalue)
            attrs.append((attrname.lower(), attrvalue))
            k = m.end()

        end = rawdata[k:endpos].strip()
        if end not in (">", "/>"):
            lineno, offset = self.getpos()
            if "\n" in self.__starttag_text:
                lineno = lineno + self.__starttag_text.count("\n")
                offset = len(self.__starttag_text) \
                         - self.__starttag_text.rfind("\n")
            else:
                offset = offset + len(self.__starttag_text)
            self.error("junk characters in start tag: %r"
                       % (rawdata[k:endpos][:20],))
        if end.endswith('/>'):
            # XHTML-style empty tag: <span attr="value" />
            self.handle_startendtag(tag, attrs)
        else:
            self.handle_starttag(tag, attrs)
            if tag in self.CDATA_CONTENT_ELEMENTS:
                self.set_cdata_mode(tag)
        return endpos

    def parse_endtag(self, i):
        rawdata = self.rawdata
        assert rawdata[i:i+2] == "</", "unexpected call to parse_endtag"
        match = htmlparser.endendtag.search(rawdata, i+1) # >
        if not match:
            return -1
        j = match.end()
        match = htmlparser.endtagfind.match(rawdata, i) # </ + tag + >
        if not match:
            if self.cdata_tag is not None:
                self.handle_data(rawdata[i:j])
                return j
            self.error("bad end tag: %r" % (rawdata[i:j],))
        tag = match.group(1).strip()

        if self.cdata_tag is not None and tag.lower() != self.cdata_tag:
            self.handle_data(rawdata[i:j])
            return j

        self.handle_endtag(tag.lower())
        self.clear_cdata_mode()
        return j

    def set_cdata_mode(self, tag):
        self.interesting = interesting_cdata
        self.cdata_tag = None
