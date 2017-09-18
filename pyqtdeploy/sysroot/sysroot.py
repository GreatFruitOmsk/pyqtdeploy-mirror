# Copyright (c) 2017, Riverbank Computing Limited
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
import subprocess
import sys

from ..file_utilities import (copy_embedded_file as fu_copy_embedded_file,
        create_file as fu_create_file, extract_version as fu_extract_version,
        get_embedded_dir as fu_get_embedded_dir,
        get_embedded_file_for_version as fu_get_embedded_file_for_version,
        open_file as fu_open_file, parse_version as fu_parse_version,
        read_embedded_file as fu_read_embedded_file)
from ..targets import normalised_target
from ..user_exception import UserException
from ..windows import get_python_install_path

from .hosts import Host
from .specification import Specification


class Sysroot:
    """ Encapsulate a target-specific system root directory. """

    def __init__(self, sysroot_dir, sysroot_json, plugin_path, sources_dir, sdk, target_name, message_handler):
        """ Initialise the object. """

        self.target_name = normalised_target(target_name)

        if not sysroot_dir:
            sysroot_dir = 'sysroot-' + self.target_name

        self.sysroot_dir = os.path.abspath(sysroot_dir)
        self._build_dir = os.path.join(self.sysroot_dir, 'build')

        self._host = Host.factory()
        self._specification = Specification(sysroot_json, plugin_path,
                self.target_name)
        self._sdk = self._find_sdk(sdk)
        self._message_handler = message_handler

        self._sources_dir = os.path.abspath(sources_dir) if sources_dir else os.path.dirname(self._specification.specification_file)

        self._pyqt5_disabled_features = None
        self._python_version_nr = None

    def build_packages(self, package_names, no_clean):
        """ Build a sequence of packages.  If no names are given then create
        the system image root directory and build everything.  Raise a
        UserException if there is an error.
        """

        # Allow the packages to configure sysroot even if they are not being
        # built.
        for package in self._specification.packages:
            package.publish(self)

        if package_names:
            packages = self._packages_from_names(package_names)
        else:
            packages = self._specification.packages
            self.create_dir(self.sysroot_dir, empty=True)
            os.makedirs(self.host_bin_dir)
            os.makedirs(self.target_include_dir)
            os.makedirs(self.target_lib_dir)
            os.makedirs(self.target_src_dir)

        # Create a new build directory.
        self.create_dir(self._build_dir, empty=True)
        cwd = os.getcwd()
        os.chdir(self._build_dir)

        # Build the packages.
        for package in packages:
            package.build(self)

        # Remove the build directory if requested.
        os.chdir(cwd)

        if not no_clean:
            self.delete_dir(self._build_dir)

    def show_options(self, package_names):
        """ Show the options for a sequence of packages.  If no names are given
        then show the options of all packages.  Raise a UserException if there
        is an error.
        """

        if package_names:
            packages = self._packages_from_names(package_names)
        else:
            packages = self._specification.packages

        self._specification.show_options(packages, self._message_handler)

    def _packages_from_names(self, package_names):
        """ Return a sequence of packages from a sequence of names. """

        packages = []

        for name in package_names:
            for package in self._specification.packages:
                if package.name == name:
                    packages.append(package)
                    break
            else:
                self.error("unkown package '{0}'".format(name))

        return packages

    @staticmethod
    def _find_sdk(user_sdk):
        """ Find an SDK to use. """

        if user_sdk and '/' in user_sdk:
            # The user specified an explicit path so use it.
            sdk = user_sdk
            if not os.path.isdir(sdk):
                sdk = None
        else:
            # TODO: The candidate directories should be target specific and we
            # need to decide how to handle iPhoneSimulator vs. iPhone.
            sdk_dirs = (
                '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs',
                '/Developer/SDKs'
            )

            for sdk_dir in sdk_dirs:
                if os.path.isdir(sdk_dir):
                    if user_sdk:
                        sdk = os.path.join(sdk_dir, user_sdk)
                    else:
                        # Use the latest SDK we find.
                        sdks = glob.glob(sdk_dir + '/MacOSX*.sdk')
                        if len(sdks) == 0:
                            sdk = None
                        else:
                            sdks.sort()
                            sdk = sdks[-1]

                    break
            else:
                sdk = None

        return sdk

    ###########################################################################
    # The following make up the public API to be used by package plugins.
    ###########################################################################

    def copy_file(self, src, dst):
        """ Copy a file. """

        self.verbose("Copying {0} to {1}".format(src, dst))

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

        self.verbose("Copying {0} to {1}".format(src, dst))

        if ignore is not None:
            ignore = shutil.ignore_patterns(*ignore)

        try:
            shutil.copytree(src, dst, ignore=ignore)
        except Exception as e:
            self.error("unable to copy directory {0}".format(src),
                    detail=str(e))

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
    def create_file(name):
        """ Create a text file.  A UserException is raised if there was an
        error.
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

    def delete_dir(self, name):
        """ Delete a directory and its contents. """

        if os.path.exists(name):
            if not os.path.isdir(name):
                self.error("{0} exists but is not a directory".format(name))

            self.verbose("Deleting {0}".format(name))

            try:
                shutil.rmtree(name)
            except Exception as e:
                self.error("unable to remove directory {0}.".format(name),
                        detail=str(e))

    @staticmethod
    def error(text, detail=''):
        """ Raise an exception that will report an error is a user friendly
        manner.
        """

        raise UserException(text, detail=detail)

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

    def find_exe(self, exe):
        """ Return the absolute pathname of an executable located on PATH. """

        host_exe = self.host_exe(exe)

        for d in os.environ.get('PATH', '').split(os.pathsep):
            exe_path = os.path.join(d, host_exe)

            if os.access(exe_path, os.X_OK):
                return exe_path

        self.error("'{0}' must be installed on PATH".format(exe))

    def find_file(self, name):
        """ Find a file (or directory).  If the name is relative then it is
        relative to the directory specified by the --sources command line
        option.  If this is not specified then the directory containing the
        JSON specification file is used.  The name may be a glob pattern.  The
        absolute pathname of the file is returned.
        """

        # Convert the name to a normalised absolute pathname.
        name = os.path.expandvars(name)

        if not os.path.isabs(name):
            name = os.path.join(self._sources_dir, name)

        # Check the name matches exactly one file.
        names = glob.glob(name)
        if names:
            if len(names) > 1:
                self.error(
                        "'{0}' matched several files and directories".format(
                                name))
        else:
            self.error(
                    "nothing matching '{0}' could not be found".format(name))

        return os.path.normpath(names[0])

    @staticmethod
    def decode_version_nr(version_nr):
        """ Decode an encoded version number to a 3-tuple. """

        major = version_nr >> 16
        minor = (version_nr >> 8) & 0xff
        patch = version_nr & 0xff

        return major, minor, patch

    @classmethod
    def format_version_nr(cls, version_nr):
        """ Convert an encoded version number to a string. """

        return '.'.join([str(v) for v in cls.decode_version_nr(version_nr)])

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

        return self._host.exe(name)

    @property
    def host_make(self):
        """ The name of the host make executable. """

        return self._host.make

    @property
    def host_python(self):
        """ The pathname of the host Python interpreter. """

        return os.path.join(self.host_bin_dir, self.host_exe('python'))

    @property
    def host_qmake(self):
        """ The name of the host qmake executable. """

        return os.path.join(self.host_bin_dir, self.host_exe('qmake'))

    @property
    def host_sip(self):
        """ The name of the host sip executable. """

        sip = os.path.join(self.host_bin_dir, self.host_exe('sip'))

        if not os.path.exists(sip):
            self.error(
                    "the sysroot specification must contain an entry for sip before anything that depends on it")

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

    @property
    def native(self):
        """ Return True if the target and host platforms are the same.  The
        word size is ignored.
        """

        if sys.platform == 'darwin':
            return self.target_name.startswith('osx-')

        if sys.platform == 'win32':
            return self.target_name.startswith('win-')

        return self.target_name.startswith('linux-')

    @staticmethod
    def open_file(name):
        """ Open an existing text file.  A UserException is raised if there was
        an error.
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

    def progress(self, message):
        """ Issue a progress message. """

        self._message_handler.progress_message(message)

    def py_windows_install_path(self):
        """ The name of the directory caontaining the root of the Python
        installation directory for an existing installation.  It must not be
        called on a non-Windows platform.
        """

        major, minor, _ = self.decode_version_nr(self.python_version_nr)

        reg_version = str(major) + '.' + str(minor)
        if self.python_version_nr >= 0x030500 and self.target_name.endswith('-32'):
            reg_version += '-32'

        return get_python_install_path(reg_version)

    @property
    def pyqt5_disabled_features(self):
        """ The PyQt5 features that are disabled. """

        if self._pyqt5_disabled_features is None:
            self.error(
                    "the sysroot specification must contain an entry for PyQt5 before anything that depends on it")

        return self._pyqt5_disabled_features

    @pyqt5_disabled_features.setter
    def pyqt5_disabled_features(self, disabled_features):
        """ The setter for the PyQt5 features that are disabled. """

        self._pyqt5_disabled_features = disabled_features

    @property
    def python_version_nr(self):
        """ The Python version being targetted. """

        if self._python_version_nr is None:
            self.error(
                    "the sysroot specification must contain an entry for the host/target Python before anything that depends on it")

        return self._python_version_nr

    @python_version_nr.setter
    def python_version_nr(self, version_nr):
        """ The setter for the Python version being targetted. """

        self._python_version_nr = version_nr

    def run(self, *args, capture=False):
        """ Run a command, optionally capturing stdout. """

        self._message_handler.verbose_message(
                "Running '{0}'".format(' '.join(args)))

        if capture:
            try:
                stdout = subprocess.check_output(args,
                        universal_newlines=True, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                self.error("execution of '{0}' failed".format(args[0]),
                        detail=e.stderr)

            return stdout.strip()

        subprocess.check_call(args)

        return None

    @staticmethod
    def read_embedded_file(name):
        """ Return the contents of an embedded text file as a QByteArray.  name
        is the name of the file.  A UserException is raised if there was an
        error.
        """

        return fu_read_embedded_file(name)

    @property
    def sdk(self):
        """ The Apple SDK to use. """

        if self._sdk is None:
            self.error("a valid SDK hasn't been specified")

        return self._sdk

    @property
    def target_include_dir(self):
        """ The name of the directory containing target header files. """

        return os.path.join(self.sysroot_dir, 'include')

    @property
    def target_lib_dir(self):
        """ The name of the directory containing target libraries. """

        return os.path.join(self.sysroot_dir, 'lib')

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
    def target_sip_dir(self):
        """ The name of the directory containing the target .sip files. """

        return os.path.join(self.sysroot_dir, 'share', 'sip')

    @property
    def target_qt_dir(self):
        """ The name of the root directory of the target Qt installation. """

        return os.path.join(self.sysroot_dir, 'qt')

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

        # Unpack the archive.
        try:
            shutil.unpack_archive(archive)
        except Exception as e:
            self.error("unable to unpack {0}".format(archive), detail=str(e))

        # Assume that the name of the extracted directory is the same as the
        # archive without the extension.
        archive_dir = None
        archive_file = os.path.basename(archive)
        for _, extensions, _ in shutil.get_unpack_formats():
            for ext in extensions:
                if archive_file.endswith(ext):
                    archive_dir = archive_file[:-len(ext)]
                    break

            if archive_dir:
                break
        else:
            # This should never happen if we have got this far.
            self.error("'{0}' has an unknown extension".format(archive))

        # Validate the assumption by checking the expected directory exists.
        if not os.path.isdir(archive_dir):
            self.error(
                    "unpacking {0} did not create a directory called '{1}' as expected".format(archive, archive_dir))

        # Change to the extracted directory if required.
        if chdir:
            os.chdir(archive_dir)

        # Return the directory name which the package plugin will often use to
        # extract version information.
        return archive_dir

    def verbose(self, message):
        """ Issue a verbose progress message. """

        self._message_handler.verbose_message(message)

    @property
    def _py_subdir(self):
        """ The name of a version-specific Python sub-directory. """

        major, minor, _ = self.decode_version_nr(self.python_version_nr)

        return 'python' + str(major) + '.' + str(minor)
