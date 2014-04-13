The :mod:`pyqtdeploy` Module
============================

.. module:: pyqtdeploy

Every deployed application is able to import the :mod:`pyqtdeploy` module.
This enables the application to determine if it is running as a deployed
application and, if necessary, change its behaviour accordingly.

.. data:: hexversion

    This is the version number of pyqtdeploy encoded as a single (non-zero)
    integer.  The encoding used is the same as that used by
    :data:`sys.hexversion`.

    The following code fragment shows how this might be used to locate a QML
    file differently in a deployed application::

        import os

        try:
            from pyqtdeploy import hexversion as pyqtdeploy_hexversion
        except ImportError:
            pyqtdeploy_hexversion = 0

        if pyqtdeploy_hexversion:
            qml_url = 'qrc://main.qml'
        else:
            qml_url = os.path.join(os.path.dirname(__file__), 'main.qml')
