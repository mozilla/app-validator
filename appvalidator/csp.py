
CSP_INFO = "https://developer.mozilla.org/en-US/docs/Security/CSP"

MESSAGE_TITLE = "CSP Violation Detected"
MESSAGE_DESCRIPTION = ["It appears that your code may be performing an action "
                       "which violates the CSP (content security policy) for "
                       "privileged apps.",
                       "You can find more information about what is and is "
                       "not allowed by the CSP on the Mozilla Developers "
                       "website. %s" % CSP_INFO]

def warn(err, filename, line, column, context, violation_type="default",
         severity="warning"):
    params = dict(err_id=("csp", violation_type),
                  description=MESSAGE_DESCRIPTION,
                  filename=filename,
                  line=line,
                  column=column,
                  context=context)
    params[severity] = MESSAGE_TITLE
    getattr(err, severity)(**params)
