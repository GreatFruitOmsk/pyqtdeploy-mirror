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


.. program:: pyqtdeploycli

:program:`pyqtdeploycli`
------------------------

:program:`pyqtdeploycli` implements a number of modes of operation that are
usually used in automated build scripts.  These modes are invoked by specifying
an *action* as the only positional argument on the command line.  The behaviour
of an action may be modified by additional command line options.

The supported actions are:

.. cmdoption:: build

    This will build all the source code, include the :program:`qmake` ``.pro``
    files, needed to create the application.  The next step in the full build
    process would be to run :program:`qmake`.

.. cmdoption:: configure

    This will create a configuration file for compiling a particular package
    for a particular target platform.  The configuration file is used by the
    package's build system to create the package's Python bindings.

    Configuration files are intended as a basis which will be fine for most
    cases.  However you should check that they are appropriate for your
    particular case and modify them if necessary.

.. cmdoption:: install

    .. versionadded:: 1.2

    This will compile (if necessary) and install a particular package for a
    particular target platform.  It is assumed that the recommended directory
    structure described in :ref:`ref-directory-structure` is being used.

    At the moment only the ``python`` package for the ``win`` target is
    supported.  It is assumed that you have installed Python using one of the
    Windows installers from ``python.org``.

.. cmdoption:: show-packages

    This will display a list of packages that :program:`pyqtdeploycli` can
    create configuration files for.

.. cmdoption:: show-targets

    This will display a list of targets that :program:`pyqtdeploycli` can
    create configuration files for.

.. cmdoption:: show-version

    This will display the version number.

The full set of command line options is:

.. cmdoption:: -h, --help

    This will display a summary of the command line actions and options.

.. cmdoption:: --android-api LEVEL

    .. versionadded:: 1.3

    When used with the :option:`configure` action to configure the ``python``
    package for the ``android`` target this specifies the Android API level.
    The default value is obtained from the value of the
    :envvar:`ANDROID_NDK_PLATFORM` environment variable.  If this is not set
    then ``9`` is used which is the default level used by Qt.

.. cmdoption:: --disable-patches

    .. versionadded:: 1.2

    When used with the :option:`configure` action to configure the ``python``
    package this specifies that the Python source code will not be patched.
    The default is to enable the patching of the Python source code for Android
    based targets.  Use this option when you want to apply your own set of
    patches, or if you are using an NDK (such as `CrystaX NDK
    <https://www.crystax.net>`__) that doesn't require the Python source code
    to be patched at all.

.. cmdoption:: --enable-dynamic-loading

    When used with the :option:`configure` action to configure the ``python``
    package this specifies that the Python interpreter will have dynamic
    loading enabled.  The default is to disable dynamic loading.

.. cmdoption:: --include-dir

    .. versionadded:: 1.2

    When used with the :option:`build` action this specifies the name of the
    directory containing the target Python installation's ``Python.h`` file.
    It overrides any value specified in the project file.

.. cmdoption:: --interpreter

    .. versionadded:: 1.2

    When used with the :option:`build` action this specifies the **host**
    Python interpreter used to compile all of the Python modules used by the
    application.  It overrides any value specified in the project file.

.. cmdoption:: --opt LEVEL

    When used with the :option:`build` action this specifies the level of
    optimisation performed when freezing Python source files:

    0 - no optimisation is done

    1 - ``assert`` statements are removed

    2 - ``assert`` statements and docstrings are removed.

    The default is ``2``.

.. cmdoption:: --output OUTPUT

    When used with the :option:`build` action this specifies the name of the
    build directory where all the application source code will be placed.  By
    default the directory defined in the project file is used.

    When used with the :option:`configure` action this specifies the name of
    the configuration file that is created.  By default the file is called
    ``package-target.cfg`` (where *package* is the name of the package and
    *target* is the name of the target platform) and placed in the current
    directory.

.. cmdoption:: --package PACKAGE

    This is required by the :option:`configure` and :option:`install` actions
    to specify the package.

.. cmdoption:: --project FILE

    This is required by the :option:`build` action to specify the project file.

.. cmdoption:: --python-library

    .. versionadded:: 1.2

    When used with the :option:`build` action this specifies the name of the
    target Python interpreter library.  It overrides any value specified in the
    project file.

.. cmdoption:: --resources NUMBER

    When used with the :option:`build` action this specifies the number of Qt
    ``.qrc`` resource files that are generated.  On Windows, MSVC cannot cope
    with very large resource files and complains of a lack of heap space.  If
    you run into this problem then try increasing the the number of resource
    files generated.

.. cmdoption:: --source-dir

    .. versionadded:: 1.2

    When used with the :option:`build` action this specifies the name of the
    directory containing the Python source code.  It overrides any value
    specified in the project file.

.. cmdoption:: --standard-library-dir

    .. versionadded:: 1.2

    When used with the :option:`build` action this specifies the name of the
    directory containing the target Python interpreter's standard library.  It
    overrides any value specified in the project file.

.. cmdoption:: --sysroot

    .. versionadded:: 1.2

    When used with the :option:`install` action this specifies the name of the
    system image root directory as recommended in
    :ref:`ref-directory-structure`.

.. cmdoption:: --system-python VERSION

    .. versionadded:: 1.2

    When used with the :option:`install` action to install the ``python``
    package this specifies the version number of Python to use.  Only the major
    and minor version numbers need be specified (e.g. ``3.5``).

.. cmdoption:: --target TARGET

    This is used with the :option:`configure` and :option:`install` actions to
    specify the target platform.  By default the host platform is used.  The
    full target consists of the base target and an optional target variant
    (usually related to the target's word size).  The supported base targets
    are ``linux``, ``win``, ``osx``, ``ios`` and ``android``.  The
    :option:`show-targets` action will list the supported targets including the
    target variants.

.. cmdoption:: --quiet

    This is used with the :option:`build` action to specify that progress
    messages should be disabled.

.. cmdoption:: --verbose

    This is used with the :option:`build` action to specify that additional
    progress messages should be enabled.


Examples
--------

::

    pyqtdeploycli --output /tmp/build --project myproject.pdy --quiet build

The code for the application described by the ``myproject.pdy`` project file
will be created in the ``/tmp/build`` directory.  All progress messages will be
disabled.

::

    pyqtdeploycli --package pyqt5 configure

If this command was run on a Linux system then a configuration file for
building PyQt5 for Linux, called ``pyqt5-linux.cfg``, would be created in the
current directory.

::

    pyqtdeploycli --package pyqt4 --target android configure

A configuration file for building PyQt4 for Android, called
``pyqt4-android.cfg`` will be created in the current directory.

::

    pyqtdeploycli --output /tmp/pyqt.config --package pyqt5 --target ios configure

A configuration file for building PyQt5 for iOS, called ``pyqt.config`` will be
created in the ``/tmp`` directory.
