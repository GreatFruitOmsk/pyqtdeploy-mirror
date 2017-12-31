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

from . import (Builder, MessageHandler, Project, PYQTDEPLOY_RELEASE,
        UserException)


def main():
    """ The entry point for the setuptools generated pyqtdeploy-build wrapper.
    """

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('--build-dir', help="the name of the build directory",
            metavar="DIR")
    parser.add_argument('--include-dir',
            help="the target Python include directory", metavar="DIR")
    parser.add_argument('--interpreter',
            help="the host interpreter executable",
            metavar="EXECUTABLE")
    parser.add_argument('--no-clean',
            help="do not delete and re-create the build directory before "
                    "starting",
            dest='clean', default=True, action='store_false')
    parser.add_argument('--opt',
            help="the optimisation level where 0 is none, 1 is no asserts, 2 "
                    "is no asserts or docstrings [default: 2]",
            metavar="LEVEL", type=int, choices=range(3), default=2),
    parser.add_argument('--python-library', help="the target Python library",
            metavar="LIB")
    parser.add_argument('--resources',
            help="the number of .qrc resource files to generate [default: 1]",
            metavar="NUMBER", type=int, default=1),
    parser.add_argument('--source-dir',
            help="the Python source code directory", metavar="DIR")
    parser.add_argument('--standard-library-dir',
            help="the target Python standard library directory", metavar="DIR")
    parser.add_argument('--sysroot', help="the system image root directory",
            metavar="DIR")
    parser.add_argument('--target', help="the target architecture"),
    parser.add_argument('--quiet', help="disable progress messages",
            action='store_true')
    parser.add_argument('--verbose', help="enable verbose progress messages",
            action='store_true')
    parser.add_argument('-V', '--version', action='version',
            version=PYQTDEPLOY_RELEASE)
    parser.add_argument('project', help="the project to build")

    args = parser.parse_args()

    # Perform the build.
    message_handler = MessageHandler(args.quiet, args.verbose)

    if args.resources < 1:
        message_handler.error(
                "error: argument --resources: number must be at least 1")
        return 2

    try:
        builder = Builder(Project.load(args.project), args.target,
                message_handler)

        builder.build(args.opt, args.resources, args.clean, args.sysroot,
                build_dir=args.build_dir, include_dir=args.include_dir,
                interpreter=args.interpreter,
                python_library=args.python_library, source_dir=args.source_dir,
                standard_library_dir=args.standard_library_dir)
    except UserException as e:
        message_handler.exception(e)
        return 1

    return 0
