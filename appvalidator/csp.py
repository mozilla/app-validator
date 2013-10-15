
CSP_INFO = "https://developer.mozilla.org/Apps/CSP"

MESSAGE_TITLE = "CSP Violation Detected"
MESSAGE_GENERAL_DESC = ("You can find more information about what is and is "
                        "not allowed by the CSP on the Mozilla Developers "
                        "website. %s" % CSP_INFO)
MESSAGE_DESC = ["It appears that your code may be performing an action which "
                "violates the CSP (content security policy) for privileged "
                "apps.", MESSAGE_GENERAL_DESC]
MESSAGE_DESC_WEB = ["An action that you're performing violates the CSP "
                    "(content security policy). While this does not affect "
                    "your app, if you decide to add permissions to your app "
                    "in the future, you will be unable to do so until this "
                    "problem is corrected. It is highly recommended that "
                    "you remedy this.", MESSAGE_GENERAL_DESC]

def warn(err, filename, line, column, context, violation_type="default",
         severity="warning"):

    app_type = err.get_resource("app_type")

    if app_type == "web":
        severity = "warning"

    params = dict(err_id=("csp", violation_type),
                  description=MESSAGE_DESC_WEB if app_type == "web" else
                              MESSAGE_DESC,
                  filename=filename,
                  line=line,
                  column=column,
                  context=context)
    params[severity] = MESSAGE_TITLE

    getattr(err, severity)(**params)
