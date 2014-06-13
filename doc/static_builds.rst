Building Static Packages
========================

In this section we describe how to build static versions of the various
packages that might be part of a deployment.  As this covers cross-compiling
(specifically to support mobile platforms) we refer to *host* and *target*
installations.  All compiling is performed on the *host* system and generates
code that will eventually run on the *target* system.  A *native* build is
where the *host* and *target* systems are the same.

You must have a host Python installation that is the same version as the target
version you will be building.  Other than that there is nothing special about
the host Python installation.  The notes refer to the host Python interpreter
as ``python`` although the actual name you use will depend on your version of
Python and the host platform.

You must also have an appropriate host Qt installation.  This can be a regular
native Qt installation, a static native Qt installation or a cross-compiling
Qt installation.  For most target platforms it is not necessary to build a
static version of Qt.  The main advantage of a static version is that it
removes an external dependency and so eases deployment.  The main disadvantage
is that it increases the size of the final executable.  The notes refer to the
:program:`qmake` command of your Qt installation as ``qmake``.  You must make
sure that you run the correct copy of :program:`qmake` if you have multiple
versions of Qt installed.  When cross-compiling for mobile devices it is
recommended that you use one of the binary installers provided by Digia.

You must also have a host SIP installation that is the same version as the
target version you will be building.

The notes refer to the make command as ``make``.  If you are using Microsoft
Visual C++ then use ``nmake`` instead.

All packages are built in a nominal ``$SYSROOT`` directory.  Only those command
line options related to static and cross-compiled builds are specifed - you
will probably want to specify other options to fully configure each package.


Python
------

TODO

Non-Windows Platforms

To build a static, native version of Python, change to the Python source
directory and run::

    ./configure --prefix $SYSROOT
    make
    make install

Note that a static, native build of Python is the default on these platforms.


Windows

Instructions for creating a static version of the Python library on Windows are
given in the ``readme.txt`` file in the ``PCbuild`` directory of the Python
source code.  However these are rather brief and incomplete.  The following
are, hopefully, a little clearer and will result in a static installation
similar to one created by the standard Python installer.

In the following *XY* refers to the major and minor version of Python, e.g.
``pythonXY.lib``.

If you are building Python v3 then it is assumed you are using Microsoft Visual
C++ 2010.  If you are building Python v2 then it is assumed you are using
Microsoft Visual C++ 2008.

If you are building a 64 bit version of Python then you will need to have an
existing Python installation.  (The standard Python installer is fine.)  You
need to set the :envvar:`HOST_PYTHON` environment variable to the name of the
Python interpreter in that installation, e.g. ``C:\PythonXY\python.exe``.

- Edit the file ``pyconfig.h`` in the ``PC`` directory of the Python source
  package.  Locate the line that defines the preprocessor symbol
  ``HAVE_DYNAMIC_LOADING`` and comment it out.  Locate the line where the
  preprocessor symbol ``Py_NO_ENABLE_SHARED`` is tested and insert the
  following line before it::

    #define Py_NO_ENABLE_SHARED

- Open the ``pcbuild.sln`` file in the ``PCbuild`` directory in Visual C++.
  Ignore any message about solution folders not being supported.

- Set the configuration to ``Release`` from the default ``Debug``.

- If you are building a 64 bit version of Python then set the platform to
  ``x64`` from the default ``Win32``.

- If you are building a 64 bit version of Python v3 then, using the Solution
  Explorer, right click on each project and select ``Properties``.  In the
  dialog select ``Configuration Properties`` and set ``Platform Toolset`` to
  ``Windows7.1SDK``.  (Note that you can select multiple projects and set the
  properties for all selected at the same time.)

- Using the Solution Explorer, right click on  ``pythoncore`` and select
  ``Properties``.  In the dialog select ``Configuration Properties`` and set
  ``Configuration Type`` to ``Static library (.lib)``.

- In the same dialog expand ``C/C++`` and select ``Preprocessor``. Edit
  ``Preprocessor Definitions`` and remove ``Py_ENABLE_SHARED``.

- If you are building a 64 bit version of Python v3 then, in the same dialog,
  expand ``Librarian``, select ``General`` and set ``Target Machine`` to
  ``MachineX64 (/MACHINE:X64)``.

- Using the Solution Explorer, expand ``pythoncore``, right click on
  ``Modules`` and select ``Add`` and then ``Existing Item...``.  Select the
  ``getbuildinfo.c`` file from the ``Modules`` directory of the Python source
  package.  Expand ``Python``, right click on ``dynload_win.c`` and select 
  ``Exclude From Project``.

- Press ``F7`` to build Python.  Some projects will not build unless external
  libraries on which they depend are installed.  If you do not need these then
  you can simply ignore them.

