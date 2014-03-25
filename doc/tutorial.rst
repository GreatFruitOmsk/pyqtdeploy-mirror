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
    specifies the list of *glob*-style patterns that are applied to the scanned
    files and directories.  Those items that match are then completely ignored.
    To edit the list just double-click on the entry to modify or delete.  To
    add a new entry just double-click the list after the last entry.


Defining the PyQt Modules
-------------------------

The tab for defining the PyQt modules used by the application is shown below.

.. image:: /images/pyqt_modules_tab.png
    :align: center

TODO


Defining the Standard Library Packages
--------------------------------------

The tab for defining the Python standard library packages used by the
application is shown below.

.. image:: /images/stdlib_packages_tab.png
    :align: center

TODO


Defining the ``site-packages`` Packages
---------------------------------------

The tab for defining the ``site-packages`` packages used by the application is
shown below.

.. image:: /images/site_packages_tab.png
    :align: center

TODO


Defining the Extension Modules
------------------------------

The tab for defining the C extension modules used by the application is shown
below.

.. image:: /images/extension_modules_tab.png
    :align: center

TODO


Defining the Python Configuration
---------------------------------

The tab for defining the configuration of the Python interpreter is shown
below.

.. image:: /images/python_configuration_tab.png
    :align: center

TODO


Building the C++ Source Code
----------------------------

TODO


Creating a Deployable Package
-----------------------------

TODO
