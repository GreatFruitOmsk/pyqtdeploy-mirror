#!/usr/bin/env python3

# Build a sysroot containing Qt v5, Python v3 and the current SIP and PyQt5
# previews.


import argparse
import glob
import os
import shutil
import struct
import subprocess
import sys
import tarfile
import zipfile


QT_VERSION = '5.4.0'
PY_VERSION = '3.4.2'

# The supported targets.
TARGETS = ('android-32', 'ios-64', 'linux-32', 'linux-64', 'osx-64', 'win-32',
        'win-64')


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
    def python(self):
        """ The name of the python executable including any required path. """

        raise NotImplementedError

    @property
    def qmake(self):
        """ The name of the qmake executable including any required path. """

        return os.path.join(self.sysroot, 'qt-' + QT_VERSION, 'bin', 'qmake')

    @property
    def qt_package(self):
        """ The 2-tuple of the absolute path of the Qt package file and the
        base name of the package (without an extension).
        """

        raise NotImplementedError

    @property
    def sip_package(self):
        """ The 2-tuple of the absolute path of the SIP package file and the
        base name of the package (without an extension).
        """

        raise NotImplementedError

    @property
    def sysroot(self):
        """ The absolute path of the sysroot directory. """

        return self._sysroot

    @property
    def sysroot_src_dir(self):
        """ The absolute path of the src sub-directory of the sysroot
        directory.
        """

        return os.path.join(self.sysroot, 'src')

    def __init__(self, target, sysroot_base):
        """ Initialise the object. """

        self.target = target
        self._sysroot = sysroot_base + '-' + self.target

    @staticmethod
    def find_package(package_dir, pattern, extension):
        """ Return a 2-tuple of the absolute path of a package file and the
        base name of the package (without an extension).
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


class PosixHost(AbstractHost):
    """ The abstract base class that encapsulates a POSIX based host platform.
    """

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'

    @property
    def qt_package(self):
        """ The 2-tuple of the absolute path of the Qt package file and the
        base name of the package (without an extension).
        """

        base_name = 'qt-everywhere-enterprise-src-' + QT_VERSION

        return (os.path.expandvars('$HOME/Source/Qt/' + base_name + '.tar.gz'),
                base_name)

    @property
    def sip_package(self):
        """ The 2-tuple of the absolute path of the SIP package file and the
        base name of the package (without an extension).
        """

        sip_dir = os.path.expandvars('$HOME/hg/sip')

        os.chdir(sip_dir)
        self.run('./build.py', 'clean')
        self.run('./build.py', 'release')

        return self.find_package(sip_dir, 'sip-*', '.tar.gz')

    def __init__(self, target):
        """ Initialise the object. """

        super().__init__(target=target,
                sysroot_base=os.path.expandvars('$HOME/usr/sysroot'))


class OSXHost(PosixHost):
    """ The class that encapsulates an OS X host. """

    @property
    def pyqtdeploycli(self):
        """ The name of the pyqtdeploycli executable including any required
        path.
        """

        return 'pyqtdeploycli'

    @property
    def python(self):
        """ The name of the python executable including any required path. """

        return 'python3'


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


def get_default_target():
    """ Return the default target platform. """

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


def clean_sysroot(host):
    """ Create a clean sysroot. """

    rmtree(host.sysroot)
    os.makedirs(host.sysroot_src_dir)


def build_qt(host):
    """ Build a static Qt. """

    get_package_source(host, host.qt_package)

    host.run('./configure', '-prefix',
            os.path.join(host.sysroot, 'qt-' + QT_VERSION), '-commercial',
            '-confirm-license', '-static', '-release', '-nomake', 'examples')
    host.run(host.make)
    host.run(host.make, 'install')


def build_python(host):
    """ Build a static Python that supports dynamic loading. """

#    cd $SYSROOT_SRC_DIR
#    tar xvf $PY_SOURCE
#    cd $PY_SOURCE_BASE-$PY_VERSION
#    pyqtdeploycli --package python --enable-dynamic-loading configure
#    $QT_BIN_DIR/qmake SYSROOT=$SYSROOT
#    make
#    make install


def build_sip(host):
    """ Build a static SIP. """

    get_package_source(host, host.sip_package)

    configuration = 'sip-' + host.target + '.cfg'

    host.run(host.pyqtdeploycli, '--package', 'sip', '--output', configuration,
            '--target', host.target, 'configure')
    host.run(host.python, 'configure.py', '--static', '--sysroot',
            host.sysroot, '--no-tools', '--use-qmake', '--configuration',
            configuration)
    host.run(host.qmake)
    host.run(host.make)
    host.run(host.make, 'install')


def build_pyqt(host):
    """ Build a static PyQt5. """

#    cd $SYSROOT_SRC_DIR
#    rm -rf $PYQT5_SOURCE_BASE
#    tar xvf $PYQT5_HG_DIR/$PYQT5_SOURCE_BASE.tar.gz
#    cd $PYQT5_SOURCE_BASE
#    pyqtdeploycli --package pyqt5 configure
#    python3 configure.py --static --sysroot=$SYSROOT --no-tools --no-qsci-api --no-designer-plugin --no-qml-plugin --configuration=pyqt5-osx.cfg --qmake=$QT_BIN_DIR/qmake --confirm-license -c -j1
#    make
#    make install


# The different packages in the order that they should be built.
all_packages = ('qt', 'python', 'sip', 'pyqt')

# Parse the command line.
parser = argparse.ArgumentParser()

default_target = get_default_target()

group = parser.add_mutually_exclusive_group()
group.add_argument('--all', help="build all packages", action='store_true')
group.add_argument('--build', help="the packages to build", nargs='+',
        choices=all_packages)
parser.add_argument('--clean',
        help="clean the sysroot directory before building",
        action='store_true')
parser.add_argument('--target',
        help="the target platform [default: {0}]".format(default_target),
        choices=TARGETS, default=default_target)

args = parser.parse_args()

# Configure the host.
host = get_host(args.target)

# Determine the packages to build.
packages = all_packages if args.all else args.build

# Do the builds.
if args.clean:
    clean_sysroot(host)

if 'qt' in packages:
    build_qt(host)

if 'python' in packages:
    build_python(host)

if 'sip' in packages:
    build_sip(host)

if 'pyqt' in packages:
    build_pyqt(host)
