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

parser.add_argument("in_file", help="the input file, usually a project file",
        nargs='?', metavar='FILE')
parser.add_argument("--freeze", help="freeze FILE to the C file C-FILE",
        metavar='C-FILE')

args = parser.parse_args()

# Handle the specific actions.
if args.freeze is not None:
    from pyqtdeploy import freeze_as_c

    if args.in_file is None:
        # Mimic the argparse message.
        print("{0}: error: the following arguments are required: FILE".format(sys.argv[0]),
                file=sys.stderr)
        sys.exit(1)

    freeze_as_c(args.in_file, args.freeze)
else:
    from PyQt5.QtWidgets import QApplication
    from pyqtdeploy import ProjectGUI

    app = QApplication(sys.argv, organizationName='Riverbank Computing')

    gui = ProjectGUI()

    if args.in_file is not None:
        gui.load(args.in_file)

    gui.show()

    app.exec()

# All done.
sys.exit()
