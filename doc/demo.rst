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
of the source code itself.

Throughout the rest of this documentation the demo will be used as a working
example which we will look at in detail.

.. note::
    It is recommended that, at first, you use the same versions (as specified
    in ``sysroot.json``) of the different component packages shown above.  Only
    when you have those working should you then use the versions that you
    really want to use.  This will require you to modify ``sysroot.json``
    and/or ``pyqt-demo.pdy``.


Building the Demo
-----------------

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


Android
-------

.. image:: /images/pyqt-demo-android-32.png
    :align: center

**Host platform used:** macOS Mojave (v10.14.4)

**Development tools used:** NDK r19c, SDK v26.1.1

**Python SSL support implemented:** dynamically linked bundled OpenSSL.

**Qt SSL support implemented:** dynamically linked bundled OpenSSL.

**Environment:** ``ANDROID_NDK_PLATFORM=android-24``


iOS
---

.. image:: /images/pyqt-demo-ios-64.png
    :align: center

**Host platform used:** macOS Mojave (v10.14.4)

**Development tools used:** Xcode v10.2.1

**Python SSL support implemented:** none.

**Qt SSL support implemented:** dynamically linked Secure Transport.


Linux
-----

.. image:: /images/pyqt-demo-linux-64.png
    :align: center

**Host platform used:** RHEL v7.6

**Development tools used:** gcc v4.8.5

**Python SSL support implemented:** dynamically linked system OpenSSL

**Qt SSL support implemented:** dynamically linked system OpenSSL


macOS
-----

.. image:: /images/pyqt-demo-macos-64.png
    :align: center

**Host platform used:** macOS Mojave (v10.14.4)

**Development tools used:** Xcode v10.2.1

**Python SSL support implemented:** statically linked OpenSSL.

**Qt SSL support implemented:** statically linked OpenSSL.


Windows
-------

.. image:: /images/pyqt-demo-win-32.png
    :align: center

**Host platform used:** Windows 10 Pro (v1803)

**Development tools used:** Visual Studio Build Tools 2017 (v15.9.6)

**Python SSL support implemented:** statically linked OpenSSL.

**Qt SSL support implemented:** statically linked OpenSSL.
