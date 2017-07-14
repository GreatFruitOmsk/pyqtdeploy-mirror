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

from . import MessageHandler, PYQTDEPLOY_RELEASE, Sysroot, UserException


def main():
    """ The entry point for the setuptools generated pyqtdeploysysroot wrapper.
    """

    # Parse the command line.
    parser = argparse.ArgumentParser()

    #parser.add_argument('--android-api',
    #        help="the Android API level to target when configuring Python "
    #                "(configure) [default: {}]".format(default_api),
    #        metavar="LEVEL", type=int, default=default_api)
    parser.add_argument('--debug', help="build debug versions where possible")
    #parser.add_argument('--disable-patches',
    #        help="disable the patching of the Python source code (configure)",
    #        action='store_true')
    #parser.add_argument('--enable-dynamic-loading',
    #        help="enable the dynamic loading of modules (configure)",
    #        action='store_true')
    #parser.add_argument('--include-dir',
    #        help="the target Python include directory (build)", metavar="DIR")
    #parser.add_argument('--interpreter',
    #        help="the host interpreter executable (build)",
    #        metavar="EXECUTABLE")
    #parser.add_argument('--opt',
    #        help="the optimisation level where 0 is none, 1 is no asserts, 2 "
    #                "is no asserts or docstrings (build) [default: 2]",
    #        metavar="LEVEL", type=int, choices=range(3), default=2),
    parser.add_argument('--options',
            help="show the options available for the packages",
            action='store_true')
    #parser.add_argument('--output',
    #        help="the name of the output file or directory (configure, build)",
    #        metavar="OUTPUT")
    parser.add_argument('--package', help="the package name to build",
            metavar="PACKAGE", action='append')
    parser.add_argument('--plugin-path',
            help="the directories searched for package plugins",
            metavar="PATH")
    #parser.add_argument('--project', help="the project file (build)",
    #        metavar="FILE")
    #parser.add_argument('--python-library',
    #        help="the target Python library (build)", metavar="LIB")
    #parser.add_argument('--resources',
    #        help="the number of .qrc resource files to generate (build) "
    #                "[default: 1]",
    #        metavar="NUMBER", type=int, default=1),
    #parser.add_argument('--source-dir',
    #        help="the Python source code directory (build)", metavar="DIR")
    #parser.add_argument('--standard-library-dir',
    #        help="the target Python standard library directory (build)",
    #        metavar="DIR")
    parser.add_argument('--sysroot', help="the system image root directory",
            metavar="DIR")
    #parser.add_argument('--system-python',
    #        help="use the system installed Python (install)",
    #        metavar="VERSION")
    parser.add_argument('--target', help="the target platform",
            metavar="TARGET")
    #parser.add_argument('--timeout',
    #        help="the number of seconds to wait for build processes to run "
    #                "before timing out (build)",
    #        metavar="SECONDS", type=int, default=30)
    parser.add_argument('--quiet', help="disable progress messages",
            action='store_true')
    parser.add_argument('--verbose', help="enable verbose progress messages",
            action='store_true')
    parser.add_argument('-V', '--version', action='version',
            version=PYQTDEPLOY_RELEASE)
    parser.add_argument('json',
            help="JSON specification of the system image root directory")

    args = parser.parse_args()

    # Perform the required actions.
    message_handler = MessageHandler(args.quiet, args.verbose)

    try:
        sysroot = Sysroot(args.sysroot, args.json, args.plugin_path,
                args.target, message_handler)

        if args.options:
            sysroot.show_options(args.package)
        else:
            sysroot.build_packages(args.package)
    except UserException as e:
        message_handler.exception(e)
        return 1

    return 0
