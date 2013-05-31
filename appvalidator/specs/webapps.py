import simplejson as json
import types
import urlparse

import appvalidator.python.copy as copy

from ..constants import DESCRIPTION_TYPES
from ..specprocessor import Spec, LITERAL_TYPE


_FULL_PERMISSIONS = ("readonly", "readwrite", "readcreate", "createonly")


class WebappSpec(Spec):
    """This object parses and subsequently validates webapp manifest files."""

    SPEC_NAME = "Web App Manifest"
    MORE_INFO = ("You can find more information at "
                 "https://developer.mozilla.org/docs/Apps/Manifest")
    MIN_REQUIRED_ICON_SIZE = 128

    PERMISSIONS = (
        "alarms", "attention", "audio-channel-normal", "audio-channel-content",
        "audio-channel-notification", "audio-channel-alarm",
        "audio-channel-ringer", "audio-channel-telephony",
        "audio-channel-publicnotification", "background-sensors",
        "backgroundservice", "bluetooth", "browser", "camera", "contacts",
        "desktop-notification", "device-storage:apps", "device-storage:music",
        "device-storage:pictures", "device-storage:sdcard",
        "device-storage:videos", "embed-apps", "fmradio", "geolocation",
        "idle", "mobileconnection", "mobilenetwork", "network-events",
        "networkstats-manage", "open-remote-window", "permissions", "power",
        "push", "settings", "sms", "storage", "systemXHR", "tcp-socket",
        "telephony", "time", "voicemail", "webapps-manage", "wifi-manage")
    PERMISSIONS_ACCESS = {
        "contacts": _FULL_PERMISSIONS,
        "device-storage:apps": _FULL_PERMISSIONS,
        "device-storage:music": _FULL_PERMISSIONS,
        "device-storage:pictures": _FULL_PERMISSIONS,
        "device-storage:sdcard": _FULL_PERMISSIONS,
        "device-storage:videos": _FULL_PERMISSIONS,
        "settings": ("readonly", "readwrite"),
    }

    SPEC = {
        "expected_type": dict,
        "required_nodes": ["name", "description", "developer"],
        "required_nodes_when": {"default_locale": lambda n: "locales" in n},
        "allowed_once_nodes": ["launch_path", "icons", "locales",
                               "default_locale", "installs_allowed_from",
                               "version", "screen_size", "required_features",
                               "orientation", "fullscreen", "appcache_path",
                               "type", "activities", "permissions", "csp",
                               "messages"],
        "allowed_nodes": [],
        "disallowed_nodes": ["widget"],
        "child_nodes": {
            "name": {"expected_type": types.StringTypes,
                     "max_length": 128,
                     "not_empty": True},
            "description": {"expected_type": types.StringTypes,
                            "max_length": 1024,
                            "not_empty": True},
            "launch_path": {"expected_type": types.StringTypes,
                            "process": lambda s: s.process_launch_path,
                            "not_empty": True},
            "icons": {"expected_type": dict,
                      "child_process": lambda s: s.process_icon_size,
                      "process": lambda s: s.process_icons},
            "developer":
                {"expected_type": dict,
                 "child_nodes": {"name": {"expected_type": types.StringTypes,
                                          "not_empty": True},
                                 "url": {"expected_type": types.StringTypes,
                                         "not_empty": True,
                                         "process":
                                             lambda s: s.process_dev_url}},
                 "required_nodes": ["name"],
                 "allowed_once_nodes": ["url", "email"]},
            "locales":
                {"expected_type": dict,
                 "allowed_nodes": ["*"],
                 "child_nodes": {"*": {"expected_type": dict,
                                       "child_nodes": {}}}},  # Set in __init__
            "default_locale": {"expected_type": types.StringTypes,
                               "not_empty": True},
            "installs_allowed_from": {"expected_type": list,
                                      "process": lambda s: s.process_iaf,
                                      "not_empty": True},
            "version": {"expected_type": types.StringTypes,
                        "not_empty": True,
                        "value_matches": r"^[a-zA-Z0-9_,\*\-\.]+$"},
            "screen_size":
                {"expected_type": dict,
                 "allowed_once_nodes": ["min_height", "min_width"],
                 "not_empty": True,
                 "child_nodes":
                     {"min_height":
                          {"expected_type": LITERAL_TYPE,
                           "process": lambda s: s.process_screen_size},
                      "min_width":
                          {"expected_type": LITERAL_TYPE,
                           "process": lambda s: s.process_screen_size}}},
            "required_features": {"expected_type": list},
            "orientation": {"expected_type": DESCRIPTION_TYPES,
                            "process": lambda s: s.process_orientation},
            "fullscreen": {"expected_type": types.StringTypes,
                           "values": ["true", "false"]},
            "appcache_path": {"expected_type": types.StringTypes,
                              "process": lambda s: s.process_appcache_path},
            "type": {"expected_type": types.StringTypes,
                     "process": lambda s: s.process_type},
            "activities": {
                "expected_type": dict,
                "allowed_nodes": ["*"],
                "child_nodes": {
                    "*": {
                        "expected_type": dict,
                        "required_nodes": ["href"],
                        "allowed_once_nodes": ["disposition", "filters"],
                        "child_nodes": {
                            "href": {"expected_type": types.StringTypes,
                                     "process": lambda s: s.process_act_href,
                                     "not_empty": True},
                            "disposition": {"expected_type": types.StringTypes,
                                            "values": ["window", "inline"]},
                            "filters": {
                                "expected_type": dict,
                                "allowed_nodes": ["*"],
                                "child_nodes":
                                    {"*": {"expected_type": DESCRIPTION_TYPES,
                                           "process":
                                               lambda s: s.process_act_type,
                                           "not_empty": True}}
                            },
                            "returnValue": {
                                "expected_type": bool}
                        }
                    }
                }
            },
            "permissions": {
                "allowed_nodes": PERMISSIONS,
                "expected_type": dict,
                "unknown_node_level": "error",
                "child_nodes": {
                    "*": {
                        "expected_type": dict,
                        "required_nodes": ["description"],
                        "allowed_once_nodes": ["access"],
                        "child_nodes": {
                            "description": {"expected_type": types.StringTypes,
                                            "not_empty": True},
                            "access": {"expected_type": types.StringTypes,
                                       "not_empty": True}
                        }
                    }
                },
                "process": lambda s: s.process_permissions
            },
            "csp": {"expected_type": types.StringTypes,
                    "not_empty": True},
            "messages": {
                "expected_type": list,
                "process": lambda s: s.process_messages,
            },
        }
    }

    def __init__(self, data, err, **kwargs):
        self.SPEC = copy.deepcopy(self.SPEC)

        # Get all of the locale-able nodes and allow them to be included within
        # locale elements.
        locale_nodes = ("name", "description", "launch_path", "icons",
                        "developer", "version", "screen_size", "orientation",
                        "fullscreen", "appcache_path", )
        child_nodes = self.SPEC["child_nodes"]
        sparse_nodes = dict((k, v) for k, v in child_nodes.items() if
                            k in locale_nodes)
        # Create a copy so we can modify it without modifying the *actual*
        # version.
        sparse_nodes = copy.deepcopy(sparse_nodes)

        if err.get_resource("packaged"):
            self.SPEC["required_nodes"].append("launch_path")

        # Allow the developer to avoid localizing their name.
        del sparse_nodes["developer"]["required_nodes"]
        sparse_nodes["developer"]["allowed_once_nodes"].append("name")

        # Put the locale bits in their appropriate place.
        locale_all_nodes = child_nodes["locales"]["child_nodes"]["*"]
        locale_all_nodes["child_nodes"] = sparse_nodes
        locale_all_nodes["allowed_once_nodes"] = locale_nodes

        # If we're listed, we require icons.
        if err.get_resource("listed"):
            self.SPEC["required_nodes"].append("icons")
            self.SPEC["allowed_once_nodes"].remove("icons")

        super(WebappSpec, self).__init__(data, err, **kwargs)

    def _path_valid(self, path, can_be_asterisk=False, can_be_absolute=False,
                    can_be_relative=False, can_be_data=False,
                    can_have_protocol=False):
        """Test whether a URL is a valid URL."""

        if path == "*":
            return can_be_asterisk
        if path.startswith("data:"):
            return can_be_data

        # Nothing good comes from relative protocols.
        if path.startswith("//"):
            return False

        # Try to parse the URL.
        try:
            parsed_url = urlparse.urlparse(path)

            # If the URL is relative, return whether the URL can be relative.
            if not parsed_url.scheme or not parsed_url.netloc:
                return (can_be_absolute if parsed_url.path.startswith("/") else
                        can_be_relative)

            # If the URL is absolute but uses and invalid protocol, return False.
            if parsed_url.scheme.lower() not in ("http", "https", ):
                return False

            # Return whether absolute URLs are allowed.
            return can_have_protocol

        except ValueError:
            # If there was an error parsing the URL, return False.
            return False

    def process_launch_path(self, node):
        if not node.startswith("/") or node.startswith("//"):
            self.err.error(
                err_id=("spec", "webapp", "launch_path_rel"),
                error="`launch_path` must be a path relative to app's origin.",
                description=["The `launch_path` of a web app must be a path "
                             "relative to the origin of the app.",
                             "Found: %s" % node,
                             self.MORE_INFO])

    def process_icon_size(self, node_name, node):
        if not node_name.isdigit():
            self.err.error(
                err_id=("spec", "webapp", "icon_not_num"),
                error="`icons` size is not a number.",
                description=["Icon sizes (keys) must be natural numbers.",
                             "Found: %s" % node_name,
                             self.MORE_INFO])

        if not self._path_valid(node, can_be_absolute=True,
                                can_have_protocol=True,
                                can_be_data=True,
                                can_be_relative=True):
            self.err.error(
                err_id=("spec", "webapp", "icon_path"),
                error="`icons` paths must be absolute paths.",
                description=["Paths to icons must be absolute paths, relative "
                             "URIs, or data URIs.",
                             "Found: %s" % node,
                             self.MORE_INFO])

    def process_icons(self, node):
        if not node:
            return

        # This test only applies to listed apps.
        if self.err.get_resource("listed"):
            max_size = max(int(x) for x in node.keys() if x.isdigit())
            if max_size < self.MIN_REQUIRED_ICON_SIZE:
                self.err.error(
                    err_id=("spec", "webapp", "icon_minsize"),
                    error="An icon of at least %dx%d pixels must be provided." %
                            (self.MIN_REQUIRED_ICON_SIZE,
                             self.MIN_REQUIRED_ICON_SIZE),
                    description="An icon with a minimum size of 128x128 must "
                                "be provided by each app.")

    def process_dev_url(self, node):
        if not self._path_valid(node, can_have_protocol=True):
            self.err.error(
                err_id=("spec", "webapp", "dev_url"),
                error="Developer URLs must be full or absolute URLs.",
                description=["`url`s provided for the `developer` element must "
                             "be full URLs (including the protocol).",
                             "Found: %s" % node,
                             self.MORE_INFO])

    def process_iaf(self, node):
        market_urls = set()

        # Import the constants that are overwritten by the call to the
        # validator in Zamboni.
        from ..validate import constants

        for index, item in enumerate(node):
            name = "`installs_allowed_from[%d]`" % index
            if not isinstance(item, types.StringTypes):
                self.err.error(
                    err_id=("spec", "webapp", "iaf_type"),
                    error="%s must be a string." % name,
                    description=["%s was found in `installs_allowed_from`, "
                                 "but it is not a string type." % name,
                                 self.MORE_INFO])
            elif not self._path_valid(item, can_be_asterisk=True,
                                      can_have_protocol=True):
                self.err.error(
                    err_id=("spec", "webapp", "iaf_invalid"),
                    error="Bad `installs_allowed_from` URL.",
                    description=["URLs included in `installs_allowed_from` "
                                 "must be valid, absolute URLs. %s does not "
                                 "conform to this requirement." % name,
                                 "Found: %s" % item,
                                 self.MORE_INFO])
            elif (item.startswith("http://") and "https://%s" % item[7:] in
                      constants.DEFAULT_WEBAPP_MRKT_URLS):
                self.err.error(
                    err_id=("spec", "webapp", "iaf_bad_mrkt_protocol"),
                    error="Marketplace URL must use HTTPS.",
                    description=["You included a Marketplace URL in the "
                                 "`installs_allowed_from` list, however the "
                                 "URL that you are using is not a secure URL. "
                                 "Change the protocol from `http://` to "
                                 "`https://` to correct this issue.",
                                 "Found: %s" % item,
                                 self.MORE_INFO])
            elif item == "*" or item in (self.err.get_resource("market_urls") or
                                         constants.DEFAULT_WEBAPP_MRKT_URLS):
                market_urls.add(item)

        if self.err.get_resource("listed") and not market_urls:
            self.err.error(
                err_id=("spec", "webapp", "iaf_no_amo"),
                error="App must allow installs from Marketplace for inclusion.",
                description="To be included on %s, a webapp needs to include "
                            "%s or '*' (wildcard) as an element in the "
                            "`installs_allowed_from` property." %
                                (constants.DEFAULT_WEBAPP_MRKT_URLS[0],
                                 ", ".join(constants.DEFAULT_WEBAPP_MRKT_URLS)))

    def process_messages(self, node):
        for message in node:
            if not isinstance(message, dict):
                self.err.error(
                    err_id=("spec", "webapp", "messages_not_obj"),
                    error="Manifest messages must be objects.",
                    description=["An item in the `messages` field of the "
                                 "manifest is not a key/value pair. See the "
                                 "manifest spec for more information.",
                                 self.MORE_INFO])
                continue

            if len(message.items()) != 1:
                self.err.error(
                    err_id=("spec", "webapp", "messages_not_kv"),
                    error="Manifest message objects may only have one key.",
                    description=["Perhaps unintuitively, the `messages` field "
                                 "of the manifest is a list of objects. Each "
                                 "object may only have one key/value pair.",
                                 self.MORE_INFO])
                continue

    def process_screen_size(self, node):
        if not node.isdigit():
            self.err.error(
                err_id=("spec", "webapp", "screensize_format"),
                error="`screen_size` values must be numeric.",
                description=["The values for `min_height` and `min_width` must "
                             "be strings containing only numbers.",
                             "Found: %s" % node,
                             self.MORE_INFO])

    def process_appcache_path(self, node):
        if self.err.get_resource("packaged"):
            self.err.error(
                err_id=("spec", "webapp", "appcache_packaged"),
                error="`appcache_path` is not allowed for packaged apps.",
                description=["Packaged apps cannot use Appcache. The "
                             "`appcache_path` field should not be provided in "
                             "a packaged app's manifest.",
                             self.MORE_INFO])
            return

        if not self._path_valid(node, can_be_absolute=True):
            self.err.error(
                err_id=("spec", "webapp", "appcache_not_absolute"),
                error="`appcache_path` is not an absolute path.",
                description=["The `appcache_path` must be a full, absolute URL "
                             "to the application cache manifest.",
                             "Found: %s" % node,
                             self.MORE_INFO])

    def process_type(self, node):
        if unicode(node) not in (u"web", u"privileged", u"certified", ):
            self.err.error(
                err_id=("spec", "webapp", "type_not_known"),
                error="`type` is not a recognized value",
                description=["The `type` key does not contain a recognized "
                             "value. `type` may only contain 'web', 'privileged', "
                             "or 'certified'.",
                             "Found value: '%s'" % node,
                             self.MORE_INFO])

        if self.err.get_resource("listed") and node == "certified":
            self.err.error(
                err_id=("spec", "webapp", "type_denied"),
                error="Certified apps cannot be listed on the Marketplace.",
                description=["Apps marked as `certified` cannot be listed on "
                             "the Firefox Marketplace.",
                             self.MORE_INFO])

        if not self.err.get_resource("packaged") and node != "web":
            self.err.error(
                err_id=("spec", "webapp", "type_denied_web"),
                error="Web apps may not be privileged.",
                description=["Web apps may not have a `type` of `privileged` "
                             "or `certified`.",
                             "Detected type: %s" % node,
                             self.MORE_INFO])

    def process_act_href(self, node):
        if not self._path_valid(node, can_be_absolute=True,
                                can_be_relative=True):
            self.err.error(
                err_id=("spec", "webapp", "act_href_path"),
                error="Activity `href` is not a valid path.",
                description=["The `href` value for an activity must be a an "
                             "absolute URL to the application cache manifest.",
                             "Found: %s" % node,
                             self.MORE_INFO])

    def process_act_type(self, node):
        if (isinstance(node, list) and
            not all(isinstance(s, types.StringTypes) for s in node)):
            self.err.error(
                err_id=("spec", "webapp", "act_type"),
                error="Activity `type` is not valid.",
                description=["The `type` value for an activity must either be "
                             "a string or array of strings.",
                             "Found: [%s]" % ", ".join(map(str, node)),
                             self.MORE_INFO])

    def process_orientation(self, node):
        values = [u"portrait", u"landscape", u"portrait-secondary",
                  u"landscape-secondary", u"portrait-primary",
                  u"landscape-primary"]
        message = ("The value provided for a webapp's orientation should be "
                   "either a string or an array of strings.")

        if isinstance(node, types.StringTypes):
            # The top-level conditional is going to be the type detection.
            # We don't want to trip our other conditions by mixing
            # conditionals.
            if unicode(node) in values:
                return
            self.err.error(
                err_id=("spec", "webapp", "orientation", "str"),
                error="Webapp `orientation` is not a valid value.",
                description=[message,
                             "The value provided was not a recognized value.",
                             "Recognized values: %s" % ", ".join(values),
                             self.MORE_INFO])
        elif isinstance(node, list):
            if not node:
                self.err.error(
                    err_id=("spec", "webapp", "orientation", "listempty"),
                    error="Webapp `orientation` must contain at least one "
                          "valid orientation.",
                    description=["If `orientation` is defined as an array, it "
                                 "must contain at least one valid value.",
                                 "Recognized values: %s" % ", ".join(values),
                                 self.MORE_INFO])
            for value in node:
                if not isinstance(value, types.StringTypes):
                    self.err.error(
                        err_id=("spec", "webapp", "orientation", "listtype"),
                        error="Webapp `orientation` array does not contain "
                              "string values.",
                        description=[message,
                                     "When `orientation` is provided as an "
                                     "array, all of its values must be "
                                     "strings.",
                                     "Found value: %s" % value,
                                     self.MORE_INFO])
                elif unicode(value) not in values:
                    self.err.error(
                        err_id=("spec", "webapp", "orientation", "listval"),
                        error="Webapp `orientation` array contains invalid "
                              "values.",
                        description=[message,
                                     "The value provided was not a recognized "
                                     "value.",
                                     "Recognized values: %s" %
                                         ", ".join(values),
                                     self.MORE_INFO])
        else:
            self.err.error(
                err_id=("spec", "webapp", "orientation", "type"),
                error="Webapp `orientation` is not a valid type.",
                description=[message,
                             "The value provided was not a string or an "
                             "array.",
                             self.MORE_INFO])

    def process_permissions(self, node):
        requested_permissions = set()
        for permission, per_node in node.items():
            if permission not in self.PERMISSIONS_ACCESS:
                continue

            if "access" not in per_node:
                self.err.error(
                    err_id=("spec", "webapp", "permission", "missing_access"),
                    error="Webapp permission missing `access` node.",
                    description=["The permission '%s' requires that an "
                                 "`access` node be provided in addition to a "
                                 "`description` node." % permission,
                                 "Access values for this permission: %s" %
                                     ", ".join(
                                         self.PERMISSIONS_ACCESS[permission]),
                                 self.MORE_INFO])
                continue

            access_value = per_node.get("access")
            if access_value not in self.PERMISSIONS_ACCESS[permission]:
                self.err.error(
                    err_id=("spec", "webapp", "permission", "bad_access"),
                    error="Webapp permission missing `access` node.",
                    description=["The permission '%s' was given an invalid "
                                 "`access` node value." % permission,
                                 "Valid values: %s" %
                                     ", ".join(
                                         self.PERMISSIONS_ACCESS[permission]),
                                 "Found value: %s" % access_value,
                                 self.MORE_INFO])

            requested_permissions.add(permission)

        self.err.save_resource("permissions", list(requested_permissions))

    def parse(self, data):
        if isinstance(data, types.StringTypes):
            return json.loads(data, strict=True)
        return data

    def validate_root_node(self, root):
        if not isinstance(root, dict):
            self.err.error(
                    err_id=("spec", "webapp", "root_type"),
                    error="App manifest root is not an object.",
                    description="The root of the manifest is expected to be an "
                                "object. It may not be a list or a literal.")
            return False

    def get_root_node(self, data):
        return "root", data

    def has_attribute(self, node, key):
        return False

    def get_child(self, node, child_name):
        if child_name not in node:
            return None
        return node[child_name]

    def has_child(self, node, child_name):
        return child_name in node

    def get_children(self, node):
        return node.items()
