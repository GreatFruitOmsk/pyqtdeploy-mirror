#!/usr/bin/env python3

# Copyright (c) 2014, Riverbank Computing Limited
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
import sys


# The entry point for the setuptools generated wrapper.
def main():
    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument('project_file', help="the project file", nargs='?',
            metavar="FILE")
    parser.add_argument('--build', help="build the project in DIR",
            metavar="DIR")
    parser.add_argument('--quiet', help="disable build progress messages",
            action='store_true')
    parser.add_argument('--verbose',
            help="enable verbose build progress messages", action='store_true')

    args = parser.parse_args()

    # Handle the specific actions.
    if args.build is not None:
        if args.project_file is None:
            # Mimic the argparse message.
            print("{0}: error: the following arguments are required: FILE".format(os.path.basename(sys.argv[0])),
                    file=sys.stderr)
            return 2

        from . import Builder, Project, UserException

        try:
            builder = Builder(Project.load(args.project_file))
            builder.quiet = args.quiet
            builder.verbose = args.verbose
            builder.build(args.build)
        except UserException as e:
            print("{0}: {1}".format(os.path.basename(sys.argv[0]), e.text),
                    file=sys.stderr)
            return 1

        rc = 0
    else:
        from PyQt5.QtWidgets import QApplication

        from . import Project, ProjectGUI

        app = QApplication(sys.argv, applicationName='pyqtdeploy',
                organizationDomain='riverbankcomputing.com',
                organizationName='Riverbank Computing')

        if args.project_file is None:
            project = Project()
        else:
            project = ProjectGUI.load(args.project_file)
            if project is None:
                return 1

        gui = ProjectGUI(project)
        gui.show()

        rc = app.exec()

    return rc
