
class ManifestMixin(object):
    """This mixin adds the manifest to the final JSON output. The manifest
    should be stored in the resources under the name "manifest" as a dict.

    """

    def _extend_json(self):
        """Output the manifest as part of the main JSON blob."""
        extension = super(ManifestMixin, self)._extend_json() or {}
        extension.update(manifest=self.get_resource("manifest"))
        return extension
