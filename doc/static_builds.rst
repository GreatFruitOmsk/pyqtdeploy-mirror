Building Static Packages
========================

.. program:: pyqtdeploycli

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

You must also have an appropriate target Qt installation.  This can be a
regular native Qt installation, a static native Qt installation or a
cross-compiling Qt installation.  For most target platforms it is not necessary
to build a static version of Qt.  The main advantage of a static version is
that it removes an external dependency and so eases deployment.  The main
disadvantage is that it increases the size of the final executable.  The notes
refer to the :program:`qmake` command of your Qt installation as ``qmake``.
You must make sure that you run the correct copy of :program:`qmake` if you
have multiple versions of Qt installed.  When cross-compiling for mobile
devices it is recommended that you use one of the binary installers provided by
The Qt Company.

You must also have a host SIP installation that is the same version as the
target version you will be building.

The notes refer to the make command as ``make``.  If you are using Microsoft
Visual C++ then use ``nmake`` instead.

All packages are built in a target-specific system root directory identified by
the :envvar:`SYSROOT` environment variable (see
:ref:`ref-directory-structure`).  Only those command line options related to
static and cross-compiled builds are specifed - you will probably want to
specify other options to fully configure each package.

The package configuration files created by the :option:`configure` action of
:program:`pyqtdeploycli` assume a default Qt installation, i.e. with features
that would only be enabled by default on the particular platform.  For example,
SSL support is disabled for Windows and Android targets.  If you have
configured your Qt installation differently then you may need to modify the
configuration files appropriately.


Qt
--

To build a static, native version of Qt, change to the Qt source directory
and run::

    ./configure -prefix $SYSROOT/qt-X.Y.Z -static -release -nomake examples
    make
    make install

``X.Y.Z`` is the version number of Qt you are building.

When cross-compiling for mobile devices it is recommended that you use one of
the binary installers provided by The Qt Company.

If your Qt installation is affected by `QTBUG-41204
<https://bugreports.qt-project.org/browse/QTBUG-41204>`_ then you should not
remove your Qt source directory after installing.


Statically Linking the Windows C Runtime Library
................................................

If you wish to statically link the Windows C Library then you need to modify
the :program:`qmake` configuration for your compiler before running
``configure``.

Assuming your compiler is MSVC 2015 then you need to edit the file
``mkspecs\win32-msvc2015\qmake.conf`` in the Qt source directory as follows:

- remove ``embed_manifest_dll`` and ``embed_manifest_exe`` from the ``CONFIG``
  entry

- change all occurrences of ``-MD`` and ``-MDd`` with ``-MT`` and ``-MTd``
  respectively.


Python
------

Windows Targets
...............

On Windows it is strongly recommended that you do not use a static version of
Python (see :ref:`ref-win-dynload`).  Instead you should install the
appropriate version of Python using the installer from ``python.org``.  You
should then use :program:`pyqtdeploycli` as follows to copy the relevant parts
of the installation to the system root directory::

    pyqtdeploycli --sysroot $SYSROOT --package python --system-python X.Y install

``X.Y`` is the version number of Python you are using.  There is no need to
specify the maintenance number.


Other Targets
.............

When targeting Android the default API level is 9.  In order to use a different
API level (e.g. 18) then first set the :envvar:`ANDROID_NDK_PLATFORM`
environment variable to ``android-18``.  It may also be necessary to set the
:envvar:`ANDROID_NDK_TOOLCHAIN_VERSION` if Qt and the Android NDK disagree on
which version of the toolchain to use.

To build a static version of Python for non-Windows targets, change to the
Python source directory and run::

    pyqtdeploycli --package python --target TARGET configure

This will configure Python for a minimal sub-set of standard extension modules.

To complete the build run::

    qmake SYSROOT=$SYSROOT
    make
    make install

