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

    @property
    def bin_dir(self):
        """ The executables directory. """

        return os.path.join(self._sysroot, 'bin')

    @property
    def build_dir(self):
        """ The build directory. """

        return os.path.join(self._sysroot, 'build')

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

    def find_source(self, pattern, optional=False):
        """ Return the source package that matches a pattern.  There must be no
        more than one matching package.  If optional is set then the package is
        optional.
        """

        sources = [fn for fn in os.listdir(self.src_dir)
                if fnmatch.fnmatch(fn, pattern)]
        nr_sources = len(sources)

        if nr_sources == 1:
            return sources[0]

        if nr_sources == 0 and optional:
            return None

        package = pattern.split('-')[0]

        if nr_sources > 1:
            fatal("More than one source package was found for {}".format(
                    package))

        fatal("No source package was found for {}".format(package))

    @property
    def host_python_dir(self):
        """ The host Python directory. """

        return os.path.join(self._sysroot, 'HostPython')

    @property
    def qt_dir(self):
        """ The Qt directory. """

        return os.path.join(self._sysroot, 'Qt')

    @property
    def src_dir(self):
        """ The source directory. """

        return os.path.join(self._sysroot, 'src')

    def unpack_source(self, source):
        """ Unpack the source of a package and change to it's top-level
        directory.
        """

        for ext in ('.zip', '.tar.gz', '.tar.xz', '.tar.bz2'):
            if source.endswith(ext):
                base_dir = source[:-len(ext)]
                break
        else:
            fatal("'{}' has an unknown extension".format(source))

        make_directory(self.build_dir)
        os.chdir(self.build_dir)
        rmtree(base_dir)

        source_path = os.path.join(self.src_dir, source)

        if tarfile.is_tarfile(source_path):
            tarfile.open(source_path).extractall()
        elif zipfile.is_zipfile(source_path):
            zipfile.ZipFile(source_path).extractall()
        else:
            fatal("'{}' has an unknown format".format(source))

        os.chdir(base_dir)


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
sys.stdout.write('%s\\n' % sys.executable)
"""

    @property
    def interpreter(self):
        """ The name of the host Python interpreter. """

        return self._interpreter

    @property
    def name(self):
        """ The name of the host Python. """

        return self._name

    @property
    def version(self):
        """ The major.minor version of the host Python. """

        return self._version

    def get_configuration(self, interp):
        """ Ensure that we have the configuration of the host installation. """

        fd, introspect_script = tempfile.mkstemp(suffix='.py', text=True)
        os.write(fd, self.INTROSPECT)
        os.close(fd)

        details = subprocess.check_output((interp, introspect_script),
                universal_newlines=True)
        os.remove(introspect_script)

        details = details.strip().split('\n')
        if len(details) != 3:
            fatal("Host Python script returned unexpected values")

        self._version = details[0]
        self._name = details[1]
        self._interpreter = details[2]


class Host:
    """ Encapsulate a host platform. """

    def __init__(self, sysroot):
        """ Initialise the object. """

        self.sysroot = SysRoot(sysroot)
        self.python = HostPython()
        self._qt_version = None

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name

    @staticmethod
    def factory(sysroot):
        """ Create an instance of the host platform. """

        if sys.platform == 'darwin':
            host = OSXHost(sysroot)
        elif sys.platform == 'win32':
            host = WindowsHost(sysroot)
        else:
            host = LinuxHost(sysroot)

        return host

    @property
    def interpreter(self):
        """ The name of the host Python executable including any path. """

        return os.path.join(self.sysroot.bin_dir, self.exe('python'))

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

    @property
    def qmake(self):
        """ The name of the qmake executable including any path. """

        return os.path.join(self.sysroot.bin_dir, self.exe('qmake'))

    @property
    def qt_version(self):
        """ The Qt version as a string. """

        if self._qt_version is None:
            self._qt_version = self.run(self.qmake, '-query', 'QT_VERSION',
                    capture=True)

        return self._qt_version

    @staticmethod
    def run(*args, capture=False):
        """ Run a command. """

        if capture:
            try:
                stdout = subprocess.check_output(args, universal_newlines=True,
                        stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                fatal("Execution failed: ", e.stderr)

            return stdout.strip()

        subprocess.check_call(args)

        return None

    @property
    def sip(self):
        """ The name of the sip executable including any required path. """

        return os.path.join(self.sysroot.bin_dir, self.exe('sip'))


class WindowsHost(Host):
    """ The class that encapsulates a Windows host platform. """

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name + '.exe'

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


class PosixHost(Host):
    """ The base class that encapsulates a POSIX based host platform. """

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        return 'pyqtdeploycli'


class OSXHost(PosixHost):
    """ The class that encapsulates an OS X host. """


class LinuxHost(PosixHost):
    """ The class that encapsulates a Linux host. """


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


def make_directory(name):
    """ Ensure a directory exists. """

    os.makedirs(name, exist_ok=True)


def make_symlink(root_dir, src, dst):
    """ Ensure a symbolic link exists. """

    dst_dir = os.path.dirname(dst)

    make_directory(dst_dir)

    try:
        os.remove(dst)
    except FileNotFoundError:
        pass

    if sys.platform == 'win32':
        # Don't bother with symbolic link privileges on Windows.
        shutil.copyfile(src, dst)
    else:
        # If the source directory is within the same root as the destination
        # then make the link relative.  This means that the root directory can
        # be moved and the link will remain valid.
        if os.path.commonpath((src, dst)).startswith(root_dir):
            src = os.path.relpath(src, dst_dir)

        os.symlink(src, dst)


def build_qt(host, target, qt_dir):
    """ Build Qt. """

    # See if we need to build a target Qt installation from source.
    if qt_dir is None:
        # We don't support cross-compiling Qt.
        if target.name != host.name:
            fatal("Cross compiling Qt is not supported. Use the --qt option to specify a pre-compiled Qt installation")

        source = host.sysroot.find_source('qt-everywhere-*-src-*')
        host.sysroot.unpack_source(source)

        if sys.platform == 'win32':
            configure = 'configure.bat'

            dx_setenv = os.path.expandvars(
                    '%DXSDK_DIR%\\Utilities\\bin\\dx_setenv.cmd')

            if os.path.exists(dx_setenv):
                host.run(dx_setenv)

            original_path = os.environ['PATH']
            new_path = [original_path]

            new_path.insert(0, os.path.abspath('gnuwin32\\bin'))

            new_path.insert(0, 'C:\\Python27')

            os.environ['PATH'] = ';'.join(new_path)

            # Patch the mkspec to statically link the MSVC runtime.  This is
            # the current location (which was changed very recently).
            conf_name = os.path.join('qtbase', 'mkspecs', 'common',
                    'msvc-desktop.conf')

            conf_file = open(conf_name, 'rt')
            conf = conf_file.read()
            conf_file.close()

            conf = conf.replace(' embed_manifest_dll', '').replace(' embed_manifest_exe', '').replace('-MD', '-MT')

            conf_file = open(conf_name, 'wt')
            conf_file.write(conf)
            conf_file.close()
        else:
            configure = './configure'
            original_path = None

        license = '-opensource' if '-opensource-' in source else '-commercial'

        args = [configure, '-prefix', host.sysroot.qt_dir, license,
                '-confirm-license', '-static', '-release', '-nomake',
                'examples', '-nomake', 'tools']

        if sys.platform == 'win32':
            # These cause compilation failures (although maybe only with static
            # builds).
            args.append('-skip')
            args.append('qtimageformats')
        elif sys.platform.startswith('linux'):
            args.append('-qt-xcb')

        host.run(*args)
        host.run(host.make)
        host.run(host.make, 'install')

        if original_path is not None:
            os.environ['PATH'] = original_path

        qt_dir = host.sysroot.qt_dir
    else:
        qt_dir = os.path.abspath(qt_dir)

    # Create a symbolic link to qmake in a standard place in sysroot so that it
    # can be referred to in cross-target .pdy files.
    qt_bin_dir = os.path.join(qt_dir, 'bin')

    make_symlink(str(host.sysroot),
            os.path.join(qt_bin_dir, host.exe('qmake')), host.qmake)

    # Do the same for androiddeployqt if it exists for user build scripts.
    androiddeployqt = host.exe('androiddeployqt')
    androiddeployqt_path = os.path.join(qt_bin_dir, androiddeployqt)

    if os.path.isfile(androiddeployqt_path):
        make_symlink(str(host.sysroot), androiddeployqt_path,
                os.path.join(host.sysroot.bin_dir, androiddeployqt))


def build_host_python(host, target_name, use_system_python):
    """ Build (or install) a host Python. """

    if use_system_python is None:
        if sys.platform == 'win32':
            fatal("Building the host Python from source on Windows is not supported")

        source = host.sysroot.find_source('Python-*')
        host.sysroot.unpack_source(source)
        host.run('./configure', '--prefix', host.sysroot.host_python_dir)
        host.run(host.make)
        host.run(host.make, 'install')

        major_minor = '.'.join(source.split('-')[1].split('.')[:2])
        interp = os.path.join(host.sysroot.host_python_dir, 'bin',
                'python' + major_minor)
    elif sys.platform == 'win32':
        from winreg import (HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, QueryValue)

        py_major, py_minor = use_system_python.split('.')
        reg_version = use_system_python
        if int(py_major) == 3 and int(py_minor) >= 5 and target_name.endswith('-32'):
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
            fatal("Unable to find an installation of Python v{}".format(
                    reg_version))

        interp = install_path + 'python.exe'

        # Copy the DLL.  The .exe will get copied later.
        dll = 'python' + py_major + py_minor + '.dll'
        make_directory(host.sysroot.bin_dir)
        shutil.copyfile(os.path.join(install_path, dll),
                os.path.join(host.sysroot.bin_dir, dll))
    else:
        interp = 'python' + use_system_python

    host.python.get_configuration(interp)

    # Create symbolic links to the interpreter in a standard place in sysroot
    # so that they can be referred to in cross-target .pdy files.
    make_symlink(str(host.sysroot), host.python.interpreter, host.interpreter)


def build_target_python(host, target, debug, enable_dynamic_loading):
    """ Build a target Python that optionally supports dynamic loading. """

    pattern = 'Python-{}.*'.format(host.python.version)
    source = host.sysroot.find_source(pattern, optional=True)

    if source is None:
        if sys.platform == 'win32':
            # TODO: Move the install function from pyqtdeploycli to here.
            host.run(host.pyqtdeploycli,
                    '--target', target.name,
                    '--sysroot', str(host.sysroot),
                    '--package', 'python',
                    '--system-python', host.python.version,
                    'install')
        else:
            fatal("Using the system Python as the target on non-Windows is not supported")
    else:
        host.sysroot.unpack_source(source)

        pyqtdeploycli_args = [host.pyqtdeploycli]

        if enable_dynamic_loading:
            pyqtdeploycli_args.append('--enable-dynamic-loading')

        pyqtdeploycli_args.extend(
                ['--package', 'python', '--target', target.name, 'configure'])

        # Note that we do not remove the source directory as it may be needed
        # by the generated code.
        host.run(*pyqtdeploycli_args)

        qmake_args = [host.qmake, 'SYSROOT=' + str(host.sysroot)]
        if debug:
            qmake_args.append('CONFIG+=debug')

        host.run(*qmake_args)

        host.run(host.make)
        host.run(host.make, 'install')


def build_sip_code_generator(source, host):
    """ Build a host code generator. """

    host.sysroot.unpack_source(source)

    host.run(host.interpreter, 'configure.py', '--bindir',
            host.sysroot.bin_dir)
    os.chdir('sipgen')
    host.run(host.make)
    host.run(host.make, 'install')
    os.chdir('..')


def build_sip_module(source, host, target, debug):
    """ Build a target static sip module. """

    host.sysroot.unpack_source(source)

    configuration = 'sip-' + target.name + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'sip', '--output', configuration,
            '--target', target.name, 'configure')

    args = [host.interpreter, 'configure.py', '--static', '--sysroot',
            str(host.sysroot), '--no-pyi', '--no-tools', '--use-qmake',
            '--configuration', configuration]

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.qmake)
    host.run(host.make)
    host.run(host.make, 'install')


def build_sip(host, target, debug):
    """ Build sip. """

    source = host.sysroot.find_source('sip-*')
    build_sip_code_generator(source, host)
    build_sip_module(source, host, target, debug)


def build_pyqt5(host, target, debug):
    """ Build a target static PyQt5. """

    source = host.sysroot.find_source('PyQt5_*')
    host.sysroot.unpack_source(source)

    license_path = os.path.join(host.sysroot.src_dir, 'pyqt-commercial.sip')
    if os.path.isfile(license_path):
        shutil.copy(license_path, 'sip')

    configuration = 'pyqt5-' + target.name + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'pyqt5', '--output',
            configuration, '--target', target.name, 'configure')

    args = [host.interpreter, 'configure.py', '--static', '--qmake',
            host.qmake, '--sysroot', str(host.sysroot), '--no-tools',
            '--no-qsci-api', '--no-designer-plugin', '--no-python-dbus',
            '--no-qml-plugin', '--no-stubs', '--configuration', configuration,
            '--sip', host.sip, '--confirm-license', '-c', '-j2']

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.make)
    host.run(host.make, 'install')


def build_pyqtchart(host, target, debug):
    """ Build a target static PyQtChart. """

    source = host.sysroot.find_source('PyQtChart_*')
    host.sysroot.unpack_source(source)

    configuration = 'pyqtchart-' + target.name + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'pyqtchart', '--output',
            configuration, '--target', target.name, 'configure')

    args = [host.interpreter, 'configure.py', '--static', '--qmake',
            host.qmake, '--sysroot', str(host.sysroot), '--no-qsci-api',
            '--no-sip-files', '--no-stubs', '--configuration', configuration,
            '--sip', host.sip, '-c', '--qtchart-version', host.qt_version]

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.make)
    host.run(host.make, 'install')


def build_pyqtdatavisualization(host, target, debug):
    """ Build a target static PyQtDataVisualization. """

    source = host.sysroot.find_source('PyQtDataVisualization_*')
    host.sysroot.unpack_source(source)

    configuration = 'pyqtdatavisualization-' + target.name + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'pyqtdatavisualization',
            '--output', configuration, '--target', target.name, 'configure')

    args = [host.interpreter, 'configure.py', '--static', '--qmake',
            host.qmake, '--sysroot', str(host.sysroot), '--no-qsci-api',
            '--no-sip-files', '--no-stubs', '--configuration', configuration,
            '--sip', host.sip, '-c', '--qtdatavisualization-version',
            host.qt_version]

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.make)
    host.run(host.make, 'install')


def build_pyqtpurchasing(host, target, debug):
    """ Build a target static PyQtPurchasing. """

    source = host.sysroot.find_source('PyQtPurchasing_*')
    host.sysroot.unpack_source(source)

    configuration = 'pyqtpurchasing-' + target.name + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'pyqtpurchasing', '--output',
            configuration, '--target', target.name, 'configure')

    args = [host.interpreter, 'configure.py', '--static', '--qmake',
            host.qmake, '--sysroot', str(host.sysroot), '--no-qsci-api',
            '--no-sip-files', '--no-stubs', '--configuration', configuration,
            '--sip', host.sip, '-c', '--qtpurchasing-version', host.qt_version]

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.make)
    host.run(host.make, 'install')


def build_qscintilla(host, target, debug):
    """ Build a target static QScintilla. """

    source = host.sysroot.find_source('QScintilla_*')
    host.sysroot.unpack_source(source)

    # Build the static C++ library.
    os.chdir('Qt4Qt5')
    host.run(host.qmake, 'CONFIG+=staticlib')
    host.run(host.make)
    host.run(host.make, 'install')
    os.chdir('..')

    # Build the static Python bindings.
    os.chdir('Python')

    configuration = 'qscintilla-' + target.name + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'qscintilla', '--output',
            configuration, '--target', target.name, 'configure')

    args = [host.interpreter, 'configure.py', '--static', '--qmake',
            host.qmake, '--sysroot', str(host.sysroot), '--no-qsci-api',
            '--no-sip-files', '--no-stubs', '--configuration', configuration,
            '--sip', host.sip, '-c', '--pyqt', 'PyQt5']

    if debug:
        args.append('--debug')

    host.run(*args)

    host.run(host.make)
    host.run(host.make, 'install')


# The different packages in the order that they should be built.
all_packages = ('qt', 'python', 'sip', 'pyqt5', 'pyqtchart',
        'pyqtdatavisualization', 'pyqtpurchasing', 'qscintilla')

# Parse the command line.
parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group()
group.add_argument('--all', help="build all packages", action='store_true')
group.add_argument('--build', help="the packages to build", nargs='+',
        choices=all_packages)
parser.add_argument('--clean', action='store_true',
        help="clean the sysroot directory before building")
parser.add_argument('--debug', action='store_true',
        help="build the debug versions of packages where possible")
parser.add_argument('--enable-dynamic-loading', action='store_true',
        help="build Python with dynamic loading enabled")
parser.add_argument('--qt', metavar='DIR',
        help="the pre-compiled Qt installation to 'build'")
parser.add_argument('--sysroot', metavar='DIR',
        help="the sysroot directory")
parser.add_argument('--target', choices=TARGETS,
        help="the target platform [default: native]")
parser.add_argument('--use-system-python', metavar='VERSION',
        help="use the system Python version installation to 'build'")

args = parser.parse_args()

# Create a host instance.
host = Host.factory(args.sysroot)

# Determine the packages to build.
packages = all_packages if args.all else args.build

# Do the builds.
if args.clean:
    host.sysroot.clean()

# We build the host Python as soon as possble as that is where we get the host
# platform from.
if 'python' in packages:
    build_host_python(host, args.target, args.use_system_python)
else:
    host.python.get_configuration(host.interpreter)

# Create a target instance now that we know the host.
target = Target.factory(args.target, host)

if 'qt' in packages:
    build_qt(host, target, args.qt)

if 'python' in packages:
    build_target_python(host, target, args.debug, args.enable_dynamic_loading)

if 'sip' in packages:
    build_sip(host, target, args.debug)

if 'pyqt5' in packages:
    build_pyqt5(host, target, args.debug)

if 'pyqtchart' in packages:
    build_pyqtchart(host, target, args.debug)

if 'pyqtdatavisualization' in packages:
    build_pyqtdatavisualization(host, target, args.debug)

if 'pyqtpurchasing' in packages:
    build_pyqtpurchasing(host, target, args.debug)

if 'qscintilla' in packages:
    build_qscintilla(host, target, args.debug)
