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


import os
import shutil

from ..targets import normalised_target
from ..user_exception import UserException
from .specification import Specification


class Sysroot:
    """ Encapsulate a target-specific system root directory. """

    def __init__(self, sysroot_dir, sysroot_json, plugin_path, target_name, message_handler):
        """ Initialise the object. """

        if not sysroot_dir:
            sysroot_dir = 'sysroot-' + normalised_target(target_name)

        self._sysroot_dir = os.path.abspath(sysroot_dir)

        self._specification = Specification(sysroot_json, plugin_path)
        self._message_handler = message_handler

    def build_packages(self, package_names):
        """ Build a sequence of packages.  If no names are given then create
        the system image root directory and build everything.  Raise a
        UserException if there is an error.
        """

        if package_names:
            packages = self._packages_from_names(package_names)
        else:
            packages = self._specification.packages
            self._create_empty_dir(self._sysroot_dir)

        # Create a new build directory.
        build_dir = os.path.join(self._sysroot_dir, 'build')
        self._create_empty_dir(build_dir)
        cwd = os.getcwd()
        os.chdir(build_dir)

        # Build the packages.
        for package in packages:
            package.build(self._message_handler)

        # Remove the build directory.
        os.chdir(cwd)
        self._delete_dir(build_dir)

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

        self._message_handler.progress_message("Creating {}".format(name))

        try:
            os.mkdir(name)
        except Exception as e:
            raise UserException("unable to create {}".format(name),
                    detail=str(e))

    def _delete_dir(self, name):
        """ Delete an existng directory. """

        self._message_handler.progress_message("Deleting {}".format(name))

        try:
            shutil.rmtree(name)
        except Exception as e:
            raise UserException("unable to delete {}".format(name),
                    detail=str(e))
