The Command Line
================

.. program:: pyqtdeploy

:program:`pyqtdeploy`
---------------------

:program:`pyqtdeploy` takes a single optional argument which is the name of a
project file to edit as follows::

    pyqtdeploy myproject.pdy

By convention project files have a ``.pdy`` extension.

This will open the ``myproject.pdy`` project creating it if necessary.


.. program:: pyqtdeploy-build

:program:`pyqtdeploy-build`
---------------------------

:program:`pyqtdeploy-build` generates the target-specific source code,
including the :program:`qmake` ``.pro`` files, needed to create the
application.  The next step in the full build process would be to run
:program:`qmake`.

The full set of command line options is:

.. option:: -h, --help

    This will display a summary of the command line options.

.. option:: --build-dir DIR

    ``DIR`` is the name of the directory where all the application source code
    will be placed.  The default value is ``build-`` followed by a
    target-specific suffix.

.. option:: --include-dir DIR

    ``DIR`` is the name of the directory containing the target Python
    installation's ``Python.h`` file.  It overrides any value specified in the
    project file.

.. option:: --interpreter EXECUTABLE

    ``EXECUTABLE`` is the **host** Python interpreter used to compile all of
    the Python modules used by the application.  It overrides any value
    specified in the project file.

.. option:: --no-clean

    Normally the build directory is deleted and re-created before starting a
    new build.  Specifying this option leaves any existing build directory as
    it is before starting a new build.

.. option:: --opt LEVEL

    ``LEVEL`` is the level of optimisation performed when freezing Python
    source files:

    0 - no optimisation is done

    1 - ``assert`` statements are removed

    2 - ``assert`` statements and docstrings are removed.

    The default is ``2``.

.. option:: --python-library LIB

    ``LIB`` is the name of the target Python interpreter library.  It overrides
    any value specified in the project file.

.. option:: --resources NUMBER

    ``NUMBER`` is the number of Qt ``.qrc`` resource files that are generated.
    On Windows, MSVC cannot cope with very large resource files and complains
    of a lack of heap space.  If you run into this problem then try increasing
    the the number of resource files generated.

.. option:: --source-dir DIR

    ``DIR`` is the name of the directory containing the Python source code.  It
    overrides any value specified in the project file.

.. option:: --standard-library-dir DIR

    ``DIR`` is the name of the directory containing the target Python
    interpreter's standard library.  It overrides any value specified in the
    project file.

.. option:: --sysroot DIR

    ``DIR`` is the name of the system image root directory.  The
    :envvar:`SYSROOT` environment variable is set to ``DIR`` during the build.

.. option:: --target TARGET

    ``TARGET`` is the target architecture.  By default the host architecture is
    used.  The full architecture consists of the platform (``android``,
    ``ios``, ``linux``, ``macos`` or ``win``) and the target word size
    separated by a ``-``.  For example ``android-32``, ``macos-64``.  Note that
    not all platform/word size combinations are supported.

.. option:: --quiet

    This specifies that progress messages should be disabled.

.. option:: --verbose

    This specifies that additional progress messages should be enabled.

.. option:: -V, --version

    This specifies that the version number should be displayed on ``stdout``.
    The program will then terminate.

.. option:: project

    ``project`` is the name of the project file created with
    :program:`pyqtdeploy`.


.. program:: pyqtdeploy-sysroot

:program:`pyqtdeploy-sysroot`
-----------------------------

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
