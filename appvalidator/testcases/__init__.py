
TEST_TIERS = {}


def register_test(tier=1):
    """Register tests for the validation flow."""

    def wrap(function):
        "Wrapper function to decorate registered tests."

        # Make sure the tier exists before we add to it
        if tier not in TEST_TIERS:
            TEST_TIERS[tier] = []

        # Add a test object to the test's tier
        TEST_TIERS[tier].append(function)

        # Return the function to be run
        return function

    # Return the wrapping function (for use as a decorator)
    return wrap


def _get_tiers():
    """Return a list of tier values."""
    return TEST_TIERS.keys()


def _get_tests(tier):
    """Return a generator of test functions."""
    return TEST_TIERS[tier]
