# marketplace.firefox.com Validator

The Apps Validator is a tool designed to scan open web apps for
problems and invalid code. By using a combination of various techniques and
detection mechanisms, the validator is capable of being both efficient as well
as thorough.

## Setup

### Prerequisites

Python Libraries:

- argparse
- cssutils
- fastchardet

Dev requirements:

- nose

You can install everything you need for running and testing with

```bash
pip install -r requirements.txt
```

#### Spidermonkey

A working copy of Spidermonkey (debug or non-debug is fine) is required.

The best way to make sure you install the right Spidermonkey is to
[clone](http://hg.mozilla.org/mozilla-central/) the mozilla-central repo
or [download the tip](http://hg.mozilla.org/mozilla-central/archive/tip.tar.bz2)
(which is faster). Then build it from source like this

```bash
cd mozilla-central
cd js/src
autoconf2.13
./configure
make
sudo cp dist/bin/js /usr/local/bin/js
```

You must use autoconf at *exactly* 2.13 or else it won't work. If you're using
`brew`_ on Mac OS X you can get autoconf2.13 with this

    brew install autoconf213

If you don't want to put the `js` executable in your `$PATH` or you want it
in a custom path, you can define it as `$SPIDERMONKEY_INSTALLATION` in
your environment.


## Running

Run the validator as follows:

```bash
python app-validator <path to app> [-o <output type>] [-v] [--boring] [--selfhosted]
```

The path to the XPI should point to an XPI file.

<dl>
    <dt>-o
    <dd>The type of output to generate. Types are listed below.
    <dt>-v
    <dd>Enable verbose mode. Extra information will be displayed in verbose mode,
    namely notices (informational messages), extra error info (like contexts, file
    data, etc.), and error descriptions. This only applies to ``-o text``.
    <dt>--unlisted
    <dd>Disables messages that are specific to apps hosted on Marketplace.
    <dt>--boring
    <dd>Disables colorful shell output.
</dl>

### Output

The output type may be either of the following:

<dl>
    <dt>text (default)
    <dd>Outputs a textual summary of the addo-on analysis. Supports verbose mode.
    <dt>json
    <dd>Outputs a JSON snippet representing a full summary of the analysis.
</dl>


#### Text Output Mode

In `text` output mode, output is structured in the format of one
message per line. The messages are prefixed by their priority level
(i.e.: "Warning: This is the message").

At the head of the text output is a block describing what the app type was
determined to be.


#### JSON Output Mode

In `JSON` output mode, output is formatted as a JSON snippet
containing all messages. The format for the JSON output is that of the
sample document below.


```js
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
```

A copy of the app's manifest (packaged or hosted) will be included in the
`manifest` field of the output.


### Line Numbers and Columns

Line numbers are 1-based. Column numbers are 0-based. This can be
confusing from a programmatic standpoint. "Line one" would refer to
the first line of a file.

### Contexts

The context attribute of messages will either be a list or null. Null
contexts represent the validator's inability to determine surrounding
code. As a list, there will always be three elements. Each element
represents a line surrounding the message's location.

The middle element of the context list represents the line of interest. If
an element of the context list is null, that line does not exist. For
instance, if an error is on the first line of a file, the context might
look like:

```js
[
    null,
    "This is the line with the error",
    "This is the second line of the file"
]
```

The same rule applies for the end of a file and for files with only one line.


## Testing

Unit tests can be run with 

```bash
nosetests
```


## Updating

Some regular maintenance needs to be performed on the validator in order to
make sure that the results are accurate.

### JS Libraries

A list of JS library hashes is kept to allow for whitelisting. This must be
regenerated with each new library version. To update:

```bash
cd extras
mkdir jslibs
python jslibfetcher.py
python build_whitelist.py jslibs/
# We keep a special hash for testing
echo "e96461c6c19608f528b4a3c33a032b697b999b62" >> whitelist_hashes.txt
mv whitelist_hashes.txt ../validator/testcases/hashes.txt
```

To add new libraries to the mix, edit `extras/jslibfetcher.py` and add the
version number to the appropriate tuple.

