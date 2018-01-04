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

- ``src`` which is a directory which must contain the source archives of all
  the components that will be built by :program:`pyqtdeploy-sysroot`.

Note that executables can be created for all supported targets without
requiring any changes to any of the above.

When run, the demo displays a GUI table of interesting values.  The demo
running on macOS is shown below.

.. image:: /images/pyqt-demo.png
    :align: center
    :scale: 50

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

Before building the demo you must first populate the ``src`` directory with
appropriate source archives for the following components:

- Python
- Qt
- OpenSSL
- sip
- PyQt5
- PyQt3D
- PyQtChart
- PyQtDataVisualization
- PyQtPurchasing
- QScintilla

If you don't want to build all of these then edit ``sysroot.json`` and remove
the ones you don't want.  (The Python, Qt, sip and PyQt5 sources are required.)

If you are building the demo for either Android or iOS then you must also
install an appropriate version of Qt from an installer from The Qt Company as
:program:`pyqtdeploy-sysroot` does not support building Qt from source for
those platforms.  It should be installed in a directory called ``Qt`` in the
``src`` directory.

To build the demo for the native target, run::

    python build-demo.py

Note that, on Linux, macOS and Windows, Qt will be built from source which can
take a significant amount of time.

``build-demo.py`` has a number of command line options.  To see them, run::

    python build-demo.py --help

Throughout the rest of this documentation the demo will be used as a working
example which we will look at in detail.
