#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys


class UserException(Exception):
    """ An exception used for reporting user-triggered errors. """


def default_target():
    """ Return the default target. """

    if sys.platform.startswith('linux'):
        target = 'linux-64'
    elif sys.platform == 'win32':
        # MSVC2015 is v14, MSVC2017 is v15.
        vs_major = os.environ.get('VisualStudioVersion', '0.0').split('.')[0]

        if vs_major == '15':
            is_32 = (os.environ.get('VSCMD_ARG_TGT_ARCH') != 'x64')
        elif vs_major == '14':
            is_32 = (os.environ.get('Platform') != 'X64')
        else:
            # Default to 64 bits.
            is_32 = False

        target = 'win-' + ('32' if is_32 else '64')
    elif sys.platform == 'darwin':
        target = 'macos-64'
    else:
        raise UserException("unsupported host platform")

    return target


def find_tests(test, target):
    """ Return the list of test files for a target. """

    tests = []

    if test is None:
        test = 'tests'
    elif os.path.isabs(test):
        raise UserException(
                "'{0}' must be relative to the 'tests' directory".format(test))
    else:
        test = os.path.join('tests', test)

        if not os.path.exists(test):
            raise UserException("'{0}' does not exist".format(test))

    if os.path.isfile(test):
        tests.append(test)
    else:
        for dirpath, _, filenames in os.walk(test):
            # See if there is a file describing the tests to ignore for a
            # particular platform.
            ignore = {}

            ignore_file = os.path.join(dirpath, 'Ignore')
            if os.path.isfile(ignore_file):
                with open(ignore_file) as ig_f:
                    for line in ig_f:
                        line = line.strip()

                        # Ignore comments.
                        if line.startswith('#'):
                            continue

                        # We just ignore bad lines.
                        parts = line.split(':')
                        if len(parts) != 2:
                            continue

                        test_file = parts[0].strip()
                        if test_file == '':
                            continue

                        ignore[test_file] = parts[1].strip.split()

            for fn in filenames:
                if target in ignore.get(fn, []):
                    continue

                tests.append(os.path.join(dirpath, fn))

    return tests


class TestCase:
    """ Encapsulate a test for a particular target. """

    def __init__(self, test, target):
        """ Initialise the object. """

        self.test = test
        self.target = target

    @staticmethod
    def call(args, verbose, failure_message):
        """ Call a sub-process. """

        if verbose:
            print("Running: '{}'".format(' '.join(args)))

        failed = False

        try:
            with subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True) as process:
                try:
                    line = process.stdout.readline()

                    while line:
                        if verbose:
                            print(line.rstrip())

                        line = process.stdout.readline()

                    stderr = process.stderr.read().rstrip()
                    if stderr:
                        print(stderr)

                    retcode = process.wait()
                    if retcode != 0:
                        print("Returned exit code {}".format(retcode))
                        failed = True

                except Exception as e:
                    print(process.stderr.read().rstrip())
                    process.kill()
                    failed = True

        except Exception as e:
            print(str(e))
            failed = True

        if failed:
            raise UserException(failure_message)

    def run(self, source_dirs, no_clean, verbose):
        """ Re-implemented to run a test. """

        raise NotImplementedError


class SysrootTest(TestCase):
    """ Encapsulate a pyqtdeploy-sysroot test for a particular target. """

    # The filename exyension of pyqtdeploy-sysroot tests.
    test_extension = '.json'

    def run(self, source_dirs, no_clean, verbose):
        """ Run a pyqtdeploy-sysroot test. """

        print("Building sysroot from {}".format(self.test))

        # The name of the sysroot directory to be built.
        test_name = os.path.basename(self.test).split('.')[0]
        sysroot = os.path.join('sysroot',
                '{0}-{1}'.format(self.target, test_name))

        # Run pyqtdeploy-sysroot.
        args = ['pyqtdeploy-sysroot']

        if no_clean:
            args.append('--no-clean')

        if verbose:
            args.append('--verbose')

        for s in source_dirs:
            args.extend(['--source-dir', s])

        args.extend(['--target', self.target])
        args.extend(['--sysroot', sysroot])
        args.append(self.test)

        self.call(args, verbose,
                "Build of sysroot from {} failed".format(self.test))

        print("Build of sysroot from {} successful".format(self.test))


class StdlibTest(TestCase):
    """ Encapsulate a pyqtdeploy-build test for a particular target. """

    # The filename exyension of pyqtdeploy-build tests.
    test_extension = '.pdy'

    def run(self, source_dirs, no_clean, verbose):
        """ Run a pyqtdeploy-build test. """

        print("Building application from {}".format(self.test))

        # The name of the sysroot directory to use.
        sysroot = os.path.join('sysroot',
                '{}-python_stdlib'.format(self.target))

        # Run pyqtdeploy-build.
        args = ['pyqtdeploy-build']

        if no_clean:
            args.append('--no-clean')

        if verbose:
            args.append('--verbose')

        args.extend(['--target', self.target])
        args.extend(['--sysroot', sysroot])
        args.append(self.test)

        self.call(args, verbose,
                "pyqtdeploy-build using {} failed".format(self.test))

        # Change to the build directory and run qmake and make.
        build_dir = 'build-' + self.target
        qmake = os.path.abspath(os.path.join(sysroot, 'host', 'bin', 'qmake'))
        make = 'nmake' if sys.platform == 'win32' else 'make'

        os.chdir(build_dir)
        self.call([qmake], verbose, "qmake failed")
        self.call([make], verbose, "make failed")
        os.chdir('..')

        if not no_clean:
            shutil.rmtree(build_dir)

        print("Build of application from {} successful".format(self.test))


if __name__ == '__main__':

    import argparse

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('--no-clean',
            help="do not remove the temporary build directories",
            action='store_true')
    parser.add_argument('--source-dir',
            help="a directory containing the source archives",
            metavar='DIR', dest='source_dirs', action='append')
    parser.add_argument('--test',
            help="a test directory, JSON specification file or project file")
    parser.add_argument('--target', help="the target platform")
    parser.add_argument('--verbose', help="enable verbose progress messages",
            action='store_true')

    args = parser.parse_args()

    if args.source_dirs:
        source_dirs = [os.path.abspath(s) for s in args.source_dirs]
    else:
        source_dirs = None

    # Anchor everything from the directory containing this script.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if not source_dirs:
        source_dirs = [os.path.join('..', 'demo', 'src')]

    # Run the tests.
    try:
        if args.target:
            target = args.target
        else:
            target = default_target()

        tests = find_tests(args.test, target)

        # Any sysroot tests must be run first.
        for test in tests:
            if test.endswith(SysrootTest.test_extension):
                SysrootTest(test, target).run(source_dirs, args.no_clean,
                        args.verbose)

        for test in tests:
            if test.endswith(StdlibTest.test_extension):
                StdlibTest(test, target).run(source_dirs, args.no_clean,
                        args.verbose)

    except UserException as e:
        print(e)
        sys.exit(1)
