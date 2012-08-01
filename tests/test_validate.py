import json

from appvalidator.validate import validate_app


def test_webapp_new():
    """Test that webapps can be validated with the new api."""
    with open("tests/resources/testwebapp.webapp") as file_:
        out = validate_app(file_.read())
    j = json.loads(out)
    assert j["success"], "Expected not to fail"

