from test_webapp import WebappBaseTestCase


class TestWebappActivity(WebappBaseTestCase):
    """
    This suite tests that web activities are properly handled for all
    reasonable combinations of valid nodes.
    """

    def setUp(self):
        super(TestWebappActivity, self).setUp()
        self.ad = self.data["activities"] = {
            "simple": {
                "href": "url.html",
                "disposition": "window",
                "returnValue": True,
                "filters": {
                    "literal": 123,
                    "array": ["literal", 123],
                    "filter_obj": {
                        "required": True,
                        "value": "literal",
                        "min": 1,
                        "max": 2,
                        "pattern": "asdf",
                        "patternFlags": "ig",
                        "regexp": "asdf",
                    },
                },
            },
        }
        self.simple = self.ad["simple"]

    def broken(self):
        self.analyze()
        return self.assert_failed(with_errors=True)

    def suspicious(self):
        self.analyze()
        return self.assert_failed(with_warnings=True)

    def test_pass(self):
        self.analyze()
        self.assert_silent()

    def test_missing_href(self):
        del self.simple["href"]
        self.broken()

    def test_min_features(self):
        self.data["activities"] = {
            "simple": {"href": "foo.html"},
        }
        self.analyze()
        self.assert_silent()

    def test_bad_href(self):
        self.simple["href"] = "http://foo.bar/asdf"
        self.broken()

    def test_bad_disposition(self):
        self.simple["disposition"] = "not a disposition"
        self.broken()

    def test_bad_returnValue(self):
        self.simple["returnValue"] = "foo"
        self.broken()

    def test_bad_extra(self):
        self.simple["extra"] = "this isn't part of the spec!"
        self.suspicious()

    def test_bad_filter_base(self):
        self.simple["filters"] = "foo"
        self.broken()

    def test_empty_filters(self):
        self.simple["filters"] = {}
        self.broken()

    def test_bad_basic_values(self):
        # Basic values can't be boolean, according to the spec.
        self.simple["filters"]["literal"] = True
        self.broken()

    def test_bad_basic_values_in_array(self):
        self.simple["filters"]["array"].append(True)
        self.broken()

    def test_empty_filterobj(self):
        self.simple["filters"]["filter_obj"] = {}
        self.broken()

    def test_extra_filterobj(self):
        self.simple["filters"]["filter_obj"]["extra"] = "foo"
        self.suspicious()

    def test_bad_filterobj_required(self):
        self.simple["filters"]["filter_obj"]["required"] = "foo"
        self.broken()

    def test_bad_filterobj_value(self):
        self.simple["filters"]["filter_obj"]["value"] = True
        self.broken()

    def test_bad_filterobj_value_array(self):
        self.simple["filters"]["filter_obj"]["value"] = [True]
        self.broken()

    def test_filterobj_value_array(self):
        self.simple["filters"]["filter_obj"]["value"] = [123, "foo"]
        self.analyze()
        self.assert_silent()

    def test_bad_filterobj_pattern(self):
        self.simple["filters"]["filter_obj"]["pattern"] = 123
        self.broken()

    def test_bad_filterobj_patternFlags(self):
        self.simple["filters"]["filter_obj"]["patternFlags"] = "asdf"
        self.broken()

    def test_bad_filterobj_patternFlags_length(self):
        self.simple["filters"]["filter_obj"]["patternFlags"] = "iiiii"
        self.broken()

    def test_bad_filterobj_regexp(self):
        self.simple["filters"]["filter_obj"]["regexp"] = 123
        self.broken()

    def test_filterobj_optional_elements(self):
        self.simple["filters"]["filter_obj"] = {"min": 1}
        self.analyze()
        self.assert_silent()
        self.simple["filters"]["filter_obj"] = {"required": True}
        self.analyze()
        self.assert_silent()
        # Thus, no one field is required.

