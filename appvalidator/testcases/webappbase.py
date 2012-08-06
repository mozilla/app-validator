from . import register_test
from ..webapp import detect_webapp_string


@register_test(tier=1)
def test_app_manifest(err, package):

	if "manifest.webapp" not in xpi:
		return err.error(
			err_id=("webappbase", "test_app_manifest", "missing_manifest"),
			error="Packaged app missing manifest",
			description=["All apps must contain an app manifest file.",
						 "Attempted to find a manifest at `/manifest.webapp`, "
						 "but no file was found."])

	detect_webapp_string(err, package.read("manifest.webapp"))
