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

from ..targets import normalised_target
from ..user_exception import UserException

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

    def build_packages(self, package_names):
        """ Build a sequence of packages.  If no names are given then create
        the system image root directory and build everything.  Raise a
        UserException if there is an error.
        """

        if package_names:
            packages = self._packages_from_names(package_names)
        else:
            packages = self._specification.packages
            self._create_empty_dir(self.sysroot_dir)
            os.makedirs(self.host_bin_dir)

        # Create a new build directory.
        self._create_empty_dir(self._build_dir)
        cwd = os.getcwd()
        os.chdir(self._build_dir)

        # Build the packages.
        for package in packages:
            package.build(self)

        # Remove the build directory.
        os.chdir(cwd)
        self._delete_dir(self._build_dir)

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
                raise UserException("unkown package '{}'".format(name))

        return packages

    def _create_empty_dir(self, name):
        """ Create an empty directory. """

        # Delete any existing one.
        if os.path.exists(name):
            if os.path.isdir(name):
                self._delete_dir(name)
            else:
                raise UserException(
                        "{} already exists but is not a directory".format(
                                name))

        self.verbose("Creating {}".format(name))

        try:
            os.mkdir(name)
        except Exception as e:
            raise UserException("unable to create {}".format(name),
                    detail=str(e))

    def _delete_dir(self, name):
        """ Delete an existng directory. """

        self.verbose("Deleting {}".format(name))

        try:
            shutil.rmtree(name)
        except Exception as e:
            raise UserException("unable to delete {}".format(name),
                    detail=str(e))

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

    def find_exe(self, exe):
        """ Return the absolute pathname of an executable located on PATH. """

        host_exe = self.host_exe(exe)

        for d in os.environ.get('PATH', '').split(os.pathsep):
            exe_path = os.path.join(d, host_exe)

            if os.access(exe_path, os.X_OK):
                return exe_path

        raise UserException("'{}' must be installed on PATH".format(exe))

    def find_file(self, name):
        """ Find a file.  If the name is relative then it is relative to the
        directory specified by the --sources command line option.  If this is
        not specified then the directory containing the JSON specification file
        is used.  The absolute pathname of the file is returned.
        """

        # Convert the name to a normalised absolute pathname.
        name = os.path.expandvars(name)

        if not os.path.isabs(name):
            name = os.path.join(self._sources_dir, name)

        name = os.path.normpath(name)

        # Check the file exists.
        if not os.path.exists(name):
            raise UserException("'{}' could not be found".format(name))

        return name

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
    def native(self):
        """ Return True if the target and host platforms are the same.  The
        word size is ignored.
        """

        if sys.platform == 'darwin':
            return self.target_name.startswith('osx-')

        if sys.platform == 'win32':
            return self.target_name.startswith('win-')

        return self.target_name.startswith('linux-')

    def progress(self, message):
        """ Issue a progress message. """

        self._message_handler.progress_message(message)

    def run(self, *args, capture=False):
        """ Run a command, optionally capturing stdout. """

        self._message_handler.verbose_message(
                "Running '{}'".format(' '.join(args)))

        if capture:
            try:
                stdout = subprocess.check_output(args,
                        universal_newlines=True, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                raise UserException("execution of '{}' failed".format(args[0]),
                        detail=e.stderr)

            return stdout.strip()

        subprocess.check_call(args)

        return None

    def make_symlink(self, src, dst):
        """ Create a host-specific symbolic link. """

        # Remove any existing destination.
        try:
            os.remove(dst)
        except FileNotFoundError:
            pass

        if sys.platform == 'win32':
            # Don't bother with symbolic link privileges on Windows.
            self.verbose("Copying {} to {}".format(src, dst))
            shutil.copyfile(src, dst)
        else:
            # If the source directory is within the same root as the
            # destination then make the link relative.  This means that the
            # root directory can be moved and the link will remain valid.
            if os.path.commonpath((src, dst)).startswith(self.sysroot_dir):
                src = os.path.relpath(src, os.path.dirname(dst))

            self.verbose("Linking {} to {}".format(src, dst))
            os.symlink(src, dst)

    @property
    def sdk(self):
        """ The Apple SDK to use. """

        if self._sdk is None:
            raise UserException("a valid SDK hasn't been specified")

        return self._sdk

    @property
    def target_qt_dir(self):
        """ The name of the root directory of the target Qt installation. """

        return os.path.join(self.sysroot_dir, 'qt')

    def unpack_archive(self, archive, chdir=True):
        """ An archive is unpacked in the current directory.  If requested its
        top level directory becomes the current directory.  The name of the
        directory (not it's pathname) is returned.
        """

        # Unpack the archive.
        try:
            shutil.unpack_archive(archive)
        except Exception as e:
            raise UserException("unable to unpack {}".format(archive),
                    detail=str(e))

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
            raise UserException("'{}' has an unknown extension".format(archive))

        # Validate the assumption by checking the expected directory exists.
        if not os.path.isdir(archive_dir):
            raise UserException(
                    "unpacking {} did not create a directory called '{}' as expected".format(archive, archive_dir))

        # Change to the extracted directory if required.
        if chdir:
            os.chdir(archive_dir)

        # Return the directory name which the package plugin will often use to
        # extract version information.
        return archive_dir

    def verbose(self, message):
        """ Issue a verbose progress message. """

        self._message_handler.verbose_message(message)
