from fnmatch import fnmatch as fnm

from . import register_test

# Detect blacklisted files based on their extension.
blacklisted_extensions = ("dll", "exe", "dylib", "so", "sh", "class")

blacklisted_magic_numbers = (
        (0x4d, 0x5a),  # EXE/DLL
        (0x5a, 0x4d),  # Alternative for EXE/DLL
        (0x7f, 0x45, 0x4c, 0x46),  # UNIX elf
        (0x23, 0x21),  # Shebang (shell script)
        (0xca, 0xfe, 0xba, 0xbe),  # Java + Mach-O (dylib)
        (0xca, 0xfe, 0xd0, 0x0d),  # Java (packed)
        (0xfe, 0xed, 0xfa, 0xce),  # Mach-O
        (0x46, 0x57, 0x53),  # Uncompressed SWF
        (0x43, 0x57, 0x53),  # ZLIB compressed SWF
)

# If there are more than 10 .class files in a package, it is flagged as a Java
# archive file.
JAVA_JAR_THRESHOLD = 10


@register_test(tier=1)
def test_blacklisted_files(err, xpi_package=None):
    "Detects blacklisted files and extensions."

    flagged_files = []

    for name in xpi_package:
        file_ = xpi_package.info(name)
        # Simple test to ensure that the extension isn't blacklisted
        extension = file_["extension"]
        if extension in blacklisted_extensions:
            # Note that there is a binary extension in the metadata
            err.metadata["contains_binary_extension"] = True
            flagged_files.append(name)
            continue

        # Perform a deep inspection to detect magic numbers for known binary
        # and executable file types.
        zip = xpi_package.zf.open(name)
        bytes = tuple([ord(x) for x in zip.read(4)])  # Longest is 4 bytes
        if [x for x in blacklisted_magic_numbers if bytes[0:len(x)] == x]:
            # Note that there is binary content in the metadata
            err.metadata["contains_binary_content"] = True
            err.warning(
                err_id=("testcases_packagelayout",
                        "test_blacklisted_files",
                        "disallowed_file_type"),
                warning="Flagged file type found",
                description=["A file was found to contain flagged content "
                             "(i.e.: executable data, potentially "
                             "unauthorized scripts, etc.).",
                             u"The file \"%s\" contains flagged content" %
                                 name],
                filename=name)

    if flagged_files:
        # Detect Java JAR files:
        if (sum(1 for f in flagged_files if f.endswith(".class")) >
                JAVA_JAR_THRESHOLD):
            err.notice(
                err_id=("testcases_packagelayout",
                        "test_blacklisted_files",
                        "java_jar"),
                notice="Java JAR file detected.",
                description="A Java JAR file was detected in the add-on.",
                filename=xpi_package.filename)
        else:
            err.warning(
                err_id=("testcases_packagelayout",
                        "test_blacklisted_files",
                        "disallowed_extension"),
                warning="Flagged file extensions found.",
                description=["Files whose names end with flagged extensions "
                             "have been found in the add-on.",
                             "The extension of these files are flagged because "
                             "they usually identify binary components. Please "
                             "see "
                             "http://addons.mozilla.org/developers/docs/"
                                 "policies/reviews#section-binary"
                             " for more information on the binary content "
                             "review process.",
                             "\n".join(flagged_files)],
                filename=name)


@register_test(tier=1)
def test_layout_all(err, xpi_package):
    """Tests the well-formedness of extensions."""

    package_namelist = list(xpi_package.zf.namelist())
    package_nameset = set(package_namelist)
    if len(package_namelist) != len(package_nameset):
        err.error(
            err_id=("testcases_packagelayout", "test_layout_all",
                    "duplicate_entries"),
            error="Package contains duplicate entries",
            description="The package contains multiple entries with the same "
                        "name. This practice has been banned. Try unzipping "
                        "and re-zipping your add-on package and try again.")