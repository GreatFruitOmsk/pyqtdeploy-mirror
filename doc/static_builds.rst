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


Python
------

To build a static, native version of Python, change to the Python source
directory and run::

    ./configure --prefix $ROOT/python
    make
    make install

Note that a static, native build of Python is the default.


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

    $ROOT/python/bin/python3 configure.py --static
    make
    make install


PyQt5
-----

To build a static, native version of PyQt5, change to the PyQt5 source
directory and run::

    $ROOT/python/bin/python3 configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip
    make
    make install


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

    python3 -c "from PyQt5.QtCore import PYQT_CONFIGURATION; print(PYQT_CONFIGURATION['sip_flags'])"

To build a static, native version of the Python bindings, change to the
QScintilla source directory and run::

    cd Python
    $ROOT/python/bin/python3 configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip --pyqt=PyQt5 --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install


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

    $ROOT/python/bin/python3 configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip --pyqt=PyQt5 --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install


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

    $ROOT/python/bin/python3 configure.py --static --qmake=$ROOT/qt/bin/qmake --sip=$ROOT/python/bin/sip --pyqt-sip-flags="$PYQT_SIP_FLAGS"
    make
    make install
