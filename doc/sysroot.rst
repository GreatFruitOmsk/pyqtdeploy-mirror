.. _ref-building-a-sysroot:

.. program:: pyqtdeploy-sysroot

Building a System Root Directory
================================

:program:`pyqtdeploy-sysroot` is used to create a target-specific system root
directory (*sysroot*) containing the target Python installation and any
third-party components required by the application.  It's use is optional but
highly recommended.

:program:`pyqtdeploy-sysroot` is actually a wrapper around a number of
component plugins.  A plugin, written in Python, is responsible for building
and/or installing (in the sysroot) an individual component.  It would normally
be a Python package or extension module but could just as easily be a
supporting library.

A sysroot is defined by a JSON sysroot specification file.  This contains an
object for each component to build and/or install.  The attributes of an
object determine how the component is configured.  Component and attribute
names may be scoped in the same way as :program:`qmake` variables (described in
:ref:`ref-other-extension-modules`) so that components can be included and
configured on a target by target basis.

The components are built and/or installed in the order in which their objects
appear in the specification file.

An API is provided to allow you to develop your own component plugins.  If you
develop a plugin for a commonly used component then please consider
contributing it so that it can be included in a future release of
:program:`pyqtdeploy`.

TODO - building a spec file from scratch


Standard Component Plugins
--------------------------

TODO - describe what comes as standard


The :program:`pyqt-demo` Sysroot
--------------------------------

TODO - walk through the demo spec


The Command Line
----------------

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

    ``json`` is the name of a JSON specification file that defines each package
    to be included in the sysroot and how each is to be configured.


Writing A Component Plugin
--------------------------

TODO - describe the API
