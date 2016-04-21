#!/usr/bin/env python3

# Build a sysroot containing Qt v5, Python v3 and the current SIP and PyQt5
# previews.

# Copyright (c) 2015, Riverbank Computing Limited
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
import glob
import os
import shutil
import struct
import subprocess
import sys
import tarfile
import zipfile


QT_VERSION_NATIVE = '5.6.0'
# Note that the Qt v5.5.1 installer for Andoid and iOS is broken.
QT_VERSION_CROSS = '5.6.0'
PY2_VERSION = '2.7.11'
PY3_VERSION = '3.5.1'

# The supported targets.
TARGETS = ('android-32', 'ios-64', 'linux-32', 'linux-64', 'osx-64', 'win-32',
        'win-64')

# Where the sources are kept on Windows.
WINDOWS_SRC_DIR = 'C:\\src'


class AbstractHost:
    """ The abstract base class that encapsulates a host platform. """

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        raise NotImplementedError

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        raise NotImplementedError

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

    @property
    def sysroot(self):
        """ The absolute path of the sysroot directory. """

        return self._sysroot

    @property
    def sysroot_bin_dir(self):
        """ The absolute path of the bin sub-directory of the sysroot
        directory.
        """

        return os.path.join(self.sysroot, 'bin')

    @property
    def sysroot_src_dir(self):
        """ The absolute path of the src sub-directory of the sysroot
        directory.
        """

        return os.path.join(self.sysroot, 'src')

    def __init__(self, target, sysroot_base, python_installation_factory):
        """ Initialise the object. """

        self.target = target
        self._sysroot = sysroot_base + '-' + self.target

        if self.target == get_native_target():
            self.qt_builder = NativeQtBuilder(self)
        elif self.target in self.supported_cross_targets:
            self.qt_builder = CrossQtBuilder(self)
        else:
            fatal("this host does not support building Qt for the {0} target".format(self.target))

        self.python2_installation = python_installation_factory(PY2_VERSION,
                self)
        self.python3_installation = python_installation_factory(PY3_VERSION,
                self)

    def build_configure(self):
        """ Perform any host-specific pre-build checks and configuration.
        Return a closure to be passed to build_deconfigure().
        """

        old_path = os.environ['PATH']
        os.environ['PATH'] = os.path.join(self.sysroot,
                'qt-' + self.qt_builder.qt_version, 'bin') + os.pathsep + old_path

        return old_path

    def build_deconfigure(self, closure):
        """ Undo any host-specific post-build configuration. """

        os.environ['PATH'] = closure

    @staticmethod
    def find_package(package_dir, pattern, extension):
        """ Return a 2-tuple of the absolute path of a source file and the base
        name of the package (without an extension).
        """

        full_pattern = os.path.join(package_dir, pattern + extension)
        files = glob.glob(full_pattern)

        if len(files) != 1:
            if len(files) == 0:
                raise Exception(
                        "{0} didn't match any files".format(full_pattern))

            raise Exception("{0} matched too many files".format(full_pattern))

        package = files[0]
        base_dir = os.path.basename(package)[:-len(extension)]

        return (package, base_dir)

    @staticmethod
    def run(*args):
        """ Run a command. """

        subprocess.check_call(args)


class WindowsHost(AbstractHost):
    """ The class that encapsulates a Windows host platform. """

    def __init__(self, target):
        """ Initialise the object. """

        super().__init__(target=target, sysroot_base='C:\\sysroot',
                python_installation_factory=WindowsPythonInstallation)

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


