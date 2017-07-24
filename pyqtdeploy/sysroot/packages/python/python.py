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

from .... import (AbstractPackage, DebugPackageMxin, PackageOption,
        PythonPackageMixin, UserException)


class PythonPackage(PythonPackageMixin, DebugPackageMixin, AbstractPackage):
    """ The target Python package. """

    # The package-specific options.
    options = [
        PackageOption('android_api', str,
                help="The Android API level to target."),
        PackageOption('disable_patches', bool,
                help="Disable the patching of the source code for Android."),
        PackageOption('dynamic_loading', bool,
                help="Set to enable support for the dynamic loading of extension modules when building from source."),
    ]

    def build(self, sysroot):
        """ Build Python for the target. """

        self.validate_install_source_options()

        if self.installed_version:
            sysroot.progress(
                    "Installing the existing Python v{0} as the target Python".format(self.installed_version))

            if sys.platform == 'win32':
                self._install_existing_windows_version(sysroot)
            else:
                raise UserException(
                        "using an existing Python installation is not supported for the {0} target".format(sysroot.target_name))

        else:
            sysroot.progress("Building the target Python")

            self._build_from_source(sysroot)

    def _build_from_source(self, sysroot):
        """ Build the target Python from source. """

    def _install_existing_windows_version(self, sysroot):
        """ Install the host Python from an existing installation on Windows.
        """ 

        py_major, py_minor = self.installed_version.split('.')
        install_path = self.get_windows_install_path()

        # The interpreter library.
        lib_name = 'python{0}{1}.lib'.format(py_major, py_minor)

        sysroot.copy_file(install_path + 'libs\\' + lib_name,
                os.path.join(sysroot.target_lib_dir, lib_name))

        if py_major >= 3 and py_minor >= 4:
            lib_name = 'python{0}.lib'.format(py_major)

            sysroot.copy_file(install_path + 'libs\\' + lib_name,
                    os.path.join(sysroot.target_lib_dir, lib_name))

        # The DLLs and extension modules.
        sysroot.copy_dir(install_path + 'DLLs',
                os.path.join(sysroot.target_lib_dir,
                        'DLLs{0}.{1}'.format(py_major, py_minor)),
                ignore=('*.ico', 'tcl*.dll', 'tk*.dll', '_tkinter.pyd'))

        py_dll = 'python{0}{1}.dll'.format(py_major, py_minor)

        if py_major == 3 and py_minor >= 5:
            py_dll_dir = install_path

            vc_dll = 'vcruntime140.dll'
            sysroot.copy_file(py_dll_dir + vc_dll,
                    os.path.join(dlls_dir, vc_dll))
        else:
            # Check for an installation for all users on 32 bit Windows.
            py_dll_dir = 'C:\\Windows\\System32\\'
            if not os.path.isfile(py_dll_dir + py_dll):
                # Check for an installation for all users on 64 bit Windows.
                py_dll_dir = 'C:\\Windows\\SysWOW64\\'
                if not os.path.isfile(py_dll_dir + py_dll):
                    # Assume it is an installation for the current user.
                    py_dll_dir = install_path

        sysroot.copy_file(py_dll_dir + py_dll, os.path.join(dlls_dir, py_dll))

        # The standard library.
        py_subdir = 'python{0}.{1}'.format(py_major, py_minor)

        sysroot.copy_dir(install_path + 'Lib',
                os.path.join(sysroot.target_lib_dir, py_subdir),
                ignore=('site-packages', '__pycache__', '*.pyc', '*.pyo'))

        # The header files.
        sysroot.copy_dir(install_path + 'include',
                os.path.join(sysroot.target_include_dir, py_subdir))