See notes [#target]_, [#qmake]_ and [#iphone]_.


sip
---

To build a static version of sip, change to the sip source directory and run::

    pyqtdeploycli --package sip --target TARGET configure
    python configure.py --static --sysroot=$SYSROOT --no-tools --use-qmake --configuration=sip-TARGET.cfg
    qmake
    make
    make install

See notes [#target]_ and [#iphone]_.


PyQt5
-----

To build a static version of PyQt5, change to the PyQt5 source directory and
run::

    pyqtdeploycli --package pyqt5 --target TARGET configure
    python configure.py --static --sysroot=$SYSROOT --no-tools --no-qsci-api --no-designer-plugin --no-qml-plugin --configuration=pyqt5-TARGET.cfg
    make
    make install

See notes [#target]_, [#docstrings]_, [#qmake]_, [#sip]_ and [#iphone]_.


PyQt4
-----

To build a static version of PyQt4, change to the PyQt4 source directory and
run::

    pyqtdeploycli --package pyqt4 --target TARGET configure
    python configure-ng.py --static --sysroot=$SYSROOT --no-tools --no-qsci-api --no-designer-plugin --configuration=pyqt4-TARGET.cfg
    make
    make install

See notes [#target]_, [#docstrings]_, [#qmake]_, [#sip]_ and [#iphone]_.


QScintilla
----------

To build a static version of the QScintilla library, change to the QScintilla
source directory and run::

    cd Qt4Qt5
    qmake CONFIG+=staticlib
    make
    make install

To build a static version of the Python bindings, change to the QScintilla
source directory and run::

    cd Python
    pyqtdeploycli --package qscintilla --target TARGET configure
    python configure.py --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --pyqt=PyQt5 --configuration=qscintilla-TARGET.cfg
    make
    make install

See notes [#target]_, [#docstrings]_, [#qmake]_, [#sip]_ and [#iphone]_.


Qt Charts
---------

To build a static version of the Python bindings, change to the PyQtChart
source directory and run::

    pyqtdeploycli --package pyqtchart --target TARGET configure
    python configure.py --qtchart-version=X.Y.Z --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --configuration=pyqtchart-TARGET.cfg
    make
    make install

Make sure that you specify a value of ``X.Y.Z`` that matches your Qt Charts
installation.

See notes [#target]_, [#docstrings]_, [#qmake]_, [#sip]_, [#qtbug39300]_ and
[#iphone]_.


Qt Data Visualization
---------------------

To build a static version of the Python bindings, change to the
PyQtDataVisualization source directory and run::

    pyqtdeploycli --package pyqtdatavisualization --target TARGET configure
    python configure.py --qtdatavisualization-version=X.Y.Z --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --configuration=pyqtdatavisualization-TARGET.cfg
    make
    make install

Make sure that you specify a value of ``X.Y.Z`` that matches your Qt Data
Visualization installation.

See notes [#target]_, [#docstrings]_, [#qmake]_, [#sip]_, [#qtbug39300]_ and
[#iphone]_.


Qt Purchasing
-------------

To build a static version of the Python bindings, change to the PyQtPurchasing
source directory and run::

    pyqtdeploycli --package pyqtpurchasing --target TARGET configure
    python configure.py --qtpurchasing-version=X.Y.Z --static --sysroot=$SYSROOT --no-sip-files --no-qsci-api --configuration=pyqtpurchasing-TARGET.cfg
    make
    make install

Make sure that you specify a value of ``X.Y.Z`` that matches your Qt Purchasing
installation.

See notes [#target]_, [#docstrings]_, [#qmake]_, [#sip]_, [#qtbug39300]_ and
[#iphone]_.


.. rubric:: Notes

.. [#target] If you are building a native version of the package then you may
    omit the ``--target`` option.

.. [#docstrings] You may also wish to disable the automatic generation of
    docstrings using the ``--no-docstrings`` option.

.. [#qmake] On Windows make sure that the directory containing :program:`qmake`
    is on your :envvar:`PATH`.  On other platforms you may need to specify the
    :program:`qmake` executable using the ``--qmake`` option.

.. [#sip] You may also need to specify the ``sip`` executable using the
    ``--sip`` option.

.. [#qtbug39300] If your Qt installation is affected by `QTBUG-39300
    <https://bugreports.qt-project.org/browse/QTBUG-39300>`_ then you will also
    need to add ``"CONFIG-=android_install"`` to the :program:`qmake` command
    line.

.. [#iphone] :program:`qmake` generates ``Makefile``\s that support iOS devices
    and the simulator.  The default is to build and install for a device.  To
    build and install for the simulator, run the following commands::

        make iphonesimulator
        make iphonesimulator-install

    However, if your Qt installation is affected by `QTBUG-40353
    <https://bugreports.qt-project.org/browse/QTBUG-40353>`_ then the support
    for the ``subdirs`` template in ``.pro`` files is broken in that
    :program:`qmake` does not generate the ``iphonesimulator-install`` target
    in the top-level ``Makefile``.  It is, therefore, necessary to explictly
    install from each of the sub-directories.

    For example, for sip you would run::

        make -C siplib iphonesimulator-install

    For PyQt you would run (for the ``QtCore`` module)::

        make -C QtCore iphonesimulator-install
        make install_init_py install_uic_package
