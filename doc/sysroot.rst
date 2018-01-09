.. _ref-building-a-sysroot:

.. program:: pyqtdeploy-sysroot

Building a System Root Directory
================================

:program:`pyqtdeploy-sysroot` is used to create a target-specific system root
directory (*sysroot*) containing the target Python installation and any
third-party components required by the application.  It's use is optional but
highly recommended.

:program:`pyqtdeploy-sysroot` is actually a wrapper around a number of
component plugins.  A plugin, written in Python, is responsible for building
and/or installing (in the sysroot) an individual component.  It would normally
be a Python package or extension module but could just as easily be a
supporting library.

A sysroot is defined by a JSON sysroot specification file.  This contains an
object for each component to build and/or install.  The attributes of an
object determine how the component is configured.  Component and attribute
names may be scoped in the same way as :program:`qmake` variables (described in
:ref:`ref-other-extension-modules`) so that components can be included and
configured on a target by target basis.

The components are built and/or installed in the order in which their objects
appear in the specification file.

An API is provided to allow you to develop your own component plugins.  If you
develop a plugin for a commonly used component then please consider
contributing it so that it can be included in a future release of
:program:`pyqtdeploy`.


Standard Component Plugins
--------------------------

The following component plugins are included as standard with
:program:`pyqtdeploy`.

**openssl**
    This builds the OpenSSL libraries for v1.0.* on Android (dynamically),
    macOS (statically) and Windows (statically).  It requires ``perl`` to be
    installed on :envvar:`PATH`.

**pip**
    This is a meta-component which will install any number of components that
    can be installed by ``pip``.

**pyqt3d**
    This builds a static version of the PyQt3D extension modules for all target
    architectures.  It must be built after PyQt5.

**pyqt5**
    This builds a static version of the PyQt5 extension modules for all
    target architectures.  It must be built after sip and Qt5.

**pyqtchart**
    This builds a static version of the PyQtChart extension module for all
    target architectures.  It must be built after PyQt5.

**pyqtdatavisualization**
    This builds a static version of the PyQtDataVisualization extension module
    for all target architectures.  It must be built after PyQt5.

**pyqtpurchasing**
    This builds a static version of the PyQtPurchasing extension module for
    all target architectures.  It must be built after PyQt5.

**python**
    This will build Python from source, or install it into sysroot from an
    existing installation, for both the host and target architectures.
    Building the host version from source is not supported on Windows.
    Installing the host version from an existing installation is not supported
    on Android or iOS.  The target version of the Python library and extension
    modules built from source will be built statically.  Installing the target
    version from an existing installation is only supported on Windows.  If
    building the target version from source and SSL support is required then
    OpenSSL must be built first.

**qscintilla**
    This builds a static version of the QScintilla library and Python extension
    module for all target architectures.  It must be built after PyQt5.

**qt5**
    This will build a static version of Qt5 from source (but not for the
    Android and iOS targets).  It will also install Qt5 into the sysroot from
    an existing installation created by the standard installer.  When building
    from source on Windows it requires Python v2.7 to be installed (but it does
    not need to be on :envvar:`PATH`).  If building from source and SSL support
    using OpenSSL is required then OpenSSL must be built first.

**sip**
    This builds a static version of the sip extension module for all target
    architectures.  It also builds the sip code generator for the host
    platform.  It must be built after Python.


Creating a Sysroot Specification File
-------------------------------------

The following specification file contains an object for each of the standard
component plugins.  (You can also download a copy of the file from
:download:`here</examples/skeleton.json>`).  No configuration options have been
set for any component.

.. literalinclude:: /examples/skeleton.json

The first object, called ``Description``, is simple a way of including a
comment in the specification and is otherwise ignored.

Using this file, run the following command::

    pyqtdeploy-sysroot --options skeleton.json

You will then see a description of each component's configuration options, the
type of value expected and whether or not a value is required.  You can then
add options as attributes to the appropriate objects to meet your requirements.

If your application does not require all of the standard components then simply
remove the corresponding objects from the specification file.  If your
application requires additional components then you need to create appropriate
component plugins and add corresponding objects to the specification file.

To build a native sysroot (i.e. for the host architecture) from a fully
configured specification file, run::

    pyqtdeploy-sysroot skeleton.json


The :program:`pyqt-demo` Sysroot
--------------------------------

In this section we walk through the sysroot specification file for
:program:`pyqt-demo`, component by component.

openssl
.......

::

    "android|macos|win#openssl": {
        "source":           "openssl-1.0.*.tar.gz",
        "python_source":    "Python-3.*.tar.xz"
    },

