#!/usr/bin/env python3


###############################################################################
# Copyright (c) 2016 Riverbank Computing Limited.
###############################################################################


import sys

from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QLabel, QTreeView, QVBoxLayout,
        QWidget)
from sip import SIP_VERSION_STR

try:
    from pdytools import hexversion as pdy_hexversion
except ImportError:
    pdy_hexversion = 0


class View(QTreeView):
    """ A read-only view for displaying a model. """

    def __init__(self, title):
        """ Initialise the object. """

        super().__init__(windowTitle=title)

        self.setRootIsDecorated(False)
        self.setEditTriggers(self.EditTrigger(0))


class Model(QStandardItemModel):
    """ A model containing a collection of interesting values. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__()

        self.setHorizontalHeaderLabels(["Name", "Value"])

        # Populate the model.
        self.add_value("PyQt version", PYQT_VERSION_STR)
        self.add_value("Python version", self.from_hexversion(sys.hexversion))
        self.add_value("Qt version", QT_VERSION_STR)
        self.add_value("sip version", SIP_VERSION_STR)
        self.add_value("sys.path", str(sys.path))
        self.add_value("sys.meta_path", str(sys.meta_path))

    def add_value(self, name, value):
        """ Add a name/value pair to the model. """

        self.appendRow([QStandardItem(name), QStandardItem(value)])

    @staticmethod
    def from_hexversion(hexversion):
        """ Convert a hexadecimal version number to a string. """

        return '%s.%s.%s' % ((hexversion >> 24) & 0xff,
                (hexversion >> 16) & 0xff, (hexversion >> 8) & 0xff)


# Create the GUI.
app = QApplication(sys.argv)

view = View("PyQt Demo")
view.setModel(Model())

shell = QWidget()
shell_layout = QVBoxLayout()

header = QLabel("""<p>
This is a simple Python application using the PyQt bindings for the
cross-platform Qt application framework.
</p>
<p>
It will run on OSX, Linux, Windows, iOS and Android without changes to the
source code.
</p>
<p>
For more information about PyQt go to
<a href="https://www.riverbankcomputing.com">www.riverbankcomputing.com</a>.
</p>""")
header.setOpenExternalLinks(True)
header.setTextFormat(Qt.RichText)
header.setWordWrap(True)
shell_layout.addWidget(header)

shell_layout.addWidget(view)

if pdy_hexversion != 0:
    footer = "It is a self-contained executable created using pyqtdeploy v%s." % Model.from_hexversion(pdy_hexversion)
    shell_layout.addWidget(QLabel(footer))

shell.setLayout(shell_layout)

# Show the GUI and interact with it.
shell.show()
app.exec()

# All done.
sys.exit()
