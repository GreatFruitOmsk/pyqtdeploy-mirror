What is pogles?
===============

pogles is a Python package that implements bindings for OpenGL ES v2.0 for
Python v2.3 or later and Python v3.  It comprises three modules:

- :mod:`pogles.gles2` contains the bindings for Open GL ES v2.0 itself.

- :mod:`pogles.egl` contains the bindings for the EGL native platform
  interface.

- :mod:`pogles.platform` contains platform specific bindings for creating
  native windows.  Currently the Raspberry Pi and X11 platforms are supported.
  Usually the X11 platform will be used for development before porting to a
  specific embedded platform.

The full ES and EGL APIs are implemented and given a Pythonic twist where
appropriate - for example errors raise Python exceptions.

Standalone applications may be developed using the :mod:`pogles.gles2` module
with the :mod:`pogles.egl` and :mod:`pogles.platform` modules.  Alternatively
it can be used with a separate framework, e.g.
`PyQt <http://www.riverbankcomputing.com/software/pyqt>`__, that handles the
platform dependencies.


Author
------

pogles is copyright (c) Riverbank Computing Limited.  Its homepage is
http://www.riverbankcomputing.com/software/pogles/.

Support may be obtained from the PyQt mailing list at
http://www.riverbankcomputing.com/mailman/listinfo/pyqt


License
-------

pogles is released under the BSD license.


Installation
============

pogles is implemented using the SIP Python bindings generator which must be
installed first.  SIP is available for all Linux distributions but pogles
requires v4.14.2 or later.  The current version of SIP can be found at
http://www.riverbankcomputing.com/software/sip/download.

pogles itself is available from `PyPi <http://pypi.python.org/pypi/pogles/>`__.
It is installed as a normal Python package::

    python setup.py install

This assumes that the :program:`sip` code generator is on your :envvar:`PATH`.
If it isn't then you need to use the ``--sip`` option to the ``build_ext``
sub-command, for example::

    python setup.py build_ext --sip /path/to/sip install


Building the HTML Documentation
-------------------------------

If you want to build a local copy of the HTML documentation (and you have
Sphinx installed) then run::

    python setup.py build_sphinx


Examples
========

The ``examples`` directory contains a small number of examples that should run
on all supported platforms.

More examples are always welcome.
