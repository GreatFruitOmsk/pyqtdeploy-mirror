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

TODO


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
