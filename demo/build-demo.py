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


import argparse
import os
import subprocess
import sys


def run(args):
    """ Run a command and terminate if it fails. """

    try:
        ec = subprocess.call(' '.join(args), shell=True)
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
        ec = 1

    if ec:
        sys.exit(ec)


# Parse the command line.
parser = argparse.ArgumentParser()
parser.add_argument('--no-sysroot', help="do not build the sysroot",
        action='store_true')
parser.add_argument('--sources',
        help="the directory containing the source packages", metavar="DIR")
parser.add_argument('--target', help="the target platform", default='')
parser.add_argument('--quiet', help="disable progress messages",
        action='store_true')
parser.add_argument('--verbose', help="enable verbose progress messages",
        action='store_true')
cmd_line_args = parser.parse_args()
build_sysroot = not cmd_line_args.no_sysroot
sources = cmd_line_args.sources
target = cmd_line_args.target
quiet = cmd_line_args.quiet
verbose = cmd_line_args.verbose

if sources:
    sources = os.path.abspath(sources)
else:
    sources = 'src'

# Pick a default target if none is specified.
if not target:
    if sys.platform == 'win32':
        # Look for a 64-bit compiler.
        arch = '64' if os.environ.get('Platform') == 'X64' else '32'
        target = 'win-' + arch
    elif sys.platform == 'darwin':
        target = 'macos-64'
    elif sys.platform.startswith('linux'):
        import struct

        target = 'linux-{0}'.format(8 * struct.calcsize('P'))
    else:
        print("Unsupported platform:", sys.platform, file=sys.stderr)
        sys.exit(2)

# Anchor everything from the directory containing this script.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

sysroot_dir = 'sysroot-' + target
build_dir = 'build-' + target
host_bin_dir = os.path.abspath(os.path.join(sysroot_dir, 'host', 'bin'))

# Build sysroot.
if build_sysroot:
    args = ['pyqtdeploy-sysroot', '--target', target, '--sysroot', sysroot_dir,
            '--source-dir', sources]

    if quiet:
        args.append('--quiet')

    if verbose:
        args.append('--verbose')

    args.append('sysroot.json')

    run(args)

# Build the demo.
run(['pyqtdeploy-build', '--target', target, '--sysroot', sysroot_dir,
            '--build-dir', build_dir, 'pyqt-demo.pdy'])

# Run qmake.  Use the qmake left by pyqtdeploy-sysroot.
os.chdir(build_dir)
run([os.path.join(host_bin_dir, 'qmake')])

# Run make. (When targeting iOS we leave it to Xcode.)
if target.startswith('ios'):
    pass
else:
    # We only support MSVC on Windows.
    make = 'nmake' if sys.platform == 'win32' else 'make'

    run([make])

    if target.startswith('android'):
        run([make, 'INSTALL_ROOT=deploy', 'install'])
        run([os.path.join(host_bin_dir, 'androiddeployqt'), '--input',
                'android-libpyqt-demo.so-deployment-settings.json', '--output',
                'deploy'])

# Tell the user where the demo is.
if target.startswith('android'):
    apk_dir = os.path.join(build_dir, 'deploy', 'bin')
    print("""The QtApp-debug.apk file can be found in the '{0}'
directory.  Run adb to install it to a simulator.""".format(apk_dir))

elif target.startswith('ios'):
    print("""The pyqt-demo.xcodeproj file can be found in the '{0}' directory.
Run Xcode to build the app and run it in the simulator or deploy it to a
device.""".format(build_dir))

elif target.startswith('win') or sys.platform == 'win32':
    print("The pyqt-demo executable can be found in the '{0}' directory.".format(os.path.join(build_dir, 'release')))

else:
    print("The pyqt-demo executable can be found in the '{0}' directory.".format(build_dir))
