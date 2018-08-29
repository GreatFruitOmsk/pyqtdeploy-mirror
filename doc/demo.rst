:program:`pyqt-demo`
====================

The :program:`pyqtdeploy`
`source package <https://pypi.python.org/pypi/pyqtdeploy#downloads>`__ contains
a demo application called :program:`pyqt-demo` which can be found in the
``demo`` sub-directory.

The demo consists of:

- ``pyqt-demo.py`` which is the source code of the demo

- ``sysroot.json`` which is the sysroot specification used by
  :program:`pyqtdeploy-sysroot` to build a target-specific sysroot

- ``pyqt-demo.pdy`` which is the :program:`pyqtdeploy` project file describing
  the application and its components

- ``build-demo.py`` which is a simple script to run
  :program:`pyqtdeploy-sysroot` and :program:`pyqtdeploy-build` to create the
  demo executable

Note that executables can be created for all supported targets without
requiring any changes to any of the above.

When run, the demo displays a GUI table of interesting values including a copy
of the source code itself.  The demo running on macOS is shown below.

.. image:: /images/pyqt-demo.png
    :align: center

.. note::
    It is recommended that, at first, you use the same versions of the
    different component packages shown above.  Only when you have those working
    should you then use the versions that you really want to use.  This may
    require you to modify ``sysroot.json`` and/or ``pyqt-demo.pdy``.

If Python v3.7.0 or later is being used then the demo will use the
:py:mod:`importlib.resources` module from the standard library to read the
source code embedded in the executable.  For earlier versions of Python it uses
PyQt5's :py:class:`~PyQt5.QtCore.QFile` class instead.

The demo chooses to implement support for SSL for both Python and Qt in ways
that differ between target platforms.  These are summarised in the table below.

======== ================================== ===================================
Platform Python                             Qt
======== ================================== ===================================
Android  Bundled dynamically linked OpenSSL Bundled dynamically linked OpenSSL
iOS      Unsupported                        Dynamically linked Secure Transport
Linux    Dynamically linked OpenSSL         Dynamically linked OpenSSL
macOS    Statically linked OpenSSL          Statically linked OpenSSL
Windows  Statically linked OpenSSL          Statically linked OpenSSL
======== ================================== ===================================

To build the demo for the native target, run::

    python build-demo.py

This assumes that the current directory contains appropriate source archives
for the following components:

- Python
- Qt
- OpenSSL
- zlib
- sip
- PyQt5
- PyQt3D
- PyQtChart
- PyQtDataVisualization
- PyQtPurchasing
- QScintilla

You may put the source archives elsewhere and use the ``--sources-dir`` option
to specify their location.  It may be specified any number of times and each
directory will be searched in turn.

If you don't want to build all of these then edit ``sysroot.json`` and remove
the ones you don't want.  (The Python, Qt, sip and PyQt5 sources are required.)

Note that, on Linux, macOS and Windows, Qt will be built from source which can
take a significant amount of time.

If you are building the demo for either Android or iOS then you must also
install an appropriate version of Qt from an installer from The Qt Company as
:program:`pyqtdeploy-sysroot` does not support building Qt from source for
those platforms.  The ``--installed-qt-dir`` option must be used to specify
where Qt is installed.  The directory's name would normally be the version
number of Qt and contain the architecture-specific directories (e.g. ``gcc64``,
``android-arm7``).

``build-demo.py`` has a number of other command line options.  To see them all,
run::

    python build-demo.py --help

Throughout the rest of this documentation the demo will be used as a working
example which we will look at in detail.
