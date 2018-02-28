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


import os
import shutil
import sys

from .... import ComponentBase, ComponentOption

from .configure_python import configure_python


class PythonComponent(ComponentBase):
    """ The host and target Python component. """

    # The component options.
    options = [
        ComponentOption('build_host_from_source', type=bool,
                help="Build the host Python from source code rather than use an existing installation."),
        ComponentOption('build_target_from_source', type=bool,
                help="Build the target Python from source code rather than use an existing installation."),
        ComponentOption('dynamic_loading', type=bool,
                help="Set to enable support for the dynamic loading of extension modules when building from source."),
        ComponentOption('host_installation_bin_dir',
                help="The pathname of the directory containing the existing host Python interpreter installation. If it is not specified on Windows then the value found in the registry is used. On other platforms it is assumed to be on PATH."),
        ComponentOption('source', required=True,
                help="The archive containing the Python source code."),
    ]

    def build(self, sysroot):
        """ Build Python for the host and target. """

        # Extract the source code.
        archive = sysroot.find_file(self.source)
        old_wd = os.getcwd()
        os.chdir(sysroot.target_src_dir)
        sysroot.unpack_archive(archive)
        self._patch_source_for_target(sysroot)
        os.chdir(old_wd)

        # Build the host installation.
        if self.build_host_from_source:
            if sys.platform == 'win32':
                sysroot.error(
                        "building the host Python from source on Windows is not supported")

            sysroot.progress("Building the host Python from source")
            interpreter = self._build_host_from_source(sysroot, archive)
        else:
            sysroot.progress(
                    "Installing an existing Python v{0} as the host Python".format(sysroot.format_version_nr(sysroot.target_py_version_nr)))

            if sys.platform == 'win32':
                interpreter = self._install_host_from_existing_windows_version(
                        sysroot)
            else:
                interpreter = self._install_host_from_existing_version(sysroot)

        # Create symbolic links to the interpreter in a standard place in
        # sysroot so that they can be referred to in cross-target .pdy files.
        sysroot.make_symlink(interpreter, sysroot.host_python)

        # Do the same for pip taking care of the fact that on Windows in a
        # non-venv they are in different directories.
        interpreter_dir, interpreter_name = os.path.split(interpreter)
        pip_dir = interpreter_dir

        if sys.platform == 'win32':
            if os.path.basename(interpreter_dir) != 'Scripts':
                pip_dir = os.path.join(interpreter_dir, 'Scripts')

        pip_name = interpreter_name.replace('python', 'pip')
        sysroot.make_symlink(os.path.join(pip_dir, pip_name), sysroot.host_pip)

        # Build the target installation.
        if self.build_target_from_source:
            sysroot.progress("Building the target Python from source")
            self._build_target_from_source(sysroot, archive)
        else:
            if sys.platform == 'win32':
                sysroot.progress(
                        "Installing an existing Python v{0} as the target Python".format(sysroot.format_version_nr(sysroot.target_py_version_nr)))
                self._install_target_from_existing_windows_version(sysroot)
            else:
                sysroot.error(
                        "using an existing Python installation is not supported for {0}".format(sysroot.target_arch_name))

    def configure(self, sysroot):
        """ Complete the configuration of the component. """

        archive = sysroot.find_file(self.source)
        version_nr = sysroot.extract_version_nr(archive)

        if version_nr < 0x020700 or (version_nr >= 0x030000 and version_nr < 0x030300):
            sysroot.error(
                    "Python v{0} is not supported.".format(
                            sysroot.format_version_nr(version_nr)))

        if sysroot.target_platform_name == 'android':
            if version_nr < 0x030600:
                sysroot.error(
                        "Python v{0} is not supported on android.".format(
                                sysroot.format_version_nr(version_nr)))

        sysroot.target_py_version_nr = version_nr

    def _build_host_from_source(self, sysroot, archive):
        """ Build the host Python from source and return the absolute pathname
        of the interpreter.
        """

        sysroot.building_for_target = False

        # Unpack the source.
        sysroot.unpack_archive(archive)

        # ensurepip was added in Python v2.7.9 and v3.4.0.
        ensure_pip = False
        if sysroot.target_py_version_nr < 0x030000:
            if sysroot.target_py_version_nr >= 0x020709:
                ensure_pip = True
        elif sysroot.target_py_version_nr >= 0x030400:
            ensure_pip = True

        configure = ['./configure', '--prefix', sysroot.host_dir]
        if ensure_pip:
            configure.append('--with-ensurepip=no')

        sysroot.run(*configure)

        # For reasons not fully understood, the presence of this environment
        # variable breaks the build (probably only on macOS).
        launcher = os.environ.get('__PYVENV_LAUNCHER__')
        if launcher is not None:
            del os.environ['__PYVENV_LAUNCHER__']

        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

        if launcher is not None:
            os.environ['__PYVENV_LAUNCHER__'] = launcher

        sysroot.building_for_target = True

        return os.path.join(sysroot.host_bin_dir,
                'python' + self._major_minor(sysroot))

    def _install_host_from_existing_windows_version(self, sysroot):
        """ Install the host Python from an existing installation on Windows
        and return the absolute pathname of the interpreter.
        """

        if self.host_installation_bin_dir:
            install_path = os.path.expanduser(self.host_installation_bin_dir) + '\\'
        else:
            install_path = sysroot.get_python_install_path()

        # Copy the DLL.
        dll = 'python' + self._major_minor(sysroot).replace('.', '') + '.dll'
        shutil.copyfile(os.path.join(install_path, dll),
                os.path.join(sysroot.host_bin_dir, dll))

        return install_path + 'python.exe'

    def _install_host_from_existing_version(self, sysroot):
        """ Install the host Python from an existing installation and return
        the absolute pathname of the interpreter.
        """

        interpreter = 'python' + self._major_minor(sysroot)

        if self.host_installation_bin_dir:
            return os.path.join(
                    os.path.expanduser(self.host_installation_bin_dir),
                    interpreter)

        return sysroot.find_exe(interpreter)

    def _build_target_from_source(self, sysroot, archive):
        """ Build the target Python from source. """

        # Unpack the source.
        sysroot.unpack_archive(archive)
        self._patch_source_for_target(sysroot)

        # Configure for the target.
        configure_python(self.dynamic_loading, sysroot)

        # Do the build.
        sysroot.run(sysroot.host_qmake, 'SYSROOT=' + sysroot.sysroot_dir)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

        # Create a platform-specific dummy _sysconfigdata module.  This allows
        # the sysconfig module to work.  If necessary we can populate it with
        # genuinely useful information if people ask for it.
        if sysroot.target_platform_name != 'win':
            self._create_sysconfigdata(sysroot)

    def _create_sysconfigdata(self, sysroot):
        """ Create the _sysconfigdata module. """

        # The names must match those used in python.pro.  On macOS and Linux
        # they are chosen to match those used by a default build.  On Android
        # and iOS they are chosen to be unique so that they can have separate
        # entries in the Python meta-data.
        scd_names = {
            'android':  'linux_android',
            'ios':      'darwin_ios',
            'macos':    'darwin_darwin',
            'linux':    'linux_x86_64-linux-gnu',
        }

        scd_name = '_sysconfigdata_m_{0}.py'.format(
                scd_names[sysroot.target_platform_name])
        scd_path = os.path.join(sysroot.target_py_stdlib_dir, scd_name)
        scd = sysroot.create_file(scd_path)
        scd.write('''# Automatically generated.

build_time_vars = {
}
''')
        scd.close()

    def _install_target_from_existing_windows_version(self, sysroot):
        """ Install the target Python from an existing installation on Windows.
        """ 

        install_path = sysroot.get_python_install_path()

        py_major, py_minor, _ = sysroot.decode_version_nr(
                sysroot.target_py_version_nr)

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

    def _patch_source_for_target(self, sysroot):
        """ Patch the source code as necessary for the target. """

        # The only patching needed is for iOS.
        if sysroot.target_platform_name != 'ios':
            return

        patch = os.path.join('Modules', 'posixmodule.c')
        orig = patch + '.orig'

        sysroot.progress("Patching {0}".format(patch))

        # iOS doesn't have system() and the POSIX module uses hard-coded
        # configurations rather than the normal configure by introspection
        # process.
        os.rename(patch, orig)

        orig_file = sysroot.open_file(orig)
        patch_file = sysroot.create_file(patch)

        for line in orig_file:
            # Just skip any line that sets HAVE_SYSTEM.
            minimal = line.strip().replace(' ', '')
            if minimal != '#defineHAVE_SYSTEM1':
                patch_file.write(line)

        orig_file.close()
        patch_file.close()

    @staticmethod
    def _major_minor(sysroot):
        """ Return the Python major.minor as a string. """

        major, minor, _ = sysroot.decode_version_nr(
                sysroot.target_py_version_nr)

        return str(major) + '.' + str(minor)