class PosixHost(AbstractHost):
    """ The abstract base class that encapsulates a POSIX based host platform.
    """

    def __init__(self, target, python_installation_factory):
        """ Initialise the object. """

        super().__init__(target=target,
                sysroot_base=os.path.expandvars('$HOME/usr/sysroot'),
                python_installation_factory=python_installation_factory)

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'

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

    def __init__(self, target):
        """ Initialise the object. """

        super().__init__(target=target,
                python_installation_factory=OSXPythonInstallation)

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

    def __init__(self, target):
        """ Initialise the object. """

        super().__init__(target=target,
                python_installation_factory=LinuxPythonInstallation)

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
            raise Exception(
                    "Unable to find an installation of Python v{0}.".format(
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

        get_package_source(host, host.qt_package)

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


def fatal(message):
    """ Print an error message to stderr and exit the application. """

    print("{0}: {1}".format(os.path.basename(sys.argv[0]), message),
            file=sys.stderr)
    sys.exit(1)


def rmtree(dir_name):
    """ Remove a directory tree. """

    shutil.rmtree(dir_name, ignore_errors=True)


def unpack(package):
    """ Unpack a package into the current directory. """

    if tarfile.is_tarfile(package):
        tarfile.open(package).extractall()
    elif zipfile.is_zipfile(package):
        zipfile.ZipFile(package).extractall()
    else:
        raise Exception("{0} has an unknown format".format(package))


def get_native_target():
    """ Return the native target platform. """

    if sys.platform == 'darwin':
        main_target = 'osx'
    elif sys.platform == 'win32':
        main_target = 'win'
    else:
        main_target = 'linux'

    return '{0}-{1}'.format(main_target, 8 * struct.calcsize('P'))


def get_host(target):
    """ Return the host platform. """

    if sys.platform == 'darwin':
        host = OSXHost(target)
    elif sys.platform == 'win32':
        host = WindowsHost(target)
    else:
        host = LinuxHost(target)

    return host


def get_package_source(host, package):
    """ Extract the source of a package and change to it's top-level directory.
    """

    package_src, base_dir = package
    os.chdir(host.sysroot_src_dir)
    rmtree(base_dir)
    unpack(package_src)
    os.chdir(base_dir)


def remove_current_dir():
    """ Remove the current directory. """

    cwd = os.getcwd()
    os.chdir('..')
    rmtree(cwd)


def clean_sysroot(host):
    """ Create a clean sysroot. """

    rmtree(host.sysroot)
    os.makedirs(host.sysroot_src_dir)


def build_qt(host):
    """ Build Qt. """

    host.qt_builder.build()


def build_python(host, python_installation, debug, enable_dynamic_loading):
    """ Build a Python that optionally supports dynamic loading. """

    if sys.platform == 'win32':
        host.run(host.pyqtdeploycli,
                '--sysroot', host.sysroot,
                '--package', 'python',
                '--system-python', python_installation.major_minor_version(),
                'install')
    else:
        get_package_source(host, python_installation.package)

        pyqtdeploycli_args = [host.pyqtdeploycli]

        if enable_dynamic_loading:
            pyqtdeploycli_args.append('--enable-dynamic-loading')

        pyqtdeploycli_args.extend(
                ['--package', 'python', '--target', host.target, 'configure'])

        # Note that we do not remove the source directory as it may be needed
        # by the generated code.
        host.run(*pyqtdeploycli_args)

        qmake_args = ['qmake', 'SYSROOT=' + host.sysroot]
        if debug:
            qmake_args.append('CONFIG+=debug')

        host.run(*qmake_args)

        host.run(host.make)
        host.run(host.make, 'install')


def build_sip_code_generator(host, python_installation):
    """ Build the host-specific code generator. """

    get_package_source(host, host.sip_package)

    host.run(python_installation.host_python, 'configure.py', '--bindir',
            host.sysroot_bin_dir)
    os.chdir('sipgen')
    host.run(host.make)
    host.run(host.make, 'install')
    os.chdir('..')

    remove_current_dir()


def build_sip_module(host, python_installation, debug):
    """ Build a static SIP module. """

    get_package_source(host, host.sip_package)

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


def build_pyqt(host, python_installation, debug):
    """ Build a static PyQt5. """

    get_package_source(host, host.pyqt_package)

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
all_packages = ('qt', 'python2', 'python3', 'sip', 'pyqt')

# Parse the command line.
parser = argparse.ArgumentParser()

native_target = get_native_target()

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
parser.add_argument('--target',
        help="the target platform [default: {0}]".format(native_target),
        choices=TARGETS, default=native_target)

args = parser.parse_args()

# Configure the host.
host = get_host(args.target)

# Determine the packages to build.
packages = all_packages if args.all else args.build

# Do the builds.
if args.clean:
    clean_sysroot(host)

closure = host.build_configure()

if 'qt' in packages:
    build_qt(host)

if 'python2' in packages:
    build_python(host, host.python2_installation, args.debug,
            args.enable_dynamic_loading)

if 'python3' in packages:
    build_python(host, host.python3_installation, args.debug,
            args.enable_dynamic_loading)

if 'sip' in packages:
    build_sip_code_generator(host, host.python3_installation)

    build_sip_module(host, host.python2_installation, args.debug)
    build_sip_module(host, host.python3_installation, args.debug)

if 'pyqt' in packages:
    build_pyqt(host, host.python2_installation, args.debug)
    build_pyqt(host, host.python3_installation, args.debug)

host.build_deconfigure(closure)