The first thing to notice is that the object name is scoped so that the
component is only built for Android, macOS and Windows.  On iOS we choose to
not support SSL from Python and use Qt's SSL support instead (which will use
Apple's Secure Transport).  On Linux we will use the system versions of the
OpenSSL libraries.

The Python binary installer for macOS from `www.python.org <www.python.org>`__
includes a patched version of OpenSSL.  The plugin will apply the same patch to
OpenSSL (on macOS only) if a Python source archive is specified.  The patch
applies to a specific version of OpenSSL - which one depends on the version of
Python being targeted.


qt5
...

::

    "qt5": {
        "android#qt_dir":           "Qt/*/android_armv7",
        "ios#qt_dir":               "Qt/*/ios",

        "linux|macos|win#source":   "qt-everywhere-*-src-5.*.tar.xz",

        "android|linux#ssl":        "openssl-runtime",
        "ios#ssl":                  "securetransport",
        "macos|win#ssl":            "openssl-linked",

        "static_msvc_runtime":      true
    },

The Qt5 component plugin will install Qt into the sysroot from an existing
installation.  We have chosen to do this for Android and iOS by specifying the
``qt_dir`` attribute.

The plugin will build Qt from source if the ``source`` attribute is specified.
We have chosen to do this for Linux, macOS and Windows.

The ``ssl`` attribute specifies how Qt's SSL support is to be implemented.

For Android and Linux we have chosen to dynamically load external OpenSSL
libraries at runtime.  On Android the external libraries are those built by the
``openssl`` component plugin and are bundled automaticallly with the
application executable.  On Linux the external libraries are the system
versions.

For iOS Qt is dynamically linked to the Secure Transport libraries.

For macOS and Windows we have chosen to link against the static OpenSSL
libraries built by the ``openssl`` component plugin.

Finally we have specified that (on Windows) we will link to static versions of
the MSVC runtime libraries.

For simplicity we have chosen to build a full Qt implementation when building
from source.  We could have chosen to use the ``configure_options``,
``disabled_features`` and ``skip`` attributes to tailor the Qt build in order
to reduce the time taken to do the build.


python
......

::

    "python": {
        "build_host_from_source":   false,
        "build_target_from_source": true,
        "source":                   "Python-3.*.tar.xz"
    },

The Python component plugin handles installation for both host and target
architectures.  For the host we choose to use an existing Python installation
rather than build from source.  On Windows the registry is searched for the
location of the existing installation.  On Linux and macOS the Python
interpreter must be on :envvar:`PATH`.  For all target architecures we choose
to build Python from source.

:program:`pyqt-demo` is a very simple application that does not need to
dynamically load extension modules.  If this was needed then the
``dynamic_loading`` attribute would be set to ``true``.


sip
...

::

    "sip": {
        "source":   "sip-4.*.tar.gz"
    },

It is only necessary to specifiy the name of the source archive.


pyqt5
.....

::

    "pyqt5": {
        "android#disabled_features":    [
                "PyQt_Desktop_OpenGL", "PyQt_Printer", "PyQt_PrintDialog",
                "PyQt_PrintPreviewDialog", "PyQt_PrintPreviewWidget"
        ],
        "android#modules":              [
                "QtCore", "QtGui", "QtNetwork", "QtPrintSupport", "QtWidgets",
                "QtAndroidExtras"
        ],

        "ios#disabled_features":        [
                "PyQt_Desktop_OpenGL", "PyQt_MacOSXOnly",
                "PyQt_MacCocoaViewContainer", "PyQt_Printer",
                "PyQt_PrintDialog", "PyQt_PrintPreviewDialog",
                "PyQt_PrintPreviewWidget", "PyQt_Process",
                "PyQt_NotBootstrapped"
        ],
        "ios|macos#modules":            [
                "QtCore", "QtGui", "QtNetwork", "QtPrintSupport", "QtWidgets",
                "QtMacExtras"
        ],

        "linux#modules":                [
                "QtCore", "QtGui", "QtNetwork", "QtPrintSupport", "QtWidgets",
                "QtX11Extras"
        ],

        "win#disabled_features":        ["PyQt_Desktop_OpenGL"],
        "win#modules":                  [
                "QtCore", "QtGui", "QtNetwork", "QtPrintSupport", "QtWidgets",
                "QtWinExtras"
        ],

        "source":                   "PyQt5_*-5.*.tar.gz"
    },

The two attributes used to tailor the build of PyQt5 are ``disabled_features``
and ``modules``.

