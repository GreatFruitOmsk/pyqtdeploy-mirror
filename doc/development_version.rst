Working with the Development Version
====================================

The source of :program:`pyqtdeploy` is held in a public read-only
`Mercurial <http:mercurial.selenic.com>`_ repository at
http://www.riverbankcomputing.com/hg/pyqtdeploy/.  In order to clone the
repository, run the following command::

    hg clone http://www.riverbankcomputing.com/hg/pyqtdeploy

If you are using a version of Python earlier that v3.4 then you should also
have :mod:`setuptools` installed.

The repository contains a ``Makefile`` which has the following useful targets.

**develop**
    is used to install :program:`pyqtdeploy` in what :mod:`setuptools` calls
    *Development Mode*.

**develop-uninstall**
    is used to uninstall the *Development Mode* version of
    :program:`pyqtdeploy`.

**doc**
    is used to build the HTML version of the documentation. You must have
    `Sphinx <http://sphinx-doc.org>`_ installed.

**wheel**
    is used to create a wheel package.  You must have
    `wheel <http://pypi.python.org/pypi/wheel/>`_ installed.

**sdist**
    is used to create a source distribution package.

**upload**
    is used to create wheel and source distribution packages and to upload them
    to `PyPI <http://pypi.python.org>`_.  You must have
    `twine <http://pypi.python.org/pypi/twine/>`_ installed.

**clean**
    is used to remove any temporary machine generated files that are not part
    of the repository.

If you run :program:`make` without any arguments then you will be given a list
of available targets.

.. note::
    The ``Makefile`` isn't designed to be used on Windows.  It also requires
    both Python v2 and Python v3 to be installed.
