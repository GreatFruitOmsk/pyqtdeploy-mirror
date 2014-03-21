What is pyqtdeploy?
===================

pyqtdeploy is a tool that, in conjunction with other tools provided with Qt,
enables the deployment of PyQt5 applications written with Python v3.x.  It
supports deployment to desktop platforms (Linux, Windows and OS/X) and to
mobile platforms (iOS, Android and Windows RT).

pyqtdeploy works by taking the individual modules of a PyQt5 application,
freezing them, and then placing them in a Qt resource file that is converted to
C++ code by Qt's ``rcc`` tool.  Python's standard library is handled in the
same way.

pyqtdeploy generates a simple C++ wrapper around the Python interpreter library
that uses the Python import mechanism to enable access to the embedded frozen
modules in a similar way that Python supports the packaging of modules in zip
files.

Finally pyqtdeploy generates a Qt ``.pro`` file that describes all the
generated C++ code.  From this Qt's ``qmake`` tool is used to generate a
platform-specific ``Makefile`` which will then generate a single executable.
Further Qt and/or platform specific tools can then be used to convert the
executable to a platform specific deployable package.

When run pyqtdeploy presents a GUI that allows the modules that make up the
application to be specified, along with the PyQt5 components that the
application requires and the parts of the Python standard library that should
also be included.  This information is stored in a pyqtdeploy project file.
pyqtdeploy can also be run as a command line tool to generate the C++ code from
a project file.

Normally you would create statically compiled versions of the Python
interpreter library, any third party extension modules, PyQt5 and Qt.  This way
your application has no external dependencies.  In fact this approach is
required when deploying to iOS.  However there is nothing to stop you using
shared versions of any of these components in order to reduce the size of the
application, but at the cost of increasing the complexity of the deployment.

There are some things that pyqtdeploy does not do (although this may change in
future versions):

- It does not perform auto-discovery of Python standard library modules or
  third party modules to be included with the application.  You must explicitly
  specify these yourself.

- It does not provide any help in creating an appropriately compiled Python
  interpreter library.  This is particularly an issue when deploying
  applications to non-native platforms, typically mobile platforms.  The same
  applies to third party extension modules.


Author
------

pyqtdeploy is copyright (c) Riverbank Computing Limited.  Its homepage is
http://www.riverbankcomputing.com/software/pyqtdeploy/.

Support may be obtained from the PyQt mailing list at
http://www.riverbankcomputing.com/mailman/listinfo/pyqt


License
-------

pyqtdeploy is released under the BSD license.


Future Versions
===============

The following enhancements may be included in future versions.  Comments and
requests are welcome.

- Support for Python v2.6 and v2.7.

- Support for PyQt4 (desktop platforms only).

- Support for cross-compilation of the Python interpreter library.

- Support for the auto-discovery of required modules.


Installation
============

pyqtdeploy can be downloaded and installed from
`PyPi <http://pypi.python.org/pypi/pyqtdeploy/>`__::

    pip3 install pyqtdeploy

pyqtdeploy requires
`PyQt5 <http://www.riverbankcomputing.com/software/pyqt/download5>`__ to be
installed.  This is not installed automatically.
