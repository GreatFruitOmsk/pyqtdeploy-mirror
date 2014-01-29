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


from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QPushButton,
        QTreeWidget, QTreeWidgetItem, QVBoxLayout)


class MfsPackageEditor(QGroupBox):
    """ A memory file system package editor. """

    # Emitted when the package has changed.
    package_changed = pyqtSignal()

    def __init__(self, title):
        """ Initialise the editor. """

        super().__init__(title)

        self._package = None
        self._title = title
        self._previous_scan = ''

        layout = QHBoxLayout()

        self._package_edit = QTreeWidget()
        self._package_edit.setHeaderLabels(["Name", "Included"])
        layout.addWidget(self._package_edit)

        scan_layout = QVBoxLayout()

        scan_layout.addWidget(QPushButton("Scan...", clicked=self._scan))

        self._exclusions_edit = QTreeWidget()
        self._exclusions_edit.setHeaderLabels(["Exclusions"])
        self._exclusions_edit.setEditTriggers(
                QTreeWidget.DoubleClicked|QTreeWidget.SelectedClicked|
                        QTreeWidget.EditKeyPressed)
        self._exclusions_edit.setRootIsDecorated(False)
        self._exclusions_edit.itemChanged.connect(self._exclusion_changed)

        scan_layout.addWidget(self._exclusions_edit)

        layout.addLayout(scan_layout)

        self.setLayout(layout)

    def setPackage(self, package):
        """ Update the editor with the contents of the given package. """

        # TODO - set contents.

        # Set the exclusions.
        self._exclusions_edit.clear()

        for exclude in package.exclusions:
            self._add_exclusion_item(QTreeWidgetItem([exclude]))

        # Add one to be edited to create a new entry.
        self._add_exclusion_item(QTreeWidgetItem())

        # Save the package.
        self._package = package

    def _add_exclusion_item(self, itm):
        """ Add a QTreeWidgetItem that holds an exclusion. """

        itm.setFlags(
                Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled|
                        Qt.ItemNeverHasChildren)

        self._exclusions_edit.addTopLevelItem(itm)

    def _exclusion_changed(self, itm, column):
        """ Invoked when an exclusion has changed. """

        exc_edit = self._exclusions_edit

        new_exc = itm.data(column, Qt.DisplayRole)
        itm_index = exc_edit.indexOfTopLevelItem(itm)

        if new_exc != '':
            # See if we have added a new one.
            if itm_index == exc_edit.topLevelItemCount() - 1:
                self._add_exclusion_item(QTreeWidgetItem())
        else:
            # It is empty so remove it.
            exc_edit.takeTopLevelItem(itm_index)

        # Save the new exclusions.
        self._package.exclusions = [
                exc_edit.topLevelItem(i).data(column, Qt.DisplayRole)
                        for i in range(exc_edit.topLevelItemCount() - 1)]

        self.package_changed.emit()

    def _scan(self, value):
        """ Invoked when the user clicks on the scan button. """

        name = QFileDialog.getExistingDirectory(self._package_edit,
                self._title, self._previous_scan)

        if name != '':
            self._previous_scan = name

            print("Scanning", name)

            # TODO - emit a signal so the project.modified can be set.
