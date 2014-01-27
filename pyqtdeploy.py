#!/usr/bin/env python3

# Copyright (c) 2014 Riverbank Computing Limited.
#
# This file is part of pyqtdeploy.
#
# This file may be used under the terms of the GNU General Public License
# v2 or v3 as published by the Free Software Foundation which can be found in
# the files LICENSE-GPL2.txt and LICENSE-GPL3.txt included in this package.
# In addition, as a special exception, Riverbank gives you certain additional
# rights.  These rights are described in the Riverbank GPL Exception, which
# can be found in the file GPL-Exception.txt in this package.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


import argparse
import sys


# Parse the command line.
parser = argparse.ArgumentParser()

parser.add_argument('project_file', help="the project file", nargs='?',
        metavar="FILE")
parser.add_argument('--build', help="build the project in DIR", metavar="DIR")

args = parser.parse_args()


# Handle the specific actions.
if args.build is not None:
    if args.project_file is None:
        # Mimic the argparse message.
        print("{0}: error: the following arguments are required: FILE".format(sys.argv[0]),
                file=sys.stderr)
        sys.exit(2)

    from pyqtdeploy import Builder, Project, UserException

    try:
        Builder(Project.load(args.project_file)).build(args.build)
    except UserException as e:
        print("{0}: {1}".format(sys.argv[0], e.text), file=sys.stderr)
        sys.exit(1)
else:
    from PyQt5.QtWidgets import QApplication
    from pyqtdeploy import Project, ProjectGUI

    app = QApplication(sys.argv, organizationName='Riverbank Computing')

    if args.project_file is None:
        project = Project()
    else:
        project = ProjectGUI.load(args.project_file)
        if project is None:
            sys.exit(1)

    gui = ProjectGUI(project)
    gui.show()

    app.exec()


# All done.
sys.exit()
