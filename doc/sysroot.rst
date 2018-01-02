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
    :param type type: the type of the option (either ``bool``, ``int``,
        ``list`` or ``str``).
    :param bool required: ``True`` if a value for the option is required.
    :param default: the default value of the option.
    :param values: the possible values of the option.
    :param str help: the help text displayed by the
        :option:`--options <pyqtdeploy-sysroot --options>` option of
        :program:`pyqtdeploy-sysroot`.

.. py:class:: Sysroot

    This class encapsulates a sysroot as seen by a component plugin.
