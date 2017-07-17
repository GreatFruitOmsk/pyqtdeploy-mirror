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


class PythonPackage(PythonPackageMixin, AbstractPackage):
    """ The target Python package. """

    # The package-specific options.
    options = [
        PackageOption('dynamic_loading', bool,
                help="Set to enable support for the dynamic loading of extension modules when building from source."),
    ]

    def build(self, sysroot):
        """ Build Python for the target. """

        if self.installed_version:
            if self.source:
                raise UserException(
                        "the 'installed_version' and 'source' options cannot both be specified")

            sysroot.progress(
                    "Installing the existing Python v{} as the target Python".format(self.installed_version))

            if sys.platform == 'win32':
                self._install_existing_windows_version(sysroot)
            else:
                raise UserException(
                        "using an existing Python installation is not supported for the {} target".format(sysroot.target_name))
        else:
            if not self.source:
                raise UserException(
                        "either the 'installed_version' or 'source' option must be specified")
                
            sysroot.progress("Building the target Python")

            self._build_from_source(sysroot)

    def _build_from_source(self, sysroot):
        """ Build the target Python from source. """

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

    def _install_existing_windows_version(self, sysroot):
        """ Install the host Python from an existing installation on Windows.
        """ 

        from winreg import (HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, QueryValue)

        py_major, py_minor = self.installed_version.split('.')
        reg_version = self.installed_version
        if int(py_major) == 3 and int(py_minor) >= 5 and target_name is not None and target_name.endswith('-32'):
            reg_version += '-32'

        sub_key_user = 'Software\\Python\\PythonCore\\{}\\InstallPath'.format(
                reg_version)
        sub_key_all_users = 'Software\\Wow6432Node\\Python\\PythonCore\\{}\\InstallPath'.format(
                reg_version)

        queries = (
            (HKEY_CURRENT_USER, sub_key_user),
            (HKEY_LOCAL_MACHINE, sub_key_user),
            (HKEY_LOCAL_MACHINE, sub_key_all_users))

        for key, sub_key in queries:
            try:
                install_path = QueryValue(key, sub_key)
            except OSError:
                pass
            else:
                break
        else:
            raise UserException(
                    "unable to find an installation of Python v{}".format(
                            reg_version))

        # Copy the DLL.
        dll = 'python' + py_major + py_minor + '.dll'
        shutil.copyfile(os.path.join(install_path, dll),
                os.path.join(sysroot.host_bin_dir, dll))
