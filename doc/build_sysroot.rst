Building a System Root Directory
================================

.. program:: build-sysroot.py

Experience shows that a major part of deploying an application is building the
system root directory.  Care must be taken to manage the various different
Python installations that may be involved (e.g the target installation, the
matching host installation, and the host installation used to run
:program:`pyqtdeploy` itself).  Cross-compiling third-party packages is another
substantial area of potential problems, particularly for a Python developer who
may not be familiar with compiling C++ code.

Best practice for building the system root directory is still evolving.  It is
anticipated that future versions of :program:`pyqtdeploy` will offer greater
automated support for the task.  In the meantime the Mercurial repository
contains a Python script called `build-sysroot.py
<https://www.riverbankcomputing.com/hg/pyqtdeploy/file/tip/Developers/build-sysroot.py>`_
which can be used to create a basic system root directory containing a Qt
installation, host and target Python installations and static versions of sip,
PyQt5, PyQtChart, PyQtDataVisualization, PyQtPurchasing and QScintilla.  The
script requires Python v3.5 or later and runs on Windows, OS X and Linux.  It
is a work-in-progress and completely unsupported and its name and command line
interface *will* change.  If you choose to use it then it is recommended that
you maintain your own copy.

The first step is to create the system root directory itself.  This will be
refered to as ``sysroot`` from now on.  You should then create a sub-directory
called ``src``.  You should then copy the source packages of Python, sip and
PyQt5 to the ``src`` directory.  For Qt you can use an existing Qt installation
or build one from source.  For mobile platforms you would typically use one of
the installers from The Qt Company.  If you are building Qt from source then
copy the Qt source package to the ``src`` directory.


:program:`build-sysroot.py`
---------------------------

:program:`build-sysroot.py` will build and install Qt, Python, sip, PyQt5,
PyQtChart, PyQtDataVisualization, PyQtPurchasing and QScintilla as specified
using command line options:

.. cmdoption:: --h, --help

    This will display a summary of the command line options.

.. cmdoption:: --all

    This will build each of Qt, Python, sip, PyQt5, PyQtChart,
    PyQtDataVisualization, PyQtPurchasing and QScintilla in that order.  The
    order is important as there are interdependencies between the individual
    builds.

.. cmdoption:: --build package [package ...]

    This will build one or more of the individual packages in the order
    specified on the command line.  *package* is either ``qt``, ``python``,
    ``sip``, ``pyqt5``, ``pyqtchart``, ``pyqtdatavisualization``,
    ``pyqtpurchasing`` or ``qscintilla``.  You need to allow for the
    interdependencies between the builds.  For example, if you have updated the
    source package for sip then you should rebuild sip and PyQt5.

.. cmdoption:: --clean

    This will deleted the contents of the ``sysroot`` directory before
    building.  The ``src`` directory is left untouched.

.. cmdoption:: --debug

    This will cause debug versions of packages to be built where possible.

.. cmdoption:: --enable-dynamic-loading

    This will enable dynamic loading when building the target Python
    installation.

.. cmdoption:: --qt DIR

    This specifies a directory containing an existing Qt installation which is
    used instead of building Qt from source.  However, you must still use the
    :option:`--build` option.

.. cmdoption:: --sysroot DIR

    This specifies the name of the system root directory to be populated.  If
    it is not specified then the :envvar:`SYSROOT` environment variable is
    used.

.. cmdoption:: --target {android-32, ios-64, linux-32, linux-64, osx-64, win-32, win-64}

    This specifies the target platform.  The default is to build natively (i.e.
    where the host and target platforms are the same).

.. cmdoption:: --use-system-python VERSION

    This specifies that an existing host Python installation with the given
    version is used rather than building it from source.  The version is
    specified as the major and minor numbers separated by a period.  The
    target Python installation is always built from source.


Standard Build Locations
------------------------

When ``sysroot`` has been created with :program:`build-sysroot.py` the
following values should be used in the **Locations** tab.

**Interpreter**
    ``$SYSROOT/bin/python``

**Source directory**
    ``$SYSROOT/build/Python-$PDY_PY_MAJOR.$PDY_PY_MINOR.$PDY_PY_MICRO``

**Include directory**
    ``$SYSROOT/include/python$PDY_PY_MAJOR.$PDY_PY_MINOR``

**Python library**
    ``$SYSROOT/lib/libpython$PDY_PY_MAJOR.$PDY_PY_MINOR.a``

**Standard library directory**
    ``$SYSROOT/lib/python$PDY_PY_MAJOR.$PDY_PY_MINOR``

**Build directory**
    ``build``

**qmake**
    ``$SYSROOT/bin/qmake``
