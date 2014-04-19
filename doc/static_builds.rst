Building Static Packages
========================

In this section we describe how to build static, native versions of the various
packages that might be part of a deployment.

Depending on the target platform it is not necessary to build static versions
of all packages.  The main advantage of a static version is that it removes an
external dependency and so eases deployment.  The main disadvantage is that it
inceases the size of the final executable.  In reality it probably only makes
sense to consider a non-static version of Qt (given its relatively large size)
and only if you are deploying more that one application or if you know it will
already be installed as dynamic libraries on the target platform.

All packages are built in a nominal ``$ROOT`` directory.  Only those command
line options related to static builds are specifed - you will probably want
to specify other options to fully configure each package.

The notes refer to the Python interpreter as ``$ROOT/python/bin/python`` which
is correct for Python v2 on non-Windows platforms.  If you are using Python v3
(on a non-Windows platform) then use ``$ROOT/python/bin/python3`` instead.  If
you are using Windows then use ``$ROOT\Python-X.Y.Z\python`` where *X.Y.Z* is
the Python version number.

Similarly the notes refer to the SIP code generator as ``$ROOT/python/bin/sip``
which is correct for non-Windows platforms.  If you are using Windows then use
``$ROOT\Python-X.Y.Z\sip.exe`` instead.

Finally, the notes refer to the make command as ``make``.  If you are using
Microsoft Visual C++ then use ``nmake`` instead.


Python
------

Non-Windows Platforms
.....................

To build a static, native version of Python, change to the Python source
directory and run::

    ./configure --prefix $ROOT/python
    make
    make install

Note that a static, native build of Python is the default on these platforms.


Windows
.......

Instructions for creating a static version of the Python library on Windows are
given in the ``readme.txt`` file in the ``PCbuild`` directory of the Python
source code.  However these are rather brief and incomplete.  The following
are, hopefully, a little clearer and will result in a static installation
similar to one created by the standard Python installer.

- Edit the file ``pyconfig.h`` in the ``PC`` directory of the Python source
  package.  Locate the line that defines the preprocessor symbol
  ``HAVE_DYNAMIC_LOADING`` and comment it out.  Locate the line where the
  preprocessor symbol ``Py_NO_ENABLE_SHARED`` is tested and insert the
  following line before it::

    #define Py_NO_ENABLE_SHARED

- Open the ``pcbuild.sln`` file in the ``PCbuild`` directory in Microsoft
  Visual C++.  Ignore any message about solution folders not being supported.

- Set the configuration to ``Release`` from the default ``Debug``.

- Using the Solution Explorer, right click on  ``pythoncore`` and select
  ``Properties``.  In the dialog select ``Configuration Properties`` and set
  ``Configuration Type`` to ``Static library (.lib)`` from the default
  ``Dynamic library (.dll)``.

- In the same dialog expand ``C/C++`` and select ``Preprocessor``. Edit
  ``Preprocessor Definitions`` and remove ``Py_ENABLE_SHARED``.

- Using the Solution Explorer, expand ``pythoncore``, right click on
  ``Modules`` and select ``Add`` and then ``Existing Item...``.  Select the
  ``getbuildinfo.c`` file from the ``Modules`` directory of the Python source
  package.  Expand ``Python``, right click on ``dynload_win.c`` and select 
  ``Exclude From Project``.

- Press ``F7`` to build Python.  Some extension modules will not build unless
  external libraries on which they depend are installed.  If you do not need
  these modules then you can simply ignore them.

- To install Python in similar locations as they would be by the standard
  Python installer, run the following commands::

    copy PCbuild\python*.exe .
    copy PC\pyconfig.h Include
    mkdir libs

  If you are building Python v3 then run the following command::

    copy PCbuild\pythonXY.lib libs

  If you are building Python v2 then run the following command::

    copy PCbuild\pythoncore.lib libs\pythonXY.lib

  In the above *XY* is the major and minor version of Python, e.g.
  ``python34.lib``.


Qt
--

To build a static, native version of Qt, change to the Qt source directory
and run::

    ./configure -prefix $ROOT/qt -static
    make
    make install

Note that (for current versions of Qt) QtWebkit is not supported in a static
version on all platforms.  Therefore you may wish to add the ``-skip qtwebkit``
command line option.


sip
---

To build a static, native version of sip, change to the sip source directory
and run::

    $ROOT/python/bin/python configure.py --static
    make
    make install


PyQt5
-----

To build a static, native version of PyQt5, change to the PyQt5 source
directory and run::

    $ROOT/python/bin/python configure.py --no-designer-plugin --no-qml-plugin --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip
    make
    make install

On Windows make sure that the directory containing ``qmake`` is on your
:env:`PATH` and omit the ``--qmake`` option.


PyQt4
-----

To build a static, native version of PyQt4, change to the PyQt4 source
directory and run::

    $ROOT/python/bin/python configure-ng.py --no-designer-plugin --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip
    make
    make install

On Windows make sure that the directory containing ``qmake`` is on your
:env:`PATH` and omit the ``--qmake`` option.


QScintilla
----------

To build a static, native version of the QScintilla library, change to the
QScintilla source directory and run::

    cd Qt4/Qt5
    $ROOT/qt/bin/qmake CONFIG+=staticlib
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
    $ROOT/python/bin/python configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip --pyqt=PyQt5 --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install

The above assumes that you are using PyQt5.  If you are using PyQt4 then simply
substitute ``PyQt4`` for ``PyQt5`` in the appropriate places.

On Windows make sure that the directory containing ``qmake`` is on your
:env:`PATH` and omit the ``--qmake`` option.


Qt Charts
---------

To build a static, native version of the Qt Charts library, change to the
Qt Charts source directory and run::

    $ROOT/qt/bin/qmake "CONFIG+=release staticlib"
    make
    make install

Before building the Qt Charts Python bindings you need to determine the set of
command line options that were passed to sip when building PyQt.  See the
section describing the building of the QScintilla Python bindings.

To build a static, native version of the Python bindings, change to the
PyQtChart source directory and run::

    $ROOT/python/bin/python configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip --pyqt=PyQt5 --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install

On Windows make sure that the directory containing ``qmake`` is on your
:env:`PATH` and omit the ``--qmake`` option.


Qt Data Visualization
---------------------

To build a static, native version of the Qt Data Visualization library, change
to the Qt Data Visualization source directory and run::

    $ROOT/qt/bin/qmake "CONFIG+=release staticlib"
    make
    make install

Before building the Qt Data Visualization Python bindings you need to determine
the set of command line options that were passed to sip when building PyQt.
See the section describing the building of the QScintilla Python bindings.

To build a static, native version of the Python bindings, change to the
PyQtDataVisualization source directory and run::

    $ROOT/python/bin/python configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install

On Windows make sure that the directory containing ``qmake`` is on your
:env:`PATH` and omit the ``--qmake`` option.
