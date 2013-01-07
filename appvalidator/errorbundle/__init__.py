from basebundle import BaseErrorBundle
from manifestmixin import ManifestMixin
from metadatamixin import MetadataMixin


class ErrorBundle(MetadataMixin, ManifestMixin, BaseErrorBundle):
    """This class does all sorts of cool things. It gets passed around
    from test to test and collects up all the errors like the candy man
    'separating the sorrow and collecting up all the cream.' It's
    borderline magical.

    Keyword Arguments:

    **listed**
        True if the add-on is destined for Mozilla, false if not
    **spidermonkey**
        Optional path to the local spidermonkey installation

    """

    def __init__(self, listed=True, spidermonkey=None, *args, **kwargs):
        super(ErrorBundle, self).__init__(*args, **kwargs)

        if spidermonkey:
            self.save_resource("SPIDERMONKEY", spidermonkey)
        self.save_resource("listed", listed)
