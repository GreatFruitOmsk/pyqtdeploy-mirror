Tutorial
========

Creating a pyqtdeploy Project
-----------------------------

The first stage of deploying a PyQt5 application is to create a pyqtdeploy
project for it by running::

    pyqtdeploy myproject.pdy

This will create a new project, or open an exiting one if the file
``myproject.pdy`` already exists.  A project is simply a file with a ``.pdy``
extension.

A GUI will be displayed which consists of a ``File`` menu, a ``Build`` menu and
a set of tabbed pages that handle different aspects of the application's
specification.

The ``File`` menu contains the usual set of options to create a new project,
open an existing project, save a project and rename a project.

We will cover the ``Build`` menu in a later section.

In this tutorial we will use the ``wiggly.py`` example that is included with
PyQt.  It consists of a single Python file, rather than a collection of
packages and sub-packages that is typical of a larger application.


Defining the Application Source
-------------------------------

The tab for defining the application source is shown below.

.. image:: /images/application_source_tab.png
    :align: center

**Main script file**
    is used to specify the name of the main Python script of the application
    (actually the only Python script in this example).  The final deployable
    application will have the same name as this script (with the extension
    removed).

    .. note::
        Whenever a file or directory is specified, pyqtdeploy always saves its
        name relative to the directory containing the project file if possible.
        In this particular example the ``wiggly.py`` script is in the same
        directory as the ``wiggly.pdy`` project file.

**Scan application package...**
    is clicked to specify the name of the directory containing the Python
    package that (in more typical cases) implements the majority of the
    application.  The hierachy will be scanned for all files and directories
    that don't match any of the specified exclusions and will be displayed in
    the main area of the tab.  Each file or directory can then be checked if it
    is to be included in the package.  Note that if the main script file is a
    part of the application package then it's entry must be explicitly
    unchecked (i.e. excluded).

    .. note::
        Non-Python (i.e. data) files can also be included in the package.  An
        application typically accesses such files by using the
        :func:`os.path.dirname` function on the ``__file__`` of a module to
        obtain the name of the directory containing the data file.  This
        approach will also work with deployed applications so long as the file
        is accessed using the :class:`~PyQt5.QtCore.QFile` class (rather than
        the standard Python file access functions).

**Include all**
    is clicked to check all scanned files and directories so that they are
    included in the application package.

**Exclude all**
    is clicked to uncheck all scanned files and directories so that they are
    excluded from the application package.

**Exclusions**
    is used to specify the list of *glob*-style patterns that are applied to
    the scanned files and directories.  Those items that match are then
    completely ignored.  To edit the list just double-click on the entry to
    modify or delete.  To add a new entry just double-click the list after the
    last entry.


Defining the PyQt Modules
-------------------------

The tab for defining the PyQt modules used by the application is shown below.

.. image:: /images/pyqt_modules_tab.png
    :align: center

Simply check all the PyQt modules that are used, either implicitly or
explicitly, by the application.  pyqtdeploy does not (yet) automatically handle
inter-module dependencies.

In this example the ``wiggly.py`` script uses the :mod:`~PyQt5.QtCore`,
:mod:`~PyQt5.QtGui` and :mod:`~PyQt5.QtWidgets` modules.


Defining the Standard Library Packages
--------------------------------------

The tab for defining the Python standard library packages used by the
application is shown below.

.. image:: /images/stdlib_packages_tab.png
    :align: center

This tab is used to scan the directory containing the Python interpreter's
standard library.  You then specify which individual modules are needed, either
implicitly or explicitly, by the application.  pyqtdeploy does not (yet)
automatically handle inter-module dependencies.

The ``wiggly.py`` script does not explicitly import any standard Python module
(except for the :mod:`sys` module which is implemented as a builtin).  However,
like any application deployed with pyqtdeploy, the :mod:`importlib`,
:mod:`types` and :mod:`warnings` modules must be included.


Defining the ``site-packages`` Packages
---------------------------------------

The tab for defining the ``site-packages`` packages used by the application is
shown below.

.. image:: /images/site_packages_tab.png
    :align: center

This tab is used to scan the the Python interpreter's ``site-packages``
directory.  You then specify which individual modules are needed, either
implicitly or explicitly, by the application.  pyqtdeploy does not (yet)
automatically handle inter-module dependencies.

The ``wiggly.py`` script does not use any third-party Python packages.


Defining the Extension Modules
------------------------------

The tab for defining the C extension modules used by the application is shown
below.

.. image:: /images/extension_modules_tab.png
    :align: center

This tab is used to specify any third-party C extension modules that will be
statically linked into the Python interpreter library.  For each extension
module its name and the directory containing it must be specified.  On Windows
an extension module will have a ``.lib`` filename suffix.  The suffix will be
``.a`` on most other platforms.

To edit the list just double-click on the entry to modify or delete.  To add a
new entry just double-click the list after the last entry.

The ``wiggly.py`` script does not use any third-party C extension modules.


Defining the Python Configuration
---------------------------------

The tab for defining the configuration of the Python interpreter is shown
below.

.. image:: /images/python_configuration_tab.png
    :align: center

**Host interpreter**
    is used to specify the **host** Python interpreter used to compile all of
    the Python modules used by the application.  This must be the same version
    as the **target** Python installation to ensure that the compiled bytecode
    can be executed by the deployed application.  (Of course if you are not
    cross-compiling the application then the host and target Python
    installations are the same.)

**Target include directory**
    is used to specify the name of the directory containing the target Python
    installation's ``Python.h`` file.

**Target Python library**
    is used to specify the name of the target Python interpreter library.

**Target standard library directory**
    is used to specify the name of the directory containing the target Python
    interpreter's standard library.


Building the C++ Source Code
----------------------------

Once all the relevant information has been specified the application source
code and :program:`qmake` ``.pro`` file can be generated.  This can be done
from the GUI by selecting the ``Build Project...`` option of the ``Build``
menu.  You will then be asked for the name of an existing directory.
pyqtdeploy will then create all the necessary files in that directory.

The project can also be built from the command line by specifying the
:option:`--build` with the name of an existing directory to pyqtdeploy.  For
example::

    pyqtdeploy --build builddir wiggly.pdy

You may also specify the :option:`--verbose` option which will display a
series of progress messages.


Creating a Deployable Package
-----------------------------

The build directory now contains the source of (as far as :program:`qmake` is
concerned) the source of conventional Qt based C++ application.  To convert
this into a deployable application you must follow the appropriate Qt
documentation for compiling and packaging for your target platform.

For desktop platforms this is probably as simple as running :program:`qmake`
followed by :program:`make` (or :program:`nmake` on Windows).

.. note::
    Make sure the version of :program:`qmake` used is the same as the one used
    to build PyQt.

For mobile platforms this will be considerably more complicated.
