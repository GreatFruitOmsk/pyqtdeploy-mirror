The :mod:`pdytools` Module
==========================

.. module:: pdytools

Every deployed application is able to import the :mod:`pdytools` module.  This
enables the application to determine if it is running as a deployed application
and, if necessary, to change its behaviour accordingly.

.. data:: hexversion

    This is the version number of :program:`pdytools` encoded as a single
    (non-zero) integer.  The encoding used is the same as that used by
    :data:`sys.hexversion`.

Deployed applications also follow the convention of other deployment tools of
defining an attribute called :data:`frozen` in the :mod:`sys` module.
