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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QPushButton,
        QTreeWidget, QVBoxLayout)


class MfsPackageEditor(QGroupBox):
    """ A memory file system package editor. """

    def __init__(self, title):
        """ Initialise the editor. """

        super().__init__(title)

        self._package = None
        self._title = title
        self._previous_scan = ''

        layout = QHBoxLayout()

        self._package_edit = QTreeWidget()
        header = self._package_edit.headerItem()
        header.setData(0, Qt.DisplayRole, "Name")
        header.setData(1, Qt.DisplayRole, "Included")
        layout.addWidget(self._package_edit)

        scan_layout = QVBoxLayout()

        scan_layout.addWidget(QPushButton("Scan...", clicked=self._scan))

        self._exclusions_edit = QTreeWidget()
        header = self._exclusions_edit.headerItem()
        header.setData(0, Qt.DisplayRole, "Exclusions")

        scan_layout.addWidget(self._exclusions_edit)

        layout.addLayout(scan_layout)

        self.setLayout(layout)

    def setPackage(self, package):
        """ Update the editor with the contents of the given package. """

        print("Setting package")

        # TODO
        self._package = package

    def _scan(self, value):
        """ Invoked when the user clicks on the scan button. """

        name = QFileDialog.getExistingDirectory(self._package_edit,
                self._title, self._previous_scan)

        if name != '':
            self._previous_scan = name

            print("Scanning", name)

            # TODO - emit a signal so the project.modified can be set.
