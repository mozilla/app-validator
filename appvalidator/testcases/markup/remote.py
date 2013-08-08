from appvalidator.python.HTMLParser import HTMLParser


class RemoteHTMLParser(HTMLParser):

    def __init__(self, err):
        HTMLParser.__init__(self)
        self.err = err

    def handle_starttag(self, tag, attrs):
        if tag == "html":
            attrs = dict(attrs)
            if "manifest" in attrs:
                self.err.metadata["appcache"] = attrs["manifest"]
