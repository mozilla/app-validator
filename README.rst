===================================
 marketplace.mozilla.org Validator
===================================

The Apps Validator is a tool designed to scan open web apps for
problems and invalid code. By using a combination of various techniques and
detection mechanisms, the validator is capable of being both efficient as well
as thorough.

-------
 Setup
-------

Prerequisites
=============

Python Libraries:

- argparse
- cssutils
- fastchardet

Python Libraries for Testing:

- nose
- coverage

You can install everything you need for running and testing with ::

    pip install -r requirements.txt


Submodules
==========

The validator may require some submodules to work. Make sure to run ::

    git clone --recursive git://github.com/mozilla/app-validator.git

so that you get all of the goodies inside.


Spidermonkey
============

A working copy of Spidermonkey (debug or non-debug is fine) is required. The
version installed must include support for the Parser API. At the time of this
writing the version of Spidermonkey included with major package managers does
not yet include the Parser API.

How do you know if your js binary has the Parser API? Run this::

    js -e 'Reflect;'

There should be no error output.

The best way to make sure you install the right Spidermonkey is to `clone`_ the
mozilla-central repo or `download the tip`_ (which is faster). Then build it
from source like this::

    cd mozilla-central
    cd js/src
    autoconf2.13
    ./configure
    make
    sudo cp dist/bin/js /usr/local/bin/js

You must use autoconf at *exactly* 2.13 or else it won't work. If you're using
`brew`_ on Mac OS X you can get autoconf2.13 with this::

    brew install https://gist.github.com/raw/765545/c87a75f2cf9e26c153970522e227f1c1cf63fb81/autoconf213.rb

If you don't want to put the ``js`` executable in your ``$PATH`` or you want it
in a custom path, you can define it as ``$SPIDERMONKEY_INSTALLATION`` in
your environment.

.. _`brew`: http://mxcl.github.com/homebrew/
.. _`clone`: http://hg.mozilla.org/mozilla-central/
.. _`download the tip`: http://hg.mozilla.org/mozilla-central/archive/tip.tar.bz2

---------
 Running
---------

Run the validator as follows ::

    python app-validator <path to app> [-o <output type>] [-v] [--boring] [--selfhosted]

The path to the XPI should point to an XPI file.

-o                  The type of output to generate. Types are listed below.
-v                  Enable verbose mode. Extra information will be displayed in
                    verbose mode, namely notices (informational messages),
                    Jetpack information if available, extra error info (like
                    contexts, file data, etc.), and error descriptions. This
                    only applies to ``-o text``.
--unlisted          Disables messages that are specific to apps hosted on
                    Marketplace.
--boring            Disables colorful shell output.

Output Type:
============

The output type may be either of the following:

text (default)
    Outputs a textual summary of the addo-on analysis. Supports verbose mode.
json
    Outputs a JSON snippet representing a full summary of the analysis.


--------
 Output
--------

Text Output Mode:
=================

In ``text`` output mode, output is structured in the format of one
message per line. The messages are prefixed by their priority level
(i.e.: "Warning: This is the message").

At the head of the text output is a block describing what the app type was
determined to be.


JSON Output Mode:
=================

In ``JSON`` output mode, output is formatted as a JSON snippet
containing all messages. The format for the JSON output is that of the
sample document below.

::

    {
        "detected_type": "packaged_app",
        "errors": 2,
        "warnings": 1,
        "notices": 1,
        "success": false,
        "ending_tier": 4,
        "messages": [
            {
                "uid": "123456789",
                "id": ["module", "function", "error"],
                "type": "error",
                "message": "This is the error message text.",
                "description": ["Description of the error message.",
                                "Additional description text"],
                "file": "chrome/foo.bar",
                "line": 12,
                "column": 50,
                "context: [
                    "   if(foo = bar())",
                    "       an_error_is_somewhere_on_this_line.prototy.eval("whatever");",
                    null
                ],
                "tier": 2
            }
        ]
    }


JSON Notes:
-----------

File Hierarchy
~~~~~~~~~~~~~~

When a subpackage exists, an angle bracket will delimit the subpackage
name and the message text.

If no applicable file is available (i.e.: when a file is missing), the
``file`` value will be empty. If a ``file`` value is available within a
subpackage, then the ``file`` attribute will be a list containing the
name of the outermost subpackage's name, followed by each successive
concentric subpackage's name, followed by the name of the file that the
message was generated in. If no applicable file is available within a
subpackage, the ``file`` attribute is identical, except the last element
of the list in the ``file`` attribute is an empty string.

For instance, this tree would generate the following messages:

::

    package_to_test.xpi
        |
        |-install.rdf
        |-chrome.manifest
        |-subpackage.xpi
        |  |
        |  |-subsubpackage.xpi
        |     |
        |     |-chrome.manifest
        |     |-install.rdf
        |
        |-subpackage.jar
           |
           |-install.rdf

::

    {
        "type": "notice",
        "message": "<em:type> not found in install.rdf",
        "description": " ... ",
        "file": "install.rdf",
        "line": 0
    },
    {
        "type": "error",
        "message": "Invalid chrome.manifest subject: override",
        "description": " ... ",
        "file": "chrome.manifest",
        "line": 7
    },
    {
        "type": "error",
        "message": "subpackage.xpi > install.rdf missing from theme",
        "description": " ... ",
        "file": ["subpackage.xpi", ""],
        "line": 0
    },
    {
        "type": "error",
        "message": "subpackage.xpi > subsubpackage.xpi > Invalid chrome.manifest subject: sytle",
        "description": " ... ",
        "file": ["subpackage.xpi", "subsubpackage.xpi", "chrome.manifest"],
        "line": 5
    }

Line Numbers and Columns
~~~~~~~~~~~~~~~~~~~~~~~~

Line numbers are 1-based. Column numbers are 0-based. This can be
confusing from a programmatic standpoint, but makes literal sense. "Line
one" would obviously refer to the first line of a file.

Contexts
~~~~~~~~

The context attribute of messages will either be a list or null. Null
contexts represent the validator's inability to determine surrounding
code. As a list, there will always be three elements. Each element
represents a line surrounding the message's location.

The middle element of the context list represents the line of interest. If
an element of the context list is null, that line does not exist. For
instance, if an error is on the first line of a file, the context might
look like:

::

    [
        null,
        "This is the line with the error",
        "This is the second line of the file"
    ]

The same rule applies for the end of a file and for files with only one line.

---------
 Testing
---------

Unit tests can be run with ::

    fab test

or, after setting the proper python path: ::

    nosetests

----------
 Updating
----------

Some regular maintenance needs to be performed on the validator in order to
make sure that the results are accurate.

JS Libraries
============

A list of JS library hashes is kept to allow for whitelisting. This must be
regenerated with each new library version. To update: ::

    cd extras
    mkdir jslibs
    python jslibfetcher.py
    python build_whitelist.py jslibs/
    # We keep a special hash for testing
    echo "e96461c6c19608f528b4a3c33a032b697b999b62" >> whitelist_hashes.txt
    mv whitelist_hashes.txt ../validator/testcases/hashes.txt

To add new libraries to the mix, edit ``extras/jslibfetcher.py`` and add the
version number to the appropriate tuple.

