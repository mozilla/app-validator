import re
import fnmatch
import cssutils

from appvalidator.contextgenerator import ContextGenerator

BAD_URL_PAT = "url\(['\"]?(?!(chrome:|resource:))(\/\/|(ht|f)tps?:\/\/|data:)[a-z0-9\/\-\.#]*['\"]?\)"
BAD_URL = re.compile(BAD_URL_PAT, re.I)


def test_css_file(err, filename, data, line_start=1):
    "Parse and test a whole CSS file."

    tokenizer = cssutils.tokenize2.Tokenizer()
    context = ContextGenerator(data)

    data = "".join(c for c in data if 8 < ord(c) < 127)

    token_generator = tokenizer.tokenize(data)

    try:
        _run_css_tests(err,
                       tokens=token_generator,
                       filename=filename,
                       line_start=line_start - 1,
                       context=context)
    except:  # pragma: no cover
        # This happens because tokenize is a generator.
        # Bravo, Mr. Bond, Bravo.
        err.warning(("testcases_markup_csstester",
                     "test_css_file",
                     "could_not_parse"),
                    "Could not parse CSS file",
                    "CSS file could not be parsed by the tokenizer.",
                    filename)
        #raise
        return


def test_css_snippet(err, filename, data, line):
    "Parse and test a CSS nugget."

    # Re-package to make it CSS-complete. Note the whitespace to prevent
    # the extra code from showing in the context output.
    data = "#foo{\n\n%s\n\n}" % data

    test_css_file(err, filename, data, line)


def _run_css_tests(err, tokens, filename, line_start=0, context=None):
    """Processes a CSS file to test it for things that could cause it
    to be harmful to the browser."""

    last_descriptor = None

    skip_types = ("S", "COMMENT")

    identity_box_mods = []
    unicode_errors = []

    while True:

        try:
            (tok_type, value, line, position) = tokens.next()
        except UnicodeDecodeError:
            unicode_errors.append(str(line + line_start))
            continue
        except StopIteration:
            break
        except Exception, e:
            # Comment me out for debug!
            raise

            print type(e), e
            print filename
            print line + line_start
            continue

    if unicode_errors:
        err.info(("testcases_markup_csstester",
                  "test_css_file",
                  "unicode_decode"),
                 "Unicode decode error.",
                 ["While decoding a CSS file, an unknown character was "
                  "encountered, causing some problems.",
                  "Lines: %s" % ", ".join(unicode_errors)],
                 filename)
