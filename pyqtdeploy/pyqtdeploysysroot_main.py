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


import argparse
import os

from . import MessageHandler, PYQTDEPLOY_RELEASE, Sysroot, UserException


def main():
    """ The entry point for the setuptools generated pyqtdeploy-sysroot
    wrapper.
    """

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('--component', help="the component name to build",
            action='append')
    parser.add_argument('--no-clean',
            help="do not remove the temporary build directory",
            action='store_true')
    parser.add_argument('--options',
            help="show the options available for the components",
            action='store_true')
    parser.add_argument('--plugin-dir',
            help="search a directory for component plugins", metavar="DIR",
            action='append')
    parser.add_argument('--source-dir',
            help="a directory containing the source archives",
            metavar="DIR", dest='source_dirs', action='append')
    parser.add_argument('--sysroot', help="the system image root directory",
            metavar="DIR")
    parser.add_argument('--target', help="the target architecture"),
    parser.add_argument('--quiet', help="disable progress messages",
            action='store_true')
    parser.add_argument('--verbose', help="enable verbose progress messages",
            action='store_true')
    parser.add_argument('-V', '--version', action='version',
            version=PYQTDEPLOY_RELEASE)
    parser.add_argument('specification',
            help="JSON specification of the system image root directory")

    args = parser.parse_args()

    # Perform the required action.
    message_handler = MessageHandler(args.quiet, args.verbose)

    try:
        sysroot_dir = args.sysroot
        if not sysroot_dir:
            sysroot_dir = os.environ.get('SYSROOT')

        sysroot = Sysroot(sysroot_dir, args.specification, args.plugin_dir,
                args.source_dirs, args.target, message_handler)

        if args.options:
            sysroot.show_options(args.component)
        else:
            sysroot.build_components(args.component, args.no_clean)
    except UserException as e:
        message_handler.exception(e)
        return 1

    return 0
