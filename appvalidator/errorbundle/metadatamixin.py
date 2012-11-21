
class MetadataMixin(object):
    """
    This mixin adds metadata functionality to the standard error bundle.
    Including this in the error bundle allows the app to collect and process
    metadata during the validation process.
    """

    def __init__(self, *args, **kwargs):

        self.resources = {}
        self.pushable_resources = {}
        self.final_context = None

        self.metadata = {}

        super(MetadataMixin, self).__init__(*args, **kwargs)

    def get_resource(self, name):
        """Retrieve an object that has been stored by another test."""

        if name in self.resources:
            return self.resources[name]
        elif name in self.pushable_resources:
            return self.pushable_resources[name]
        else:
            return False

    def save_resource(self, name, resource, pushable=False):
        """Save an object such that it can be used by other tests."""

        if pushable:
            self.pushable_resources[name] = resource
        else:
            self.resources[name] = resource

    def _extend_json(self):
        """Output the metadata as part of the main JSON blob."""
        extension = super(MetadataMixin, self)._extend_json() or {}
        extension.update(metadata=self.metadata)
        return extension
