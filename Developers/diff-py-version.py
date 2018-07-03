#!/usr/bin/env python3
#
# Copyright (c) 2017, Riverbank Computing Limited
# All rights reserved.


import argparse
import glob
import os
import shutil
import sys
import tarfile


class Version:
    """ Encapsulate a version. """

    # The 'Lib' sub-directories to ignore.
    IGNORED_LIB_DIRS = ('bsddb/test', 'ctypes/test', 'distutils/tests',
            'ensurepip', 'idlelib', 'lib-tk', 'lib2to3', 'pydoc_data',
            'site-packages', 'sqlite3/test', 'test', 'tkinter', 'turtledemo',
            'unittest', 'venv')

    def __init__(self, major, minor, patch):
        """ Initialise the object. """

        self.major = major
        self.minor = minor
        self.patch = patch

    def basename(self):
        """ Return the basename of the directory that will contain the
        extracted source.
        """

        return 'Python-' + str(self)

    def configure(self):
        """ Configure the package. """

        progress("Configuring {0}".format(self.basename()))

        os.chdir(self.basename())
        os.system('./configure >/dev/null')
        os.chdir('..')

    def unpack(self, sources):
        """ Unpack the source package and return the name of the source
        directory.
        """

        # Make sure the source directory doesn't already exist.
        basename = self.basename()

        if os.path.isdir(basename):
            shutil.rmtree(basename)
        elif os.path.exists(basename):
            error("{0} already exists but isn't a directory".format(basename))

        package = self._package(sources)

        progress("Unpacking {0}".format(package))
        tar = tarfile.open(package)
        tar.extractall()
        tar.close()

        # Delete those 'Lib' sub-directories that we are not interested in.
        for d in self.IGNORED_LIB_DIRS:
            d_path = os.path.join(basename, 'Lib', d)
            if os.path.isdir(d_path):
                shutil.rmtree(d_path)

        return basename

    @classmethod
    def version(cls, version_str):
        """ Create a Version instance for a given version string. """

        # Parse the version number.
        parts = version_str.split('.')
        if len(parts) == 2:
            parts.append('0')

        if len(parts) != 3:
            error("a version number must in the form major.minor[.patch]")

        int_parts = []
        for p in parts:
            try:
                int_p = int(p)
            except ValueError:
                error("version part '{0}' must be an integer".format(p))

            if int_p < 0 or int_p > 255:
                error("version part '{0}' must be in the range 0..255".format(
                        int_p))

            int_parts.append(int_p)

        return cls(*int_parts)

    def __int__(self):
        """ Return the version as a single integer. """

        return (self.major << 16) + (self.minor << 8) + self.patch

    def __str__(self):
        """ Return the version as a string. """

        return '{0}.{1}.{2}'.format(self.major, self.minor, self.patch)

    def _package(self, sources):
        """ Return the absolute pathname of the source package. """

        pattern = os.path.join(sources, self.basename() + '.*')
        packages = glob.glob(pattern)

        if len(packages) == 0:
            error("unable to find the source package for v{0} in {1}".format(
                    str(self), sources))

        return packages[0]


def error(message, error_code=1):
    """ Display an error message and quit. """

    sys.stderr.write(
            "{0}: {1}.\n".format(os.path.basename(sys.argv[0]), message))

    sys.exit(error_code)


def progress(message):
    """ Display a progress message. """

    sys.stdout.write(message + "...\n")


def diff_directories(name, base_version, py_version, suffix=''):
    """ Create a diff between two directories. """

    return run_diff('-ruN', name, base_version, py_version, suffix)


def diff_files(name, base_version, py_version, suffix=''):
    """ Create a diff between two files. """

    return run_diff('-u', name, base_version, py_version, suffix)


def run_diff(flags, name, base_version, py_version, suffix):
    """ Run a diff command and return the name of the file containing the diff.
    """

    name1 = os.path.join(base_version.basename(), name)
    name2 = os.path.join(py_version.basename(), name)
    output = '{0}-{1}-{2}.diff{3}'.format(os.path.basename(name), base_version,
            py_version, suffix)

    try:
        os.remove(output)
    except FileNotFoundError:
        pass

    progress("Creating diff for {0}".format(name))
    cmd = 'diff {0} {1} {2} >{3}'.format(flags, name1, name2, output)
    os.system(cmd)

    if not os.path.exists(output):
        error("'{0}' failed".format(cmd), error_code)

    return output


def process_lib_diff(diff, f):
    """ If a single lib is relevant then write it to a file. """

    for line in diff:
        if 'import' in line and line[0] in '+-':
            f.write(''.join(diff))
            break


# Parse the command line.
parser = argparse.ArgumentParser()
parser.add_argument('--base',
        help="the base version to create the diffs against", metavar="VERSION")
parser.add_argument('--sources',
        help="the directory containing the source packages", metavar="DIR")
parser.add_argument('version',
        help="the version of Python to create the diffs for")

args = parser.parse_args()

sources = os.path.abspath(args.sources if args.sources else '.')

# Determine the Python version and the base version.
py_version = Version.version(args.version)

if args.base:
    base_version = Version.version(args.base)

    # Some sanity checks.
    if py_version.major != base_version.major:
        error("the base version must have the same major version number")

    if int(py_version) < int(base_version):
        error("the base version must be earlier")
elif py_version.patch == 0:
    error("use the --base option to specifiy the previous Python version")
else:
    base_version = Version(py_version.major, py_version.minor,
            py_version.patch - 1)

# Get the source directories.
py_source = py_version.unpack(sources)
base_source = base_version.unpack(sources)

# Create the diffs.
diff_files('setup.py', base_version, py_version)
diff_files('pyconfig.h.in', base_version, py_version)
diff_files('PC/pyconfig.h', base_version, py_version)
raw_lib_diff = diff_directories('Lib', base_version, py_version, suffix='.raw')

if py_version.major == 3:
    diff_files('Lib/importlib/_bootstrap.py', base_version, py_version)

    if int(py_version) >= 0x030500:
        diff_files('Lib/importlib/_bootstrap_external.py', base_version,
                py_version)

base_version.configure()
py_version.configure()
diff_files('Makefile', base_version, py_version)

# Filter the 'Lib' diff to exclude anything that doesn't involve 'import'.
lib_diff = raw_lib_diff[:-4]

progress("Filtering {0}".format(lib_diff))

raw_lib_f = open(raw_lib_diff)
lib_f = open(lib_diff, 'w')

diff = []
for line in raw_lib_f.readlines():
    if line.startswith('diff '):
        if diff:
            process_lib_diff(diff, lib_f)
            diff = []

    diff.append(line)

if diff:
    process_lib_diff(diff, lib_f)

raw_lib_f.close()
lib_f.close()

os.remove(raw_lib_diff)

# Delete the base version source directory.
progress("Removing {0}".format(base_source))
shutil.rmtree(base_source)
