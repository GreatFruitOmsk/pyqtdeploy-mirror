Tutorial
========

Creating a pyqtdeploy Project
-----------------------------

The first stage of deploying a PyQt application is to create a pyqtdeploy
project for it by running::

    pyqtdeploy myproject.pdy

This will create a new project, or open an exiting one if the file
``myproject.pdy`` already exists.  A project is simply a file with a ``.pdy``
extension.

A GUI will be displayed which consists of a ``File`` menu and a set of tabbed
pages that handle different aspects of the application's specification and
building.

The ``File`` menu contains the usual set of options to create a new project,
open an existing project, save a project and rename a project.

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
        directory as the ``wiggly.pdy`` project file.  Also, whenever a file
        or directory name is entered, pyqtdeploy allows the embedding of
        environment variables which will be expanded when necessary.

**PyQt5**
    is used to specify that the application is a PyQt5 application.

**PyQt4**
    is used to specify that the application is a PyQt4 application.

**Scan...**
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

**Remove all**
    is clicked to remove all the scanned files and directories.

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
If the application is a PyQt4 application then the PyQt4 modules will be shown
instead.

.. image:: /images/pyqt_modules_tab.png
    :align: center

Simply check all the PyQt modules that are used.  pyqtdeploy understands the
dependencies between the different PyQt modules and will automatically check
any additional modules that are required.

In this example only the :mod:`~PyQt5.QtWidgets` module has been explicitly
specified and the :mod:`~PyQt5.QtCore` and :mod:`~PyQt5.QtGui` modules are
automatically included as dependencies.


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
pyqtdeploy will ensure that all modules that it depends on internally are
included so, for example, the above shows that the :mod:`types` and
:mod:`warnings` modules will be included and cannot be changed.


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


Defining File and Directory Locations
-------------------------------------

The tab for defining the locations of various files and directories needed by
pyqtdeploy is shown below.

.. image:: /images/locations_tab.png
    :align: center

**Interpreter**
    is used to specify the **host** Python interpreter used to compile all of
    the Python modules used by the application.  This must be the same version
    as the **target** Python installation to ensure that the compiled bytecode
    can be executed by the deployed application.  (Of course if you are not
    cross-compiling the application then the host and target Python
    installations are the same.)

**Include directory**
    is used to specify the name of the directory containing the target Python
    installation's ``Python.h`` file.

**Python library**
    is used to specify the name of the target Python interpreter library.

**Standard library directory**
    is used to specify the name of the directory containing the target Python
    interpreter's standard library.

**Build directory**
    is used to specify the name of the directory into which all the code
    generated by pyqtdeploy will be placed.  It will be created automatically
    if necessary.

**qmake**
    is used to specify the name of the :program:`qmake` executable that is
    optionally used to build a ``Makefile`` for the application.


Building the Application
------------------------

Normally building an application is done from the command line.  However during
the debugging of the deployment it is convenient to be able to complete the
whole build process (generating code, running :program:`qmake`, running
:program:`make` and running the final application executable) from within the
GUI.  In particular it is useful if you are using trial and error to work out
which Python standard library modules need to be included.

The tab for building the application is shown below.

.. image:: /images/build_tab.png
    :align: center

The main area of the tab shows the output of the various stages of the build.

**Build**
    is clicked to build the application.  The application code and
    :program:`qmake` ``.pro`` file will be generated in the build directory.
    What else is done depends on the additional build steps that have been
    specified.

**Run qmake**
    is clicked to specify that :program:`qmake` will be run after generating
    the application code.  If this is disabled the later build steps will be
    disabled automatically.

**Run make**
    is clicked to specify that :program:`make` (or :program:`nmake` on Windows)
    will be run after running :program:`qmake`.  The earlier build steps will
    be enabled automatically.  If this is disabled the later build steps will
    be disabled automatically.

**Run application**
    is clicked to specify that the application executable will be run after
    running :program:`make`.  The earlier build steps will be enabled
    automatically.

    .. note::
        This only makes sense if you are building natively and not
        cross-compiling.

**Clean before building**
    is clicked to specify that the build directory is deleted and recreated
    before starting a new build.

**Capture console output**
    is clicked to specify that ``console`` is always added to the ``CONFIG``
    variable in the generated ``.pro`` file.  This is only useful on Windows
    and ensures that, even for a GUI application, tracebacks (e.g. about
    missing modules) are captured and displayed.

**Verbose output**
    is clicked specify that additional information is displayed during the
    build process.


Building from the Command Line
------------------------------

The application code and :program:`qmake` ``.pro`` file can also be built from
the command line by specifying the :option:`build`.  For example::

    pyqtdeploy --project wiggly.pdy build

You may also specify the :option:`--output`, :option:`--quiet` and
:option:`--verbose` options.  The :option:`--output` option allows you to
specify a different build directory to the one defined in the project file.
The :option:`--quiet` option will disable any progress messages.  The
:option:`--verbose` option will enable more detailed progress messages.


Creating a Deployable Package
-----------------------------

Assuming you have built the application code and the :program:`qmake` ``.pro``
file, the build directory will now contain the source of (as far as
:program:`qmake` is concerned) a Qt based C++ application.  To convert this
into a deployable application you must follow the appropriate Qt documentation
for compiling and packaging for your target platform.

For desktop platforms this is probably as simple as running :program:`qmake`
followed by :program:`make` (or :program:`nmake` on Windows).

.. note::
    Make sure the version of :program:`qmake` used is the same as the one used
    to build PyQt.

For mobile platforms this will be considerably more complicated.
