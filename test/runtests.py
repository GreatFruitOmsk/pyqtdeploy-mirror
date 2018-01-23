#!/usr/bin/env python3

import glob
import os
import shutil
import subprocess
import sys


class UserException(Exception):
    """ An exception used for reporting user-triggered errors. """


class TargetTests:
    """ Encapsulate a set of tests for a particular target. """

    def __init__(self, target, test=None):
        """ Initialise the object. """

        if not target:
            if sys.platform.startswith('linux'):
                target = 'linux-64'
            elif sys.platform == 'win32':
                target = 'win-{0}'.format(64 if os.environ.get('Platform') == 'X64' else 32)
            elif sys.platform == 'darwin':
                target = 'macos-64'
            else:
                raise UserException("unsupported host platform")

        self.target = target

        self._tests = [test] if test else self._find_tests()

    def call(self, args, verbose, failure_message):
        """ Call a sub-process. """

        if verbose:
            print("Running: '{}'".format(' '.join(args)))

        try:
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            raise UserException(failure_message)

    @classmethod
    def factory(cls, target, test):
        """ Create a tests instance for a particular test. """

        if test.endswith(TargetSysrootTests.test_extension):
            test_type = TargetSysrootTests
        elif test.endswith(TargetStdlibTests.test_extension):
            test_type = TargetStdlibTests
        else:
            raise UserException("unknown test type: {0}".format(test))

        return test_type(target, os.path.abspath(test))

    def run(self, no_clean, verbose):
        """ Run the tests. """

        for test in self._tests:
            self.run_test(test, no_clean, verbose)

    def run_test(self, test, no_clean, verbose):
        """ Re-implemented to run a single test. """

        raise NotImplementedError

    def _find_tests(self):
        """ Return the sequence of test files. """

        # Search the supported target directories.
        tests = []

        for target_dir in [self.target, 'common']:
            tests.extend(
                    glob.glob(
                            os.path.join('tests', target_dir,
                                    '*' + self.test_extension)))

        return tests


class TargetSysrootTests(TargetTests):
    """ Encapsulate a set of pyqtdeploy-sysroot tests for a particular target.
    """

    # The filename exyension of pyqtdeploy-sysroot tests.
    test_extension = '.json'

    def run_test(self, test, no_clean, verbose):
        """ Run a pyqtdeploy-sysroot test. """

        print("Building sysroot from {}".format(test))

        # The name of the sysroot directory to be built.
        test_name = os.path.basename(test).split('.')[0]
        sysroot = os.path.join('sysroot',
                '{0}-{1}'.format(self.target, test_name))

        # Run pyqtdeploy-sysroot.
        args = ['pyqtdeploy-sysroot']

        if no_clean:
            args.append('--no-clean')

        if verbose:
            args.append('--verbose')

        args.extend(['--source-dir', os.path.join('..', 'demo', 'src')])
        args.extend(['--target', self.target])
        args.extend(['--sysroot', sysroot])
        args.append(test)

        self.call(args, verbose,
                "Build of sysroot from {} failed".format(test))

        print("Build of sysroot from {} successful".format(test))


class TargetStdlibTests(TargetTests):
    """ Encapsulate a set of pyqtdeploy-build tests for a particular target.
    """

    # The filename exyension of pyqtdeploy-build tests.
    test_extension = '.pdy'

    def run_test(self, test, no_clean, verbose):
        """ Run a pyqtdeploy-build test. """

        print("Building application from {}".format(test))

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
        args.append(test)

        self.call(args, verbose,
                "pyqtdeploy-build using {} failed".format(test))

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

        print("Build of application from {} successful".format(test))


if __name__ == '__main__':

    import argparse

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('--no-clean',
            help="do not remove the temporary build directories",
            action='store_true')
    parser.add_argument('--test',
            help="the JSON specification file or project file")
    parser.add_argument('--target', help="the target platform")
    parser.add_argument('--verbose', help="enable verbose progress messages",
            action='store_true')

    args = parser.parse_args()

    # Anchor everything from the directory containing this script.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run a specific test or all of them.
    if args.test:
        TargetTests.factory(args.target, args.test).run(args.no_clean,
                args.verbose)
    else:
        # The sysroot tests must be run first.
        TargetSysrootTests(args.target).run(args.no_clean, args.verbose)
        TargetStdlibTests(args.target).run(args.no_clean, args.verbose)
