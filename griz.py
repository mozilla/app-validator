import sys
from appvalidator import validate_app, validate_packaged_app

path = sys.argv[1]
if path.endswith(".webapp"):
    print validate_app(path, format="json")
else:
    print validate_packaged_app(path, format="json")
