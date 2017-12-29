.. program:: pyqtdeploy-sysroot

Building a System Root Directory
================================

TODO


The Command Line
----------------

:program:`pyqtdeploy-sysroot` is used to create a target-specific system root
directory (*sysroot*) containing the target Python installation and any
external packages and extension modules used by the application.

The full set of command line options is:

.. option:: -h, --help

    This will display a summary of the command line options.

.. option:: --no-clean

    A temporary build directory (called ``build`` in the sysroot) is created in
    order to build the required packages.  Normally this is removed
    automatically after all packages have been built.  Specifying this option
    leaves the build directory as it is to make debugging package plugins
    easier.

.. option:: --options

    This causes the configurable options of each package specified in the JSON
    file to be displayed on ``stdout``.  The program will then terminate.

.. option:: --package PACKAGE

    ``PACKAGE`` is the name of the package (specified in the JSON file) that
    will be built.  It may be used more than once to build multiple packages.
    If the option is not specified then all packages specified in the JSON file
    will be built.

.. option:: --plugin-dir DIR

    ``DIR`` is added to the list of directories that are searched for package
    plugins.  It may be used more than once to search multiple directories.
    All directories specified in this way will be searched before those
    directories (internal to :program:`pyqtdeploy-sysroot`) searched by
    default.

.. option:: --source-dir DIR

    ``DIR`` is the name of the directory containing the source archives used to
    build the packages specified in the JSON file.

.. option:: --sysroot DIR

    ``DIR`` is the name of the system root directory.  The default value is
    ``sysroot-`` followed by a target-specific suffix.  Unless the
    :option:`--package` option is specified any existing sysroot will first be
    removed and re-created.

.. option:: --target TARGET

    ``TARGET`` is the target architecture.  By default the host architecture is
    used.

.. option:: --quiet

    This specifies that progress messages should be disabled.

.. option:: --verbose

    This specifies that additional progress messages should be enabled.

.. option:: -V, --version

    This specifies that the version number should be displayed on ``stdout``.
    The program will then terminate.

.. option:: json

    ``json`` is the name of a JSON text file that specifies each package to be
    included in the sysroot and how they are to be configured.
