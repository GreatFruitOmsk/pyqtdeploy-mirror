What is :program:`pyqtdeploy`?
==============================

:program:`pyqtdeploy` is a tool that, in conjunction with other tools provided
with Qt, enables the deployment of PyQt4 and PyQt5 applications written with
Python v2.7 or Python v3.3 or later.  It supports deployment to desktop
platforms (Linux, Windows and OS X) and to mobile platforms (iOS and Android).

Normally you would create statically compiled versions of the Python
interpreter library, any third party extension modules, PyQt and Qt.  This way
your application has no external dependencies.  In fact this approach is
required when deploying to iOS.  However there is nothing to stop you using
shared versions of any of these components in order to reduce the size of the
application, but at the cost of increasing the complexity of the deployment.

:program:`pyqtdeploy` itself requires PyQt5 and Python v3.2 or later.

:program:`pyqtdeploy` works by taking the individual modules of a PyQt
application, freezing them, and then placing them in a Qt resource file that is
converted to C++ code by Qt's :program:`rcc` tool.  Python's standard library
is handled in the same way.

:program:`pyqtdeploy` generates a simple C++ wrapper around the Python
interpreter library that uses the Python import mechanism to enable access to
the embedded frozen modules in a similar way that Python supports the packaging
of modules in zip files.

Finally :program:`pyqtdeploy` generates a Qt ``.pro`` file that describes all
the generated C++ code.  From this Qt's :program:`qmake` tool is used to
generate a platform-specific ``Makefile`` which will then generate a single
executable.  Further Qt and/or platform specific tools can then be used to
convert the executable to a platform specific deployable package.

When run :program:`pyqtdeploy` presents a GUI that allows the modules that make
up the application to be specified, along with the PyQt components that the
application requires and the parts of the Python standard library that should
also be included.  This information is stored in a :program:`pyqtdeploy`
project file.

A companion program :program:`pyqtdeploycli` can be run from the command line
(or a shell script or batch file) to generate the C++ code from a project file.
:program:`pyqtdeploycli` also provides support for compiling certain packages
(e.g. Python itself and PyQt) both natively and cross-compiling by providing
configuration files that can be used by those package's build systems.

:program:`pyqtdeploy` does not perform auto-discovery of Python standard
library modules or third party modules to be included with the application.
You must specify these yourself.  However it does understand the
inter-dependencies within the standard library, so you only need to specify
those packages that your application explicitly imports.


Author
------

:program:`pyqtdeploy` is copyright (c) Riverbank Computing Limited.  Its
homepage is http://www.riverbankcomputing.com/software/pyqtdeploy/.

Support may be obtained from the PyQt mailing list at
http://www.riverbankcomputing.com/mailman/listinfo/pyqt


License
-------

:program:`pyqtdeploy` is released under the BSD license.


Installation
============

:program:`pyqtdeploy` can be downloaded and installed from
`PyPi <http://pypi.python.org/pypi/pyqtdeploy/>`_::

    pip3 install pyqtdeploy

:program:`pyqtdeploy` requires
`PyQt5 <http://www.riverbankcomputing.com/software/pyqt/download5>`_ to be
installed.  This is not installed automatically.
