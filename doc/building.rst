.. program:: pyqtdeploy

Building the Application
========================

TODO


The Command Line
----------------

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
    used.

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
