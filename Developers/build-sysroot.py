#!/usr/bin/env python3

# Build a sysroot containing Qt v5, Python v2 or v3, SIP and PyQt5.

# Copyright (c) 2016, Riverbank Computing Limited
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


import argparse
import fnmatch
import glob
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import tarfile
import zipfile


# The supported targets.
TARGETS = ('android-32', 'ios-64', 'linux-32', 'linux-64', 'osx-64', 'win-32',
        'win-64')


class SysRoot:
    """ Encapsulate the system root directory. """

    def __init__(self, sysroot):
        """ Initialise the object. """

        if sysroot is None:
            sysroot = os.getenv('SYSROOT')
            if sysroot is None:
                fatal("Specify a sysroot directory using the --sysroot option or setting the SYSROOT environment variable")

        self._sysroot = os.path.abspath(sysroot)
        if not os.path.isdir(self._sysroot):
            fatal("The sysroot directory '{}' does not exist".format(
                    self._sysroot))

        if not os.path.isdir(self.src_dir):
            fatal("The sysroot source directory '{}' does not exist".format(
                    self.src_dir))

    def __str__(self):
        """ Return the string representation. """

        return self._sysroot

    def clean(self):
        """ Delete the contents of the sysroot directory except for the source
        directory.
        """

        for entry in os.listdir(self._sysroot):
            if entry != 'src':
                entry_path = os.path.join(self._sysroot, entry)

                if os.path.isdir(entry_path):
                    shutil.rmtree(entry_path)
                else:
                    os.remove(entry_path)

    @property
    def bin_dir(self):
        """ The executables directory. """

        return os.path.join(self._sysroot, 'bin')

    @property
    def src_dir(self):
        """ The source directory. """

        return os.path.join(self._sysroot, 'src')


class HostQt:
    """ Encapsulate the host Qt installation. """

    def __init__(self, qt_dir):
        """ Initialise the object. """

        self._qt_dir = os.path.abspath(qt_dir)

        if sys.platform == 'win32':
            # So executables can pick up the DLLs.
            old_path = os.environ['PATH']
            os.environ['PATH'] = os.path.join(self._qt_dir, 'bin') + os.pathsep + old_path

        self.qmake = os.path.join(self._qt_dir, 'bin', 'qmake')
        if sys.platform == 'win32':
            # TODO: Do we need the .exe?
            self.qmake += '.exe'

        self._properties = {}

        properties = subprocess.check_output((self.qmake, '-query'),
                universal_newlines=True)

        for p in properties.strip().split('\n'):
            n, v = p.split(':')
            self._properties[n] = v

    def __getattr__(self, name):
        """ Treat qmake properties as attributes. """

        try:
            return self._properties[name]
        except KeyError:
            raise AttributeError(
                    "'{}' is an unknown qmake property".format(name))


class HostPython:
    """ Encapsulate the host Python installation. """

    # The script to run to return the details of the host installation.
    INTROSPECT = b"""
import struct
import sys

sys.stdout.write('%d.%d\\n' % (sys.version_info[0], sys.version_info[1]))

if sys.platform == 'darwin':
    main_target = 'osx'
elif sys.platform == 'win32':
    main_target = 'win'
else:
    main_target = 'linux'

sys.stdout.write('%s-%s\\n' % (main_target, 8 * struct.calcsize('P')))
"""

    def __init__(self, interp):
        """ Initialise the object. """

        if interp is None:
            # Note that this won't work if we ever pyqtdeploy this script.
            interp = sys.executable
        else:
            interp = os.abspath(interp)

        self._interp = interp

        self._need_details = True

    @property
    def name(self):
        """ The name of the host Python. """

        self._get_details()

        return self._name

    @property
    def version(self):
        """ The major.minor version of the host Python. """

        self._get_details()

        return self._version

    def _get_details(self):
        """ Ensure that we have the details of the host installation. """

        if self._need_details:
            fd, introspect_script = tempfile.mkstemp(suffix='.py', text=True)
            os.write(fd, self.INTROSPECT)
            os.close(fd)

            details = subprocess.check_output(
                    (self._interp, introspect_script), universal_newlines=True)
            os.remove(introspect_script)

            details = details.strip().split('\n')
            if len(details) != 2:
                fatal("Host Python script returned unexpected values")

            self._version = details[0]
            self._name = details[1]

            self._need_details = False


