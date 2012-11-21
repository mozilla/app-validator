from basebundle import BaseErrorBundle
from manifestmixin import ManifestMixin
from metadatamixin import MetadataMixin


class ErrorBundle(MetadataMixin, ManifestMixin, BaseErrorBundle):

    def __init__(self, listed=True, spidermonkey=None, *args, **kwargs):
        super(ErrorBundle, self).__init__(*args, **kwargs)

        if spidermonkey:
            self.save_resource("SPIDERMONKEY", spidermonkey)
        self.save_resource("listed", listed)
