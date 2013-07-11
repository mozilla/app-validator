import json

from mock import patch

from appvalidator import validate_app, validate_packaged_app
from helper import safe


@safe
def test_webapp_new():
    """Test that webapps can be validated with the new api."""
    with open("tests/resources/testwebapp.webapp") as file_:
        out = validate_app(file_.read())
    j = json.loads(out)
    assert j["success"], "Expected not to fail: %s" % j


@safe
def test_packaged_app_new():
    """Test that packaged apps can be validated with the new api."""
    out = validate_packaged_app("tests/resources/packaged_app.zip",
                                listed=False)
    j = json.loads(out)
    assert j["success"], "Expected not to fail: %s" % j


@safe
def test_packaged_app_bundle():
    """Test that packaged apps can be validated with the new api."""
    out = validate_packaged_app("tests/resources/packaged_app.zip",
                                listed=False, format=None)
    assert out.get_resource("packaged")