class Host:
    """ Encapsulate a host platform. """

    def __init__(self, target, host_python, host_qt, sysroot):
        """ Initialise the object. """

        self.python = HostPython(host_python)
        self.qt = HostQt(host_qt)
        self.sysroot = SysRoot(sysroot)

    @staticmethod
    def factory(target, host_python, host_qt, sysroot):
        """ Create an instance of the host platform. """

        if sys.platform == 'darwin':
            host = OSXHost(target, host_python, host_qt, sysroot)
        elif sys.platform == 'win32':
            host = WindowsHost(target, host_python, host_qt, sysroot)
        else:
            host = LinuxHost(target, host_python, host_qt, sysroot)

        return host

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'

    @property
    def name(self):
        """ The canonical name of the host. """

        return self.python.name

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        return 'pyqtdeploycli'

    @staticmethod
    def run(*args):
        """ Run a command. """

        # TODO: Get rid of this completely.
        subprocess.check_call(args)

    def unpack_src(self, src):
        """ Unpack the source of a package and change to it's top-level
        directory.
        """

        # TODO: Unpack to a temporary directory and make this a staticmethod.
        for ext in ('.zip', '.tar.gz', '.tar.xz', '.tar.bz2'):
            if src.endswith(ext):
                base_dir = src[:-len(ext)]
                break
        else:
            fatal("'{}' has an unknown extension".format(src))

        os.chdir(self.sysroot.src_dir)
        rmtree(base_dir)

        if tarfile.is_tarfile(src):
            tarfile.open(src).extractall()
        elif zipfile.is_zipfile(src):
            zipfile.ZipFile(src).extractall()
        else:
            fatal("'{}' has an unknown format".format(src))

        os.chdir(base_dir)

    # TODO: Below here needs reviewing to see what is still needed.

    @property
    def pyqt_package(self):
        """ The 2-tuple of the absolute path of the PyQt source file and the
        base name of the package (without an extension).
        """

        raise NotImplementedError

    @property
    def qt_configure(self):
        """ The name of Qt's configure executable including any required path.
        """

        raise NotImplementedError

    @property
    def qt_cross_root_dir(self):
        """ The absolute path of the directory containing the binary
        cross-compiled Qt installation.
        """

        raise NotImplementedError

    @property
    def qt_package(self):
        """ The 2-tuple of the absolute path of the Qt source file and the base
        name of the package (without an extension).
        """

        license, ext = self.qt_package_detail
        if license == 'commercial':
            license = 'enterprise'

        base_name = 'qt-everywhere-' + license + '-src-' + QT_VERSION_NATIVE

        return (os.path.join(self.qt_src_dir, base_name + ext), base_name)

    @property
    def qt_package_detail(self):
        """ The 2-tuple of the Qt license and file extension. """

        raise NotImplementedError

    @property
    def qt_src_dir(self):
        """ The absolute path of the directory containing the Qt source file.
        """

        raise NotImplementedError

    @property
    def sip(self):
        """ The name of the sip executable including any required path. """

        raise NotImplementedError

    @property
    def sip_package(self):
        """ The 2-tuple of the absolute path of the SIP source file and the
        base name of the package (without an extension).
        """

        raise NotImplementedError

    @property
    def supported_cross_targets(self):
        """ The sequence of non-native targets that this host supports. """

        return ()

    @staticmethod
    def find_package(package_dir, pattern, extension):
        """ Return a 2-tuple of the absolute path of a source file and the base
        name of the package (without an extension).
        """

        full_pattern = os.path.join(package_dir, pattern + extension)
        files = glob.glob(full_pattern)

        if len(files) != 1:
            if len(files) == 0:
                fatal("{0} didn't match any files".format(full_pattern))

            fatal("{0} matched too many files".format(full_pattern))

        package = files[0]
        base_dir = os.path.basename(package)[:-len(extension)]

        return (package, base_dir)


