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

TODO - describe what comes as standard

TODO - building a spec file from scratch


The :program:`pyqt-demo` Sysroot
--------------------------------

TODO - walk through the demo spec


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
    leaves the build directory as it is to make debugging component plugins
    easier.

.. option:: --options

    This causes the configurable options of each component specified in the
    JSON file to be displayed on ``stdout``.  The program will then terminate.

.. option:: --plugin-dir DIR

    ``DIR`` is added to the list of directories that are searched for component
    plugins.  It may be used more than once to search multiple directories.
    All directories specified in this way will be searched before those
    directories (internal to :program:`pyqtdeploy-sysroot`) searched by
    default.

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
        that match a number of patterns.  If the destination directory already
        exists then it is first removed.  Any errors are handled automatically.

        :param str src: is the name of the source directory.
        :param str dst: is the name of the destination directory.
        :param list[str] ignore: is an optional sequence of patterns that
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

        :param str name: is the name of the directory
        :param bool empty: ``True`` if an existing directory should be emptied.

    .. py:method:: decode_version_nr(version_nr)

        An encoded version number is decoded to a 3-tuple of major version,
        minor version and maintenance version.

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

        :param str version_str] is the version number to parse.
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

    .. py:attribute:: target_qt_dir

        The name of the root directory of the target architecture Qt
        installation.

    .. py:attribute:: target_sitepackages_dir

        The name of the ``site-packages`` directory for the target
        architecture.

    .. py:attribute:: target_src_dir

        The name of the directory where source files can be found.  Note that
        these are sources left by components for the use of other components
        and not the sources used to build a component.

    .. py:method:: unpack_archive(archive, chdir=True)

        An archive (i.e. a ``.tar.gz`` or ``.zip`` file) is unpacked in the
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