Unfortunately the list of features that can be disabled is not properly
documented and relate to how Qt5 was configured.  However how
``disabled_features`` is set in the above will be appropriate for most cases.

The ``modules`` attribute is used to specify the names of the individual PyQt
extension modules to be built.  We choose to build only those extension
modules needed by :program:`pyqt-demo`.


pyqt3D
......

::

    "pyqt3d": {
        "source":   "PyQt3D_*-5.*.tar.gz"
    },

It is only necessary to specifiy the name of the source archive.


pyqtchart
.........

::

    "pyqtchart": {
        "source":   "PyQtChart_*-5.*.tar.gz"
    },

It is only necessary to specifiy the name of the source archive.


pyqtdatavisualization
.....................

::

    "pyqtdatavisualization": {
        "source":   "PyQtDataVisualization_*-5.*.tar.gz"
    },

It is only necessary to specifiy the name of the source archive.


pyqtpurchasing
..............

::

    "pyqtpurchasing": {
        "source":   "PyQtPurchasing_*-5.*.tar.gz"
    },

It is only necessary to specifiy the name of the source archive.


qscintilla
..........

::

    "qscintilla": {
        "source":   "QScintilla_*-2.*.tar.gz"
    }

It is only necessary to specifiy the name of the source archive.


The Command Line
----------------

The full set of command line options is:

.. option:: -h, --help

    This will display a summary of the command line options.

.. option:: --component COMPONENT

    ``COMPONENT`` is the name of the component (specified in the JSON file)
    that will be built.  It may be used more than once to build multiple
    components.  If the option is not specified then all components specified
    in the JSON file will be built.

.. option:: --no-clean

    A temporary build directory (called ``build`` in the sysroot) is created in
    order to build the required components.  Normally this is removed
    automatically after all components have been built.  Specifying this option
    leaves the build directory in place to make debugging component plugins
    easier.

.. option:: --options

    This causes the configurable options of each component specified in the
    JSON file to be displayed on ``stdout``.  The program will then terminate.

.. option:: --plugin-dir DIR

    ``DIR`` is added to the list of directories that are searched for component
    plugins.  It may be used more than once to search multiple directories.
    All directories specified in this way will be searched before those
    directories (internal to :program:`pyqtdeploy-sysroot`) that are searched
    by default.

.. option:: --source-dir DIR

    ``DIR`` is the name of the directory containing the source archives used to
    build the components specified in the JSON file.

.. option:: --sysroot DIR

    ``DIR`` is the name of the system root directory.  The default value is
    ``sysroot-`` followed by a target-specific suffix.  Unless the
    :option:`--component` option is specified any existing sysroot will first
    be removed and re-created.

.. option:: --target TARGET

    ``TARGET`` is the target architecture.  By default the host architecture is
    used.

.. option:: --quiet

    This specifies that progress messages should be disabled.

.. option:: --verbose

    This specifies that additional progress messages should be enabled.

.. option:: -V, --version

    This specifies that the version number should be displayed on ``stdout``.
    The program will then terminate.

.. option:: specification

    ``specification`` is the name of a JSON specification file that defines
    each component to be included in the sysroot and how each is to be
    configured.


Writing a Component Plugin
--------------------------

A component plugin is a Python module that defines a sub-class of
:py:class:`pyqtdeploy.ComponentBase`.  The sub-class must re-implement the
:py:meth:`~pyqtdeploy.ComponentBase.build` method and may also
re-implement the :py:meth:`~pyqtdeploy.ComponentBase.configure` method.  It
should also include a class attribute called
:py:attr:`~pyqtdeploy.ComponentBase.options` which is a sequence of
:py:class:`pyqtdeploy.ComponentOption` instances that describe each of the
component's configurable options.  It does not matter what the name of the
class is.

.. py:module:: pyqtdeploy

.. py:class:: ComponentBase

    This is the base class of all component plugins.

    .. py:attribute:: options

        This class attribute is a sequence of
        :py:class:`~pyqtdeploy.ComponentOption` instances describing the
        component's configurable options.

    .. py:method:: build(sysroot)

        This abstract method is re-implemented to build the component.

        :param Sysroot sysroot:  the sysroot being built.

    .. py:method:: configure(sysroot)

        This method is re-implemented to configure the component.  A component
        will always be configured even if it does not get built.

        :param Sysroot sysroot:  the sysroot being configured.