class WindowsHost(Host):
    """ The class that encapsulates a Windows host platform. """

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'nmake'

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        # We assume that the same Python being used to execute this script can
        # also run pyqtdeploycli.
        return os.path.join(os.path.dirname(sys.executable), 'Scripts',
                'pyqtdeploycli')

    # TODO: Review everthing below to see if it is still needed.

    @property
    def pyqt_package(self):
        """ The 2-tuple of the absolute path of the PyQt source file and the
        base name of the package (without an extension).
        """

        return self.find_package(WINDOWS_SRC_DIR, 'PyQt5_internal-*', '.tar.gz')

    @property
    def qt_configure(self):
        """ The name of Qt's configure executable including any required path.
        """

        return 'configure.bat'

    @property
    def qt_package_detail(self):
        """ The 2-tuple of the Qt license and file extension. """

        return ('opensource', '.zip')

    @property
    def qt_src_dir(self):
        """ The absolute path of the directory containing the Qt source file.
        """

        return WINDOWS_SRC_DIR

    @property
    def sip(self):
        """ The name of the sip executable including any required path. """

        # TODO: Do we need the .exe?
        return self.sysroot_bin_dir + '\\sip.exe'

    @property
    def sip_package(self):
        """ The 2-tuple of the absolute path of the SIP source file and the
        base name of the package (without an extension).
        """

        return self.find_package(WINDOWS_SRC_DIR, 'sip-*', '.tar.gz')

    def build_configure(self):
        """ Perform any host-specific pre-build checks and configuration.
        Return a closure to be passed to qt_build_deconfigure().
        """

        super_closure = super().build_configure()

        dx_setenv = os.path.expandvars(
                '%DXSDK_DIR%\\Utilities\\bin\\dx_setenv.cmd')

        if os.path.exists(dx_setenv):
            self.run(dx_setenv)

        old_path = os.environ['PATH']
        os.environ['PATH'] = 'C:\\Python27;' + old_path

        return (old_path, super_closure)

    def build_deconfigure(self, closure):
        """ Undo any host-specific post-build configuration. """

        old_path, super_closure = closure

        os.environ['PATH'] = old_path

        super().build_deconfigure(super_closure)


class PosixHost(Host):
    """ The abstract base class that encapsulates a POSIX based host platform.
    """

    @property
    def pyqt_package(self):
        """ The 2-tuple of the absolute path of the PyQt source file and the
        base name of the package (without an extension).
        """

        pyqt_dir = os.path.expandvars('$HOME/hg/PyQt5')

        os.chdir(pyqt_dir)
        self.run('./build.py', 'clean')
        self.run('./build.py', 'release')

        return self.find_package(pyqt_dir, 'PyQt5_internal-*', '.tar.gz')

    @property
    def qt_configure(self):
        """ The name of Qt's configure executable including any required path.
        """

        return './configure'

    @property
    def qt_cross_root_dir(self):
        """ The absolute path of the directory containing the binary
        cross-compiled Qt installation.
        """

        return os.path.expandvars('$HOME/usr')

    @property
    def qt_package_detail(self):
        """ The 2-tuple of the Qt license and file extension. """

        return ('commercial', '.tar.gz')

    @property
    def sip(self):
        """ The name of the sip executable including any required path. """

        return self.sysroot_bin_dir + '/sip'

    @property
    def sip_package(self):
        """ The 2-tuple of the absolute path of the SIP source file and the
        base name of the package (without an extension).
        """

        sip_dir = os.path.expandvars('$HOME/hg/sip')

        os.chdir(sip_dir)
        self.run('./build.py', 'clean')
        self.run('./build.py', 'release')

        return self.find_package(sip_dir, 'sip-*', '.tar.gz')

    @property
    def supported_cross_targets(self):
        """ The sequence of non-native targets that this host supports. """

        return ('android-32', 'ios-64')


