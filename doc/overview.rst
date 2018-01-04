An Overview of the Deployment Process
=====================================

The purpose of :program:`pyqtdeploy` is to convert a Python application, the
Python interpreter, the Python standard library, Python C extension modules,
third-party Python packages and third-party extension modules to a single,
target-specific executable.  Depending on the target the executable may need to
be packaged in some way to be truly deployable.  For example, Android
applications need to be signed and packaged as a ``.apk`` file.  Any such
packaging is outside the scope of :program:`pyqtdeploy`.

While :program:`pyqtdeploy` allows you to create a single executable you are
free to keep components external to the executable if required.

:program:`pyqtdeploy` supports the following target architectures:

- android-32
- ios-64
- linux-64
- macos-64
- win-32
- win-64.

The full architecture name consists of the platform and the word size separated
by a ``-``.  Note that not all platform/word size combinations are supported.

:program:`pyqtdeploy` uses the following parts of Qt:

- :program:`qmake` is the Qt build system that supports cross-compilation to
  multiple targets.

- :program:`rcc` is a utility that converts arbitrary files to C++ data
  structures that implement an embedded filesystem that can be linked as part
  of an application.

- The :program:`QtCore` library implements file access APIs that recognise file
  and directory names that refer to the contents of the embedded filesystem
  created with :program:`rcc`.  :program:`pyqtdeploy` implements import hooks
  that use :program:`QtCore` to allow frozen Python modules to be imported from
  the embedded filesystem just as if they were being imported from an ordinary
  filesystem.

Note that :program:`pyqtdeploy` generated code does not itself use PyQt.
:program:`pyqtdeploy` can be used to deploy non-PyQt applications, including
simple command line scripts.  However, as every deployed application is linked
with the :program:`QtCore` library, you should make sure that you application's
license is compatible with the license of the version of Qt that you are using.

When an application is made up of a number of third-party components (Python
packages and extension modules) it is necessary to have these installed in
defined locations so that they can be found during the build of the
application.  While in some cases it is possible to use an existing Python
installation for this it has a number of disadvantages:

- Different applications may have requirements for different versions of a
  third-party package making it difficult to share the same Python
  installation.

- Your application may require components (including the Python interpreter
  itself) to be configured differently.

- A standard Python installation will contain dynamically linked extension
  modules but you may want to use statically linked versions.

- It cannot be used when targeting a non-native platform.

Experience has shown that it is easier to keep all of these components separate
from any standard Python installation.  A target-specific system root directory
(*sysroot*) can be used to contain appropriately configured and built versions
of all the required components.  If you are developing a number of applications
then it is likely that you will be standardising on the versions of the
components used by those applications.  Therefore you can create a single
sysroot to be used to build all applications.  While the use of a sysroot is
completely optional, it is highly recommended.

The steps required to develop a deployable application are as follows:

- Develop and test the application as normal using a native Python
  installation containing the required third-party components.

- Identify the third-party components that are required and build a
  target-specific sysroot.  See :ref:`ref-building-a-sysroot` to learn how to
  use :program:`pyqtdeploy-sysroot` to do this.

- Create a project file for the application that identifies the application's
  source code and all the components used by the application and their
  locations.  See :ref:`ref-creating-a-project` to learn how to use
  :program:`pyqtdeploy` to do this.

- Freeze the Python modules and generate a :program:`qmake` ``.pro`` file in a
  target-specific build directory.  The ``.pro`` file will reference all of the
  required components in the associated sysroot.  Run :program:`qmake` and then
  :program:`make` to create the application executable.  See
  :ref:`ref-building-an-application` to learn how to use
  :program:`pyqtdeploy-build` to do this.
