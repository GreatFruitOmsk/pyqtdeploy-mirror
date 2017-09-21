#!/usr/bin/env python3

import glob
import os
import struct
import subprocess
import sys


class UserException(Exception):
    """ An exception used for reporting user-triggered errors. """


class TargetSpecifications:
    """ Encapsulate a set of specifications for a particular target. """

    # The root directory.  This will be the current directory when
    # pyqtdeploy-sysroot is run.
    _root_dir = os.path.abspath(os.path.dirname(__file__))

    def __init__(self, target, specification=None):
        """ Initialise the object. """

        specs_dir = os.path.join(self._root_dir, 'specifications')

        if specification:
            # An specific specification was given.
            specification = os.path.abspath(specification)

            # If there is no explicit target then we assume that the
            # specification is part of the test suite and the target
            # corresponds to the directory containing the specification.
            if not target:
                target_dir = os.path.dirname(specification)
                if os.path.dirname(target_dir) != specs_dir:
                    raise UserException(
                            "unable to determine the target name for specification '{}'".format(specification))

                target = os.path.basename(target_dir)

                if target == 'common':
                    target = self._default_target

            specifications = [specification]
        else:
            if not target:
                target = self._default_target

            # Search the supported target directories.
            specifications = []

            for target_dir in [target, 'common']:
                specifications.extend(
                        glob.glob(
                                os.path.join(specs_dir, target_dir, '*.json')))

        self._specifications = specifications
        self._target = target

    def build(self, verbose):
        """ Build the sysroot images. """

        os.chdir(self._root_dir)

        for spec in self._specifications:
            print("Building sysroot from {}".format(spec))

            # The name of the sysroot image file to be built.
            test_name = os.path.basename(spec).split('.')[0]
            sysroot = os.path.join(self._root_dir, 'sysroot',
                    '{}-{}'.format(self._target, test_name))

            # Build the command line.
            args = ['pyqtdeploy-sysroot']

            if verbose:
                args.append('--verbose')
                
            args.extend(['--source-dir', os.path.join(self._root_dir, 'src')])
            args.extend(['--target', self._target])
            args.extend(['--sysroot', sysroot])
            args.append(spec)

            if verbose:
                print("Running: '{}'".format(' '.join(args)))

            subprocess.check_call(args)

    @property
    def _default_target(self):
        """ Return the default target for this platform. """

        if sys.platform.startswith('linux'):
            main_target = 'linux'
        elif sys.platform == 'win32':
            main_target = 'win'
        elif sys.platform == 'darwin':
            main_target = 'osx'
        else:
            raise UserException("unsupported host platform")

        return '{0}-{1}'.format(main_target, 8 * struct.calcsize('P'))


if __name__ == '__main__':

    import argparse

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('--specification', help="the JSON specification file")
    parser.add_argument('--target', help="the target platform")
    parser.add_argument('--verbose', help="enable verbose progress messages",
            action='store_true')

    args = parser.parse_args()

    # Build the sysroot images.
    TargetSpecifications(args.target, args.specification).build(args.verbose)