class OSXHost(PosixHost):
    """ The class that encapsulates an OS X host. """

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        return 'pyqtdeploycli'

    @property
    def qt_src_dir(self):
        """ The absolute path of the directory containing the Qt source file.
        """

        return os.path.expandvars('$HOME/Source/Qt')


class LinuxHost(PosixHost):
    """ The class that encapsulates a Linux host. """

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        return os.path.expandvars('$HOME/usr/bin/pyqtdeploycli')

    @property
    def qt_src_dir(self):
        """ The absolute path of the directory containing the Qt source file.
        """

        return os.path.expandvars('$HOME/usr/src')


class AbstractPythonInstallation:
    """ The abstract base class that encapsulates a Python version. """

    def __init__(self, version, host):
        """ Initialise the object. """

        self.version = version
        self.host = host

    @property
    def host_include_dir(self):
        """ The name of the directory containing the host Python include files.
        """

        raise NotImplementedError

    @property
    def host_library(self):
        """ The name of the host Python library. """

        raise NotImplementedError

    @property
    def host_python(self):
        """ The name of the host python executable including any required path.
        """

        raise NotImplementedError

    @property
    def host_stdlib_dir(self):
        """ The name of the directory containing the host Python standard
        library.
        """

        raise NotImplementedError

    def major_minor_version(self, dotted=True):
        """ Return a string of the Python major and minor versions with an
        optional separating dot.
        """

        major, minor, maint = self.version.split('.')
        sep = '.' if dotted else ''

        return major + sep + minor

    @property
    def package(self):
        """ The 2-tuple of the absolute path of the Python source file and the
        base name of the package (without an extension).
        """

        base_name = 'Python-' + self.version

        return (os.path.join(self.src_dir, base_name + '.tar.xz'), base_name)

    @property
    def src_dir(self):
        """ The absolute path of the directory containing the Python source
        file.
        """

        raise NotImplementedError


class WindowsPythonInstallation(AbstractPythonInstallation):
    """ The class that encapsulates a Python installation for a Windows host.
    Note that this assumes we have installed the system Python.
    """

    @property
    def host_include_dir(self):
        """ The name of the directory containing the host Python include files.
        """

        return self.host.sysroot + '\\include\\python' + self.major_minor_version()

    @property
    def host_library(self):
        """ The name of the host Python library. """

        return self.host.sysroot + '\\lib\\python' + self.major_minor_version(dotted=False) + '.lib'

    @property
    def host_python(self):
        """ The name of the host python executable including any required path.
        """

        return self._get_windows_install_path() + 'python'

    @property
    def host_stdlib_dir(self):
        """ The name of the directory containing the platform Python standard
        library.
        """

        return self.host.sysroot + '\\lib\\python' + self.major_minor_version()

    @property
    def src_dir(self):
        """ The absolute path of the directory containing the Python source
        file.
        """

        return WINDOWS_SRC_DIR

    def _get_windows_install_path(self):
        """ Return the Windows install path. """

        from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, QueryValue

        major_minor = self.major_minor_version()

        sub_key = 'Software\\Python\\PythonCore\\{0}\\InstallPath'.format(
                major_minor)

        for key in (HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE):
            try:
                install_path = QueryValue(key, sub_key)
            except OSError:
                pass
            else:
                break
        else:
            fatal("Unable to find an installation of Python v{0}.".format(
                    major_minor))

        return install_path


class PosixPythonInstallation(AbstractPythonInstallation):
    """ The abstract base class that encapsulates a Python installation for a
    POSIX based host platform.
    """


class OSXPythonInstallation(PosixPythonInstallation):
    """ The class that encapsulates a Python installation for an OS X host. """

    @property
    def host_python(self):
        """ The name of the host python executable including any required path.
        """

        return 'python3' if self.version.startswith('3') else 'python'

    @property
    def src_dir(self):
        """ The absolute path of the directory containing the Python source
        file.
        """

        return os.path.expandvars('$HOME/Source/Python')


