# Copyright (c) 2018, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import glob
import os
import shutil
import sys

from ..file_utilities import (copy_embedded_file as fu_copy_embedded_file,
        create_file as fu_create_file, extract_version as fu_extract_version,
        get_embedded_dir as fu_get_embedded_dir,
        get_embedded_file_for_version as fu_get_embedded_file_for_version,
        open_file as fu_open_file, parse_version as fu_parse_version)
from ..platforms import Architecture, Platform
from ..user_exception import UserException
from ..windows import get_py_install_path

from .specification import Specification


class Sysroot:
    """ Encapsulate a target-specific system root directory. """

    def __init__(self, sysroot_dir, sysroot_json, plugin_dirs, source_dirs, target_arch_name, message_handler):
        """ Initialise the object. """

        self._host = Architecture.architecture()
        self._target = Architecture.architecture(target_arch_name)

        if not sysroot_dir:
            sysroot_dir = 'sysroot-' + self._target.name

        self.sysroot_dir = os.path.abspath(sysroot_dir)
        self._build_dir = os.path.join(self.sysroot_dir, 'build')

        self._specification = Specification(sysroot_json, plugin_dirs,
                self._target)
        self._message_handler = message_handler

        if source_dirs:
            self._source_dirs = [os.path.abspath(s) for s in source_dirs]
        else:
            self._source_dirs = [os.path.dirname(os.path.abspath(sysroot_json))]

        self._target_py_version_nr = None
        self._host_qmake = None

        self._target.configure()
        self._building_for_target = True

    def build_components(self, component_names, no_clean):
        """ Build a sequence of components.  If no names are given then create
        the system image root directory and build everything.  Raise a
        UserException if there is an error.
        """

        # Handle the options now we know they are needed.
        self._specification.parse_options()

        # Allow the components to configure themselves even if they are not
        # being built.
        for component in self.components:
            component.configure(self)

        if component_names:
            components = self._components_from_names(component_names)
        else:
            components = self.components
            self.create_dir(self.sysroot_dir, empty=True)
            os.makedirs(self.host_bin_dir)
            os.makedirs(self.target_include_dir)
            os.makedirs(self.target_lib_dir)
            os.makedirs(self.target_src_dir)

        # Create a new build directory.
        self.create_dir(self._build_dir, empty=True)
        cwd = os.getcwd()

        # Build the components.
        for component in components:
            os.chdir(self._build_dir)
            component.build(self)

        # Remove the build directory if requested.
        os.chdir(cwd)

        if not no_clean:
            # This can fail on Windows (complaining about non-empty
            # directories).  Therefore we just warn that we couldn't do it.
            try:
                self.delete_dir(self._build_dir)
            except UserException as e:
                self.verbose("Warning: " + e.text)

    def show_options(self, component_names):
        """ Show the options for a sequence of components.  If no names are
        given then show the options of all components.  Raise a UserException
        if there is an error.
        """

        if component_names:
            components = self._components_from_names(component_names)
        else:
            components = self.components

        self._specification.show_options(components, self._message_handler)

    def _components_from_names(self, component_names):
        """ Return a sequence of components from a sequence of names. """

        components = []

        for name in component_names:
            for component in self.components:
                if component.name == name:
                    components.append(component)
                    break
            else:
                self.error("unkown component '{0}'".format(name))

        return components

    ###########################################################################
    # The following are part of the public API for component plugins that are
    # distributed as part of pyqtdeploy.  Therefore they are not documented.
    ###########################################################################

    @staticmethod
    def copy_embedded_file(src_name, dst_name, macros={}):
        """ Copy an embedded text file to a destination file.  src_name is the
        name of the source file.  dst_name is the name of the destination file.
        macros is an optional dictionary of key/value string macros and
        instances of each key are replaced by the corresponding value.  A
        UserException is raised if there was an error.
        """

        fu_copy_embedded_file(src_name, dst_name, macros)

    @staticmethod
    def get_embedded_dir(root, *subdirs):
        """ Return a QDir corresponding to an embedded directory.  root is the
        root directory and will be the __file__ attribute of a pyqtdeploy
        module.  subdirs is a sequence of sub-directories from the root.
        Return None if no such directory exists.
        """

        return fu_get_embedded_dir(root, *subdirs)

    @staticmethod
    def get_embedded_file_for_version(version, root, *subdirs):
        """ Return the absolute file name in an embedded directory of a file
        that is the most appropriate for a particular version.  version is the
        encoded version.  root is the root directory and will be the __file__
        attribute of a pyqtdeploy module.  subdirs is a sequence of
        sub-directories from the root.  An empty string is returned if the
        version is not supported.
        """

        return fu_get_embedded_file_for_version(version, root, *subdirs)

    ###########################################################################
    # The following make up the public API to be used by component plugins.
    ###########################################################################

    @staticmethod
    def add_to_path(name):
        """ Add the name of a directory to the start of PATH if it isn't
        already present.  The original PATH is returned.
        """

        original_path = os.environ['PATH']
        path = original_path.split(os.pathsep)

        if name not in path:
            path.insert(0, name)
            os.environ['PATH'] = os.pathsep.join(path)

        return original_path

    @property
    def android_api(self):
        """ The Android API to use. """

        return self._target.platform.android_api

    @property
    def android_ndk_sysroot(self):
        """ The path of the Android NDK's sysroot directory. """

        ndk_root = os.environ['ANDROID_NDK_ROOT']

        return os.path.join(ndk_root, 'platforms',
                'android-{}'.format(self.android_api), 'arch-arm')

    @property
    def android_toolchain_bin(self):
        """ The path of the Android toolchain's bin directory. """

        if self.host_platform_name == 'win':
            self.error(
                    "Windows as an Android development host is not supported")

        ndk_root = os.environ['ANDROID_NDK_ROOT']

        toolchain_version = os.environ.get('ANDROID_NDK_TOOLCHAIN_VERSION')
        if toolchain_version is None:
            self.error(
                    "the ANDROID_NDK_TOOLCHAIN_VERSION environment variable "
                    "must be set to an appropriate value (e.g. '4.9')")

        android_host = '{}-x86_64'.format(
                'darwin' if self.host_platform_name == 'macos' else 'linux')

        return os.path.join(ndk_root, 'toolchains',
                self.android_toolchain_prefix + toolchain_version, 'prebuilt',
                android_host, 'bin')

    @property
    def android_toolchain_prefix(self):
        """ The name of the Android toolchain's prefix. """

        return 'arm-linux-androideabi-'

    @property
    def apple_sdk(self):
        """ The Apple SDK to use. """

        arch = self._target if self._building_for_target else self._host

        return arch.platform.get_apple_sdk(self._message_handler)

    @property
    def building_for_target(self):
        """ This is set if building (ie. compiling and linking) for the target
        architecture.  Otherwise build for the host.  The default is True.
        """

        return self._building_for_target

    @building_for_target.setter
    def building_for_target(self, value):
        """ Set to build (ie. compile and link) for the target architecture.
        Otherwise build for the host.
        """

        if value:
            self._host.deconfigure()
            self._target.configure()
        else:
            self._target.deconfigure()
            self._host.configure()

        self._building_for_target = value

    @property
    def components(self):
        """ The sequence of component names in the sysroot specification. """

        return self._specification.components

    def copy_file(self, src, dst):
        """ Copy a file. """

        self.verbose("Copying {0} to {1}".format(src, os.path.abspath(dst)))

        try:
            shutil.copy(src, dst)
        except Exception as e:
            self.error("unable to copy {0}".format(src), detail=str(e))

    def copy_dir(self, src, dst, ignore=None):
        """ Copy a directory and its contents optionally ignoring a sequence of
        patterns.  If the destination directory already exists its contents
        will be first deleted.
        """

        # Make sure the destination does not exist but can be created.
        self.delete_dir(dst)
        self.create_dir(os.path.dirname(dst))

        self.verbose("Copying {0} to {1}".format(src, os.path.abspath(dst)))

        if ignore is not None:
            ignore = shutil.ignore_patterns(*ignore)

        try:
            shutil.copytree(src, dst, ignore=ignore)
        except Exception as e:
            self.error("unable to copy directory {0}".format(src),
                    detail=str(e))

    @staticmethod
    def create_file(name):
        """ Create a text file and return the file object.  A UserException is
        raised if there was an error.
        """

        return fu_create_file(name)

    def create_dir(self, name, empty=False):
        """ Ensure a directory exists and optionally delete its contents. """

        if empty:
            self.delete_dir(name)

        if os.path.exists(name):
            if not os.path.isdir(name):
                self.error("{0} exists but is not a directory".format(name))
        else:
            self.verbose("Creating {0}".format(name))

            try:
                os.makedirs(name, exist_ok=True)
            except Exception as e:
                self.error("unable to create directory {0}".format(name),
                        detail=str(e))

    @staticmethod
    def decode_version_nr(version_nr):
        """ Decode an encoded version number to a 3-tuple. """

        major = version_nr >> 16
        minor = (version_nr >> 8) & 0xff
        patch = version_nr & 0xff

        return major, minor, patch

    def delete_dir(self, name):
        """ Delete a directory and its contents. """

        if os.path.exists(name):
            if not os.path.isdir(name):
                self.error("{0} exists but is not a directory".format(name))

            self.verbose("Deleting {0}".format(name))

            # Windows has a 256 character limit on file names which we can hit.
            # The Microsoft work around is to prepend a magic string.
            name_hack = '\\\\?\\' + name if sys.platform == 'win32' else name

            try:
                shutil.rmtree(name_hack)
            except Exception as e:
                self.error("unable to remove directory {0}.".format(name),
                        detail=str(e))

    @staticmethod
    def error(message, detail='', exception=None):
        """ Raise an exception that will report an error is a user friendly
        manner.
        """

        raise UserException(message, detail=detail) from exception

    def extract_version_nr(self, name):
        """ Return an encoded version number from the name of a file or
        directory.  name is the name of the file or directory.  An exception is
        raised if a version number could not be extracted.
        """

        version_nr = fu_extract_version(name)

        if version_nr == 0:
            self.error(
                    "unable to extract a version number from '{0}'".format(
                            name))

        return version_nr

    def find_component(self, name, required=True):
        """ Return the component object for the given name or None if the
        component isn't specified.  If it is not specified and it is required
        then raise an exception.
        """

        for component in self.components:
            if component.name == name:
                return component

        if required:
            self._missing_component(name)

        return None

    def find_exe(self, name):
        """ Return the absolute pathname of an executable located on PATH. """

        host_exe = self.host_exe(name)

        for d in os.environ.get('PATH', '').split(os.pathsep):
            exe_path = os.path.join(d, host_exe)

            if os.access(exe_path, os.X_OK):
                return exe_path

        self.error("'{0}' must be installed on PATH".format(name))

    def find_file(self, name, required=True):
        """ Find a file (or directory).  If the name is relative then it is
        relative to the directory specified by the --source-dir command line
        options.  If this is not specified then the directory containing the
        JSON specification file is used.  The name may be a glob pattern.  The
        absolute pathname of the file is returned.
        """

        # Convert the name to a normalised absolute pathname.
        name = os.path.expandvars(name)

        if os.path.isabs(name):
            targets = [name]
        else:
            targets = [os.path.join(s, name) for s in self._source_dirs]

        # Check the name matches exactly one file.
        for target in targets:
            self.verbose("Looking for '{}'".format(target))

            names = glob.glob(target)
            if names:
                if len(names) > 1:
                    self.error(
                            "'{0}' matched several files and/or directories".format(
                                    name))

                found = os.path.normpath(names[0])

                self.verbose("Found '{}'".format(found))

                return found

        if required:
            self.error(
                    "nothing matching '{0}' could not be found".format(name))

        return None

    @classmethod
    def format_version_nr(cls, version_nr):
        """ Convert an encoded version number to a string. """

        return '.'.join([str(v) for v in cls.decode_version_nr(version_nr)])

    def get_python_install_path(self, version_nr=None):
        """ Return the name of the directory containing the root of the Python
        installation directory for an existing installation.  It must not be
        called on a non-Windows platform.
        """

        if version_nr is None:
            version_nr = self.target_py_version_nr

        return get_py_install_path(self.decode_version_nr(version_nr),
                self._target)

    @property
    def host_arch_name(self):
        """ The name of the host architecture. """

        return self._host.arch_name

    @property
    def host_bin_dir(self):
        """ The directory containing the host binaries. """

        return os.path.join(self.host_dir, 'bin')

    @property
    def host_dir(self):
        """ The directory containing the host installations. """

        return os.path.join(self.sysroot_dir, 'host')

    def host_exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return self._host.platform.exe(name)

    @property
    def host_make(self):
        """ The name of the host make executable. """

        return self._host.platform.make

    @property
    def host_platform_name(self):
        """ The name of the host platform. """

        return self._host.platform.name

    @property
    def host_pip(self):
        """ The pathname of the host pip executable. """

        self._check_python_component()

        return os.path.join(self.host_bin_dir, self.host_exe('pip'))

    @property
    def host_python(self):
        """ The pathname of the host Python interpreter. """

        self._check_python_component()

        return os.path.join(self.host_bin_dir, self.host_exe('python'))

    @property
    def host_qmake(self):
        """ The name of the host qmake executable. """

        if self._host_qmake is None:
            self._missing_component('qt5')

        return self._host_qmake

    @host_qmake.setter
    def host_qmake(self, qmake):
        """ Set the name of the host qmake executable.  This should only be
        used by the Qt component plugin.
        """

        self._host_qmake = self.host_exe(qmake)

    @property
    def host_sip(self):
        """ The name of the host sip executable. """

        sip = os.path.join(self.host_bin_dir, self.host_exe('sip'))

        if not os.path.exists(sip):
            self._missing_component('sip')

        return sip

    def make_symlink(self, src, dst):
        """ Create a host-specific symbolic link. """

        # Remove any existing destination.
        try:
            os.remove(dst)
        except FileNotFoundError:
            pass

        if sys.platform == 'win32':
            # Don't bother with symbolic link privileges on Windows.
            self.verbose("Copying {0} to {1}".format(src, dst))
            shutil.copyfile(src, dst)
        else:
            # If the source directory is within the same root as the
            # destination then make the link relative.  This means that the
            # root directory can be moved and the link will remain valid.
            if os.path.commonpath((src, dst)).startswith(self.sysroot_dir):
                src = os.path.relpath(src, os.path.dirname(dst))

            self.verbose("Linking {0} to {1}".format(src, dst))
            os.symlink(src, dst)

    @staticmethod
    def open_file(name):
        """ Open an existing text file and return the file object.  A
        UserException is raised if there was an error.
        """

        return fu_open_file(name)

    def parse_version_nr(version_str):
        """ Return an encoded version number from a string.  version_str is the
        string.  An exception is raised if a version number could not be
        parsed.
        """

        version_nr = fu_parse_version(version_str)

        if version_nr == 0:
            self.error(
                    "unable to convert a version number from '{0}'".format(
                            version_str))

        return version_nr

    def pip_install(self, package):
        """ Use pip to install a package in the sysroot site-packages
        directory.
        """

        self.run(self.host_pip, 'install', '--target',
                self.target_sitepackages_dir, package)

    def progress(self, message):
        """ Issue a progress message. """

        self._message_handler.progress_message(message)

    def run(self, *args, capture=False):
        """ Run a command, optionally capturing stdout. """

        return Platform.run(*args, message_handler=self._message_handler,
                capture=capture)

    @property
    def target_arch_name(self):
        """ The name of the target architecture. """

        return self._target.name

    @property
    def target_include_dir(self):
        """ The name of the directory containing target header files. """

        return os.path.join(self.sysroot_dir, 'include')

    @property
    def target_lib_dir(self):
        """ The name of the directory containing target libraries. """

        return os.path.join(self.sysroot_dir, 'lib')

    @property
    def target_platform_name(self):
        """ The name of the target platform. """

        return self._target.platform.name

    @property
    def target_py_include_dir(self):
        """ The name of the directory containing target Python header files.
        """

        return os.path.join(self.target_include_dir, self._py_subdir)

    @property
    def target_py_lib(self):
        """ The name of the target Python library. """

        return self._py_subdir + 'm'

    @property
    def target_py_stdlib_dir(self):
        """ The name of the directory containing target Python standard
        library. """

        return os.path.join(self.target_lib_dir, self._py_subdir)

    @property
    def target_py_version_nr(self):
        """ The Python version being targeted. """

        if self._target_py_version_nr is None:
            self._missing_component('python')

        return self._target_py_version_nr

    @target_py_version_nr.setter
    def target_py_version_nr(self, version_nr):
        """ The setter for the Python version being targeted. """

        self._target_py_version_nr = version_nr

    @property
    def target_pyqt_platform(self):
        """ The name of the target Python platform (as known by PyQt's
        configure.py).
        """

        # Note that this is a bit of a hack because configure.py doesn't
        # distinguish between Android and Linux or iOS and macOS.
        py_platform = self.target_platform_name

        if py_platform == 'android':
            py_platform = 'linux'
        elif py_platform in ('ios', 'macos'):
            py_platform = 'darwin'
        elif py_platform == 'win':
            py_platform = 'win32'

        return py_platform

    @property
    def target_sip_dir(self):
        """ The name of the directory containing the target .sip files. """

        return os.path.join(self.sysroot_dir, 'share', 'sip')

    @property
    def target_sitepackages_dir(self):
        """ The name of the target Python site-packages directory. """

        return os.path.join(self.target_lib_dir, self._py_subdir,
                'site-packages')

    @property
    def target_src_dir(self):
        """ The name of the directory containing target sources. """

        return os.path.join(self.sysroot_dir, 'src')

    def unpack_archive(self, archive, chdir=True):
        """ An archive is unpacked in the current directory.  If requested its
        top level directory becomes the current directory.  The name of the
        directory (not it's pathname) is returned.
        """

        # Windows has a problem extracting the Qt source archive (probably the
        # long pathnames).  As a work around we copy it to the current
        # directory and extract it from there.
        self.copy_file(archive, '.')
        archive_name = os.path.basename(archive)

        # Unpack the archive.
        self.verbose("Unpacking '{}'".format(archive_name))

        try:
            shutil.unpack_archive(archive_name)
        except Exception as e:
            self.error("unable to unpack {0}".format(archive_name),
                    detail=str(e))

        # Assume that the name of the extracted directory is the same as the
        # archive without the extension.
        archive_root = None
        for _, extensions, _ in shutil.get_unpack_formats():
            for ext in extensions:
                if archive_name.endswith(ext):
                    archive_root = archive_name[:-len(ext)]
                    break

            if archive_root:
                break
        else:
            # This should never happen if we have got this far.
            self.error("'{0}' has an unknown extension".format(archive))

        # Validate the assumption by checking the expected directory exists.
        if not os.path.isdir(archive_root):
            self.error(
                    "unpacking {0} did not create a directory called '{1}' as expected".format(archive_name, archive_root))

        # Delete the copied archive.
        os.remove(archive_name)

        # Change to the extracted directory if required.
        if chdir:
            os.chdir(archive_root)

        # Return the directory name which the component plugin will often use
        # to extract version information.
        return archive_root

    def verbose(self, message):
        """ Issue a verbose progress message. """

        self._message_handler.verbose_message(message)

    @property
    def verbose_enabled(self):
        """ True if verbose messages are being displayed. """

        return self._message_handler.verbose

    @property
    def _py_subdir(self):
        """ The name of a version-specific Python sub-directory. """

        major, minor, _ = self.decode_version_nr(self.target_py_version_nr)

        return 'python' + str(major) + '.' + str(minor)

    def _check_python_component(self):
        """ Check that the Python component plugin has been run. """

        if self._target_py_version_nr is None:
            self._missing_component('python')

    def _missing_component(self, name):
        """ Raise an exception about a missing component. """

        self.error("the sysroot specification must contain an entry for '{0}' before anything that depends on it".format(name))

    def _run_error(self, args, e):
        """ Raise an exception about a sub-process error. """

        self.error("execution of '{0}' failed".format(args[0]),
                detail=e.stderr, exception=e)
