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

.. cmdoption:: --enable-dynamic-loading

    When used with the :option:`configure` action to configure the ``python``
    package this specifies that the Python interpreter will have dynamic
    loading enabled.  The default is to disable dynamic loading.

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

    This is required by the :option:`configure` action to specify the package.

.. cmdoption:: --project FILE

    This is required by the :option:`build` action to specify the project file.

.. cmdoption:: --resources NUMBER

    When used with the :option:`build` action this specifies the number of Qt
    ``.qrc`` resource files that are generated.  On Windows, MSVC cannot cope
    with very large resource files and complains of a lack of heap space.  If
    you run into this problem then try increasing the the number of resource
    files generated.

.. cmdoption:: --target TARGET

    This is used with the :option:`configure` action to specify the target
    platform.  By default the host platform is used.  The full target consists
    of the base target and an optional target variant (usually related to the
    target's word size).  The supported base targets are ``linux``, ``win``,
    ``osx``, ``ios`` and ``android``.  The :option:`show-targets` action will
    list the supported targets including the target variants.

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