class LinuxPythonInstallation(PosixPythonInstallation):
    """ The class that encapsulates a Python installation for a Linux host. """

    @property
    def host_python(self):
        """ The name of the host python executable including any required path.
        """

        return os.path.expandvars('$HOME/usr/bin/python3' if self.version.startswith('3') else '$HOME/usr/bin/python')

    @property
    def src_dir(self):
        """ The absolute path of the directory containing the Python source
        file.
        """

        return os.path.expandvars('$HOME/usr/src')


class AbstractQtBuilder:
    """ The abstract base class that encapsulates a Qt builder. """

    @property
    def qt_version(self):
        """ The Qt version number. """

        raise NotImplementedError

    def __init__(self, host):
        """ Initialise the object. """

        self.host = host

    def build(self):
        """ Build Qt. """

        raise NotImplementedError


class NativeQtBuilder(AbstractQtBuilder):
    """ The class that encapsulates a Qt builder for a native target. """

    @property
    def qt_version(self):
        """ The Qt version number. """

        return QT_VERSION_NATIVE

    def build(self):
        """ Build Qt. """

        host = self.host

        license, _ = host.qt_package_detail

        host.unpack_package(host.qt_package)

        host.run(host.qt_configure, '-prefix',
                os.path.join(host.sysroot,
                        'qt-' + QT_VERSION_NATIVE), '-' + license,
                '-confirm-license', '-static', '-release', '-nomake',
                'examples')
        host.run(host.make)
        host.run(host.make, 'install')

        remove_current_dir()


class CrossQtBuilder(AbstractQtBuilder):
    """ The class that encapsulates a Qt builder for a cross-compiled target.
    """

    # Map the target to the corresponding sub-directory in the Qt binary.
    TARGET_DIR_MAP = {
            'android-32':   'android_armv7',
            'ios-64':       'ios'}

    @property
    def qt_version(self):
        """ The Qt version number. """

        return QT_VERSION_CROSS

    def build(self):
        """ Build Qt. """

        host = self.host

        # For cross-compiling we use the Qt binary installation.
        cross_root = host.qt_cross_root_dir
        target_root = os.path.join(cross_root, 'Qt' + QT_VERSION_CROSS,
                '.'.join(QT_VERSION_CROSS.split('.')[:2]))
        target_subdir = self.TARGET_DIR_MAP[host.target]
        target_dir = os.path.join(target_root, target_subdir)

        sysroot_qt_dir = os.path.join(host.sysroot, 'qt-' + QT_VERSION_CROSS)

        try:
            os.remove(sysroot_qt_dir)
        except FileNotFoundError:
            pass

        os.symlink(target_dir, sysroot_qt_dir, target_is_directory=True)


class Target:
    """ Encapsulate a target platform. """

    def __init__(self, name):
        """ Initialise the object. """

        self.name = name

    @staticmethod
    def factory(name, host):
        """ Create an instance of the target platform. """

        # If no target is specified then assume a native build.
        if name is None:
            name = host.name

        return Target(name)


def fatal(message):
    """ Print an error message to stderr and exit the application. """

    print("{0}: {1}".format(os.path.basename(sys.argv[0]), message),
            file=sys.stderr)
    sys.exit(1)


def rmtree(dir_name):
    """ Remove a directory tree. """

    shutil.rmtree(dir_name, ignore_errors=True)


def remove_current_dir():
    """ Remove the current directory. """

    cwd = os.getcwd()
    os.chdir('..')
    rmtree(cwd)


def build_qt(host):
    """ Build Qt. """

    host.qt_builder.build()