- To install Python in similar locations as they would be by the standard
  Python installer, run the following commands.

  For a 64 bit Python v3, run::

    copy PC\pyconfig.h Include
    copy PCbuild\amd64\python*.exe .
    mkdir libs
    copy PCbuild\amd64\pythonXY.lib libs

  For a 32 bit Python v3, run::

    copy PC\pyconfig.h Include
    copy PCbuild\python*.exe .
    mkdir libs
    copy PCbuild\pythonXY.lib libs

  For a 64 bit Python v2, run::

    copy PC\pyconfig.h Include
    copy PCbuild\amd64\python*.exe .
    mkdir libs
    copy PCbuild\amd64\pythoncore.lib libs\pythonXY.lib

  For a 32 bit Python v2, run::

    copy PC\pyconfig.h Include
    copy PCbuild\python*.exe .
    mkdir libs
    copy PCbuild\pythoncore.lib libs\pythonXY.lib


Qt
--

To build a static, native version of Qt, change to the Qt source directory
and run::

    ./configure -prefix $SYSROOT/qt-X.Y.Z -static
    make
    make install

``X.Y.Z`` is the version number of Qt you are building.

Note that (for current versions of Qt) QtWebkit is not supported in a static
version on all platforms.  Therefore you may wish to add the ``-skip qtwebkit``
option.

When cross-compiling for mobile devices it is recommended that you use one of
the binary installers provided by Digia.


sip
---

To build a static version of sip (either native or cross-compiling), change to
the sip source directory and run::

    pyqtdeploy --package sip --target TARGET configure
    python configure.py --static --sysroot=$SYSROOT --no-tools --use-qmake --configuration sip-TARGET.cfg
    qmake
    make
    make install

See notes [#target]_, [#qmake]_.


PyQt5
-----

To build a static, native version of PyQt5, change to the PyQt5 source
directory and run::

    python configure.py --static --sysroot=$SYSROOT --no-tools --no-sip-files --no-qsci-api --no-designer-plugin --no-qml-plugin
    make
    make install

See notes [#docstrings]_, [#qmake]_, [#sip]_.


PyQt4
-----

To build a static, native version of PyQt4, change to the PyQt4 source
directory and run::

    python configure-ng.py --static --sysroot=$SYSROOT --no-tools --no-sip-files --no-qsci-api --no-designer-plugin
    make
    make install

See notes [#docstrings]_, [#qmake]_, [#sip]_.


QScintilla
----------

To build a static, native version of the QScintilla library, change to the
QScintilla source directory and run::

    cd Qt4/Qt5
    qmake CONFIG+=staticlib
    make
    make install

Before building the QScintilla Python bindings you need to determine the set of
command line options that were passed to sip when building PyQt - specifically
the set of :option:`-t` options and their values.  Normally the
:program:`configure.py` script imports the :mod:`~PyQt5.QtCore` module to
determine these options but a statically built PyQt cannot be imported.

Assuming you are deploying the same versions of Qt and PyQt that you have
developed the application with, then the easiest way to obtain the set of
options is to run::

    python -c "from PyQt5.QtCore import PYQT_CONFIGURATION; print(PYQT_CONFIGURATION['sip_flags'])"

To build a static, native version of the Python bindings, change to the
QScintilla source directory and run::

    cd Python
    python configure.py --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --pyqt=PyQt5 --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install

The above assumes that you are using PyQt5.  If you are using PyQt4 then simply
substitute ``PyQt4`` for ``PyQt5`` in the appropriate places.

See notes [#docstrings]_, [#qmake]_, [#sip]_.


Qt Charts
---------

To build a static, native version of the Qt Charts library, change to the
Qt Charts source directory and run::

    qmake "CONFIG+=release staticlib"
    make
    make install

Before building the Qt Charts Python bindings you need to determine the set of
command line options that were passed to sip when building PyQt.  See the
section describing the building of the QScintilla Python bindings.

To build a static, native version of the Python bindings, change to the
PyQtChart source directory and run::

    python configure.py --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --pyqt=PyQt5 --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install

The above assumes that you are using PyQt5.  If you are using PyQt4 then simply
substitute ``PyQt4`` for ``PyQt5`` in the appropriate places.

See notes [#docstrings]_, [#qmake]_, [#sip]_.


Qt Data Visualization
---------------------

To build a static, native version of the Qt Data Visualization library, change
to the Qt Data Visualization source directory and run::

    qmake "CONFIG+=release staticlib"
    make
    make install

Before building the Qt Data Visualization Python bindings you need to determine
the set of command line options that were passed to sip when building PyQt.
See the section describing the building of the QScintilla Python bindings.

To build a static, native version of the Python bindings, change to the
PyQtDataVisualization source directory and run::

    python configure.py --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install

See notes [#docstrings]_, [#qmake]_, [#sip]_.


.. rubric:: Notes

.. [#docstrings] You may also wish to disable the automatic generation of
    docstrings using the ``--no-docstrings`` option.

.. [#target] If you are building a native version of the package then you may
    omit the ``--target`` option.

.. [#qmake] On Windows make sure that the directory containing :program:`qmake`
    is on your :envvar:`PATH`.  On other platforms you may need to specify the
    :program:`qmake` executable using the ``--qmake`` option.

.. [#sip] You may also need to specify the ``sip`` executable using the
    ``--sip`` option.
