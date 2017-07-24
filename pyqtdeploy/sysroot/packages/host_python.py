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
import sys

from ... import (AbstractPackage, PackageOption, PythonPackageMixin,
        UserException)


class HostPythonPackage(PythonPackageMixin, AbstractPackage):
    """ The host Python package. """

    def build(self, sysroot):
        """ Build Python for the host. """

        self.validate_install_source_options()

        if self.installed_version:
            sysroot.progress(
                    "Installing the existing Python v{0} as the host Python".format(self.installed_version))

            if sys.platform == 'win32':
                interpreter = self._install_existing_windows_version(sysroot)
            else:
                interpreter = self._install_existing_version(sysroot)

        else:
            sysroot.progress("Building the host Python")

            if sys.platform == 'win32':
                raise UserException(
                        "building the host Python from source on Windows is not supported")

            interpreter = self._build_from_source(sysroot)

        # Create symbolic links to the interpreter in a standard place in
        # sysroot so that they can be referred to in cross-target .pdy files.
        sysroot.make_symlink(interpreter, sysroot.host_python)

    def _build_from_source(self, sysroot):
        """ Build the host Python from source and return the absolute pathname
        of the interpreter.
        """

        # Unpack the source and extract the version number.
        archive = sysroot.find_file(self.source)
        package_name = sysroot.unpack_archive(archive)
        py_version = package_name.split('-')[1].split('.')

        # ensurepip was added in Python v2.7.9 and v3.4.0.
        ensure_pip = False
        if py_version[0] == '2':
            if py_version[2] >= '9':
                ensure_pip = True
        elif py_version[1] >= '4':
            ensure_pip = True

        configure = ['./configure', '--prefix', sysroot.host_dir]
        if ensure_pip:
            configure.append('--with-ensurepip=no')

        sysroot.run(*configure)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

        return os.path.join(sysroot.host_bin_dir,
                'python' + '.'.join(py_version[:2]))

    def _install_existing_windows_version(self, sysroot):
        """ Install the host Python from an existing installation on Windows
        and return the absolute pathname of the interpreter.
        """ 

        install_path = self.get_windows_install_path()

        # Copy the DLL.
        py_major, py_minor = self.installed_version.split('.')
        dll = 'python' + py_major + py_minor + '.dll'
        shutil.copyfile(os.path.join(install_path, dll),
                os.path.join(sysroot.host_bin_dir, dll))

        return install_path + 'python.exe'

    def _install_existing_version(self, sysroot):
        """ Install the host Python from an existing installation and return
        the absolute pathname of the interpreter.
        """ 

        return sysroot.find_exe('python' + self.installed_version)