def build_python(host, target, debug, enable_dynamic_loading):
    """ Build a target Python that optionally supports dynamic loading. """

    # Find the source code.
    patt = 'Python-{}.*.*'.format(host.python.version)

    sources = [fn for fn in os.listdir(host.sysroot.src_dir)
            if fnmatch.fnmatch(fn, patt)]
    nr_sources = len(sources)

    if nr_sources > 1:
        fatal("Muliple source packages for Python v{} found in the sysroot source directory".format(host.python.version))

    if nr_sources < 1:
        if sys.platform == 'win32':
            host.run(host.pyqtdeploycli,
                    '--sysroot', str(host.sysroot),
                    '--package', 'python',
                    '--system-python', host.python.version,
                    'install')
        else:
            fatal("Copy the source of Python v{} to the sysroot source directory".format(host.python.version))
    else:
        host.unpack_src(sources[0])

        pyqtdeploycli_args = [host.pyqtdeploycli]

        if enable_dynamic_loading:
            pyqtdeploycli_args.append('--enable-dynamic-loading')

        pyqtdeploycli_args.extend(
                ['--package', 'python', '--target', target.name, 'configure'])

        # Note that we do not remove the source directory as it may be needed
        # by the generated code.
        host.run(*pyqtdeploycli_args)

        qmake_args = [host.qt.qmake, 'SYSROOT=' + str(host.sysroot)]
        if debug:
            qmake_args.append('CONFIG+=debug')

        host.run(*qmake_args)

        host.run(host.make)
        host.run(host.make, 'install')


def build_sip_code_generator(host, python_installation):
    """ Build the host-specific code generator. """

    host.unpack_package(host.sip_package)

    host.run(python_installation.host_python, 'configure.py', '--bindir',
            host.sysroot_bin_dir)
    os.chdir('sipgen')
    host.run(host.make)
    host.run(host.make, 'install')
    os.chdir('..')

    remove_current_dir()


def build_sip_module(host, python_installation, debug):
    """ Build a static SIP module. """

    host.unpack_package(host.sip_package)

    configuration = 'sip-' + host.target + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'sip', '--output', configuration,
            '--target', host.target, 'configure')

    args = [python_installation.host_python, 'configure.py', '--static',
            '--sysroot', host.sysroot, '--no-tools', '--use-qmake',
            '--configuration', configuration]

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run('qmake')
    host.run(host.make)
    host.run(host.make, 'install')

    remove_current_dir()


def build_pyqt5(host, python_installation, debug):
    """ Build a static PyQt5. """

    host.unpack_package(host.pyqt_package)

    configuration = 'pyqt-' + host.target + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'pyqt5', '--output',
            configuration, '--target', host.target, 'configure')

    args = [python_installation.host_python, 'configure.py', '--static',
            '--sysroot', host.sysroot, '--no-tools', '--no-qsci-api',
            '--no-designer-plugin', '--no-qml-plugin', '--configuration',
            configuration, '--sip', host.sip, '--confirm-license', '-c', '-j2']

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.make)
    host.run(host.make, 'install')

    remove_current_dir()


# The different packages in the order that they should be built.
all_packages = ('qt', 'python', 'sip', 'pyqt5')

# Parse the command line.
parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group()
group.add_argument('--all', help="build all packages", action='store_true')
group.add_argument('--build', help="the packages to build", nargs='+',
        choices=all_packages)
parser.add_argument('--clean',
        help="clean the sysroot directory before building",
        action='store_true')
parser.add_argument('--debug',
        help="build the debug versions of packages where possible",
        action='store_true')
parser.add_argument('--enable-dynamic-loading',
        help="build Python with dynamic loading enabled", action='store_true')
parser.add_argument('--host-python', metavar='FILE',
        help="the host Python interpreter executable to use")
parser.add_argument('--host-qt', metavar='DIR', required=True,
        help="the host Qt installation to use")
parser.add_argument('--sysroot', metavar='DIR',
        help="the sysroot directory")
parser.add_argument('--target', choices=TARGETS,
        help="the target platform [default: native]")

args = parser.parse_args()

# Create a host instance.
host = Host.factory(args.target, args.host_python, args.host_qt, args.sysroot)

# Create a target instance.
target = Target.factory(args.target, host)

# Determine the packages to build.
packages = all_packages if args.all else args.build

# Do the builds.
if args.clean:
    host.sysroot.clean()

if 'qt' in packages:
    build_qt(host)

if 'python' in packages:
    build_python(host, target, args.debug, args.enable_dynamic_loading)

if 'sip' in packages:
    build_sip_module(host, args.debug)

if 'pyqt5' in packages:
    build_pyqt5(host, args.debug)
