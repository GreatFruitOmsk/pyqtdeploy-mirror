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

from . import MessageHandler, UserException


def main():
    """ The entry point for the setuptools generated pyqtdeploycli wrapper. """

    # Get the default Android API level.  This is the level that Python v3.6.0
    # targets.
    default_api = 21

    parts = os.environ.get('ANDROID_NDK_PLATFORM', '').split('-')

    if len(parts) == 2 and parts[0] == 'android':
        try:
            default_api = int(parts[1])
        except ValueError:
            pass

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('action', help="the action to perform",
            choices=('build', 'configure'))
    parser.add_argument('--android-api',
            help="the Android API level to target when configuring Python "
                    "(configure) [default: {}]".format(default_api),
            metavar="LEVEL", type=int, default=default_api)
    parser.add_argument('--disable-patches',
            help="disable the patching of the Python source code (configure)",
            action='store_true')
    parser.add_argument('--enable-dynamic-loading',
            help="enable the dynamic loading of modules (configure)",
            action='store_true')
    parser.add_argument('--include-dir',
            help="the target Python include directory (build)", metavar="DIR")
    parser.add_argument('--interpreter',
            help="the host interpreter executable (build)",
            metavar="EXECUTABLE")
    parser.add_argument('--opt',
            help="the optimisation level where 0 is none, 1 is no asserts, 2 "
                    "is no asserts or docstrings (build) [default: 2]",
            metavar="LEVEL", type=int, choices=range(3), default=2),
    parser.add_argument('--output',
            help="the name of the output file or directory (configure, build)",
            metavar="OUTPUT")
    parser.add_argument('--package', help="the package name (configure)",
            metavar="PACKAGE")
    parser.add_argument('--project', help="the project file (build)",
            metavar="FILE")
    parser.add_argument('--python-library',
            help="the target Python library (build)", metavar="LIB")
    parser.add_argument('--resources',
            help="the number of .qrc resource files to generate (build) "
                    "[default: 1]",
            metavar="NUMBER", type=int, default=1),
    parser.add_argument('--source-dir',
            help="the Python source code directory (build)", metavar="DIR")
    parser.add_argument('--standard-library-dir',
            help="the target Python standard library directory (build)",
            metavar="DIR")
    parser.add_argument('--target', help="the target platform (configure)",
            metavar="TARGET")
    parser.add_argument('--timeout',
            help="the number of seconds to wait for build processes to run "
                    "before timing out (build)",
            metavar="SECONDS", type=int, default=30)
    parser.add_argument('--quiet', help="disable progress messages (build)",
            action='store_true')
    parser.add_argument('--verbose',
            help="enable verbose progress messages (configure, build)",
            action='store_true')

    args = parser.parse_args()

    # Handle the specific actions.
    message_handler = MessageHandler(args.quiet, args.verbose)

    if args.action == 'build':
        rc = build(args, message_handler)
    elif args.action == 'configure':
        rc = configure(args, message_handler)
    else:
        # This should never happen.
        rc = 1

    return rc


def build(args, message_handler):
    """ Perform the build action. """

    if args.project is None:
        missing_argument('--project', message_handler)
        return 2

    if args.resources < 1:
        message_handler.error(
                "error: argument --resources: number must be at least 1")
        return 2

    from . import Builder, Project

    try:
        builder = Builder(Project.load(args.project), message_handler)
        builder.build(args.opt, args.resources, args.timeout,
                build_dir=args.output, include_dir=args.include_dir,
                interpreter=args.interpreter,
                python_library=args.python_library, source_dir=args.source_dir,
                standard_library_dir=args.standard_library_dir)
    except UserException as e:
        message_handler.exception(e)
        return 1

    return 0


def configure(args, message_handler):
    """ Perform the configure action. """

    if args.package is None:
        missing_argument('--package', message_handler)
        return 2

    if args.package == 'python':
        from . import configure_python

        try:
            configure_python(args.target, args.output, args.android_api,
                    args.enable_dynamic_loading, not args.disable_patches,
                    message_handler)
        except UserException as e:
            message_handler.exception(e)
            return 1
    else:
        from . import configure_package

        try:
            configure_package(args.package, args.target, args.output)
        except UserException as e:
            message_handler.exception(e)
            return 1

    return 0


def missing_argument(name, message_handler):
    """ Tell the user about a missing argument. """

    # Mimic the argparse message.
    message_handler.error(
            "error: the following arguments are required: {0}".format(name))