.. py:class:: ComponentOption(name, type=str, required=False, default=None, values=None, help='')

    This class implements an option used to configure the component.  An option
    can be specified as an attribute of the component's object in the sysroot
    specification file.  An instance of the component plugin will contain an
    attribute for each option whose value is that specified in the sysroot
    specification file (or an appropriate default if it was omitted).

    :param str name: the name of the option.
    :param type: the type of a value of the option.
    :type type: ``bool``, ``int``, ``list`` or ``str``
    :param bool required: ``True`` if a value for the option is required.
    :param default: the default value of the option.
    :param values: the possible values of the option.
    :param str help: the help text displayed by the
        :option:`--options <pyqtdeploy-sysroot --options>` option of
        :program:`pyqtdeploy-sysroot`.

.. py:class:: Sysroot

    This class encapsulates a sysroot as seen by a component plugin.  Instances
    are only created by :program:`pyqtdeploy-sysroot` and are passed to the
    plugin when required.

    .. py:attribute:: android_api

        The numerical Android API level to use.

    .. py:attribute:: apple_sdk

        The Apple SDK to use.

    .. py:attribute:: building_for_target

        This is set to ``True`` by the component plugin to configure building
        (i.e. compiling and linking) for the target (rather than the host)
        architecture.  The default value is ``True``.

    .. py:attribute:: components

        The sequence of component names in the sysroot specification.

    .. py:method:: copy_file(src, dst)

        A file is copied.  Any errors are handled automatically.

        :param str src: is the name of the source file.
        :param str dst: is the name of the destination file.

    .. py:method:: copy_dir(src, dst, ignore=None)

        A directory is copied, optionally excluding file and sub-directories
        that match a number of glob patterns.  If the destination directory
        already exists then it is first removed.  Any errors are handled
        automatically.

        :param str src: is the name of the source directory.
        :param str dst: is the name of the destination directory.
        :param list[str] ignore: is an optional sequence of glob patterns that
            specify files and sub-directories that should be ignored.

    .. py:method:: create_file(name)

        A new text file is created and its file object returned.  Any errors
        are handled automatically.

        :param str name: is the name of the file.
        :return: the file object of the created file.

    .. py:method:: create_dir(name, empty=False)

        A new directory is created if it does not already exist.  If it does
        already exist then it is optionally emptied.  Any errors are handled
        automatically.

        :param str name: is the name of the directory.
        :param bool empty: ``True`` if an existing directory should be emptied.

    .. py:method:: decode_version_nr(version_nr)

        An encoded version number is decoded to a 3-tuple of major version,
        minor version and patch version.

        :param int version_nr: is the encoded version number.
        :return: the decoded 3-tuple.

    .. py:method:: delete_dir(name)

        A directory and any contents are deleted.  Any errors are handled
        automatically.

        :param str name: is the name of the directory.

    .. py:method:: error(message, detail='')

        An error message is displayed to the user and the program immediately
        terminates.

        :param str message: is the message.
        :param str detail: is additional detail displayed if the
            :option:`--verbose <pyqtdeploy-sysroot --verbose>` option was
            specified.

    .. py:method:: extract_version_nr(name)

        An encoded version number is extracted from the name of file or
        directory based on common naming standards.

        :param str name: is the name of the file or directory.
        :return: the encoded version number.

    .. py:method:: find_component(name, required=True)

        The :py:class:`~pyqtdeploy.ComponentBase` instance for a component is
        returned.

        :param str name: is the name of the component.
        :param bool required: ``True`` if the component must exist.
        :return: the component instance.

    .. py:method:: find_exe(name)

        The absolute path name of an executable located on :envvar:`PATH` is
        returned.  Any errors are handled automatically.

        :param str name: is the generic executable name.
        :return: the absolute path name of the executable.

    .. py:method:: find_file(name, required=True)

        The absolute path name of a file or directory is returned.  If the name
        is relative then it is assumed t be relative to the directory specified
        by the :option:`--source-dir <pyqtdeploy-sysroot --source-dir>` option.
        If this option has not been specified then the directory containing the
        JSON specification file is used.  The name may be a glob pattern but
        must only identify a single file or directory.

        :param str name: is the name of the file or directory.
        :param bool required: ``True`` if the file or directory must exist.
        :return: the absolute path name of the file or directory.

    .. py:method:: format_version_nr(version_nr)

        An encoded version number is converted to a string.

        :param int version_nr: is the encoded version number.
        :return: the string conversion.

    .. py:method:: get_python_install_path(version_nr=None)

        The name of the directory containing the root of a Python installation
        on Windows is returned.  If an encoded version number is not given then
        :py:attr:`target_py_version_nr` is used.  It must only be called by a
        Windows host.

        :param int version_nr: is the encoded version number.
        :return: the absolute path of the installation directory.

    .. py:attribute:: host_arch_name

        The name of the host architecture.

    .. py:attribute:: host_bin_dir

        The name of the directory where executables built for the host
        architecture should be installed.

    .. py:attribute:: host_dir

        The name of the root directory where components built for the host
        architecture should be installed.

    .. py:method:: host_exe(name)

        A generic executable name is converted to a host-specific version.

        :param str name: is the generic name.
        :return: the host-specific name.

    .. py:attribute:: host_make

        The name of the host ``make`` executable.

    .. py:attribute:: host_platform_name

        The name of the host platform.

    .. py:attribute:: host_pip

        The full path name of the host ``pip`` executable.

    .. py:attribute:: host_python

        The full path name of the host ``python`` executable.

    .. py:attribute:: host_qmake

        The full path name of the host ``qmake`` executable.

    .. py:attribute:: host_sip

        The full path name of the host ``sip`` executable.

    .. py:method:: make_symlink(src, dst)

        A symbolic link is made between source and destination files.  (Note
        that, on Windows, a copy of the source file is made.)

        :param str src: is the name of the source file.
        :param str dst: is the name of the destination link that is created.

    .. py:method:: open_file(name)

        An existing text file is opened and its file object returned.  Any
        errors are handled automatically.

        :param str name: is the name of the file.
        :return: the file object of the opened file.

    .. py:method:: parse_version_nr(version_str)

        Convert a string in the form [M[.m[.p]]] to an encoded version number.

        :param str version_str: is the version number to parse.
        :return: an encoded version number.

    .. py:method:: pip_install(package)

        Install a package using :py:attr:`host_pip` to
        :py:attr:`target_sitepackages_dir`.  The package may refer either to a
        local file or to one to be downloaded from
        `PyPI <https://pypi.python.org/>`__.

        :param str package: is the name of the package.

    .. py:method:: progress(message)

        A progress message is displayed to the user.  It will be suppressed if
        the :option:`--quiet <pyqtdeploy-sysroot --quiet>` option was
        specified.

        :param str message: is the message.

    .. py:method:: run(*args, capture=False)

        An external command is run.  The command's stdout can be optionally
        captured.

        :param \*args: are the name of the command and its arguments.
        :param bool capture: ``True`` if the command's stdout should be
            captured and returned.
        :return: the stdout of the command if requested, otherwise ``None``.

    .. py:attribute:: target_arch_name

        The name of the target architecture.

    .. py:attribute:: target_include_dir

        The name of the directory where header files built for the target
        architecture should be installed.

    .. py:attribute:: target_lib_dir

        The name of the directory where libraries built for the target
        architecture should be installed.

    .. py:attribute:: target_platform_name

        The name of the target platform.

    .. py:attribute:: target_py_include_dir

        The name of the directory where ``Python.h`` built for the target
        architecture can be found.

    .. py:attribute:: target_py_lib

        The name of Python library built for the target architecture.

    .. py:attribute:: target_py_stdlib_dir

        The name of the directory where the Python standard library built for
        the target architecture can be found.

    .. py:attribute:: target_py_version_nr

        The version of Python being targeted.

    .. py:attribute:: target_pyqt_platform

        The name of the target platform as known by PyQt's ``configure.py``.

    .. py:attribute:: target_sip_dir

        The name of the directory where ``.sip`` files built for the target
        architecture can be found.

    .. py:attribute:: target_sitepackages_dir

        The name of the ``site-packages`` directory for the target
        architecture.

    .. py:attribute:: target_src_dir

        The name of the directory where source files can be found.  Note that
        these are sources left by components for the use of other components
        and not the sources used to build a component.

    .. py:method:: unpack_archive(archive, chdir=True)

        An archive (e.g. a ``.tar.gz`` or ``.zip`` file) is unpacked in the
        current directory.

        :param str archive: the name of the archive.
        :param bool chdir: ``True`` if the top level directory of the extracted
            archive should become the new current directory.
        :return: the name of the top level directory of the extracted archive
            excluding any path.

    .. py:method:: verbose(message)

        A verbose progress message is displayed to the user.  It will be
        suppressed unless the
        :option:`--verbose <pyqtdeploy-sysroot --verbose>` option was
        specified.

        :param str message: is the message.

    .. py:attribute:: verbose_enabled

        This is set if the :option:`--verbose <pyqtdeploy-sysroot --verbose>`
        option was specified.
