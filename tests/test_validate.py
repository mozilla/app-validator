import json

from appvalidator import validate_app, validate_packaged_app
from helper import safe


@safe
def test_webapp_new():
    """Test that webapps can be validated."""
    with open("tests/resources/testwebapp.webapp") as file_:
        out = validate_app(file_.read())
    j = json.loads(out)
    assert j["success"], "Expected not to fail: %s" % j


@safe
def test_packaged_app_new():
    """Test that packaged apps can be validated."""
    out = validate_packaged_app("tests/resources/packaged_app.zip",
                                listed=False)
    j = json.loads(out)
    assert j["success"], "Expected not to fail: %s" % j


@safe
def test_packaged_app_bundle():
    """Test that packaged apps can be validated (format=None)."""
    out = validate_packaged_app("tests/resources/packaged_app.zip",
                                listed=False, format=None)
    assert out.get_resource("packaged")


@safe
def test_langpack():
    """Test that langpack apps can be validated."""
    out = validate_packaged_app("tests/resources/langpack.zip",
                                listed=False)
    j = json.loads(out)
    assert j["success"], "Expected not to fail: %s" % j


@safe
def test_langpack_bundle():
    """Test that langpack apps can be validated (format=None)."""
    out = validate_packaged_app("tests/resources/langpack.zip",
                                listed=False, format=None)
    assert out.get_resource("packaged")


@safe
def test_server_name_indication():
    # Make sure this doesn't raise an ImportError.
    # This is a sanity check to make sure all requirements are installed
    # to handle SSL Server Name Indication.
    # See https://bugzilla.mozilla.org/show_bug.cgi?id=875142
    from requests.packages.urllib3.contrib import pyopenssl  # noqa
