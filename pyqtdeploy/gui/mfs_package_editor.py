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


import fnmatch
import os

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QFileDialog, QGroupBox, QHBoxLayout, QPushButton,
        QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QVBoxLayout)

from ..project import MfsDirectory, MfsFile


class MfsPackageEditor(QGroupBox):
    """ A memory file system package editor. """

    # Emitted when the package has changed.
    package_changed = pyqtSignal()

    def __init__(self, title, scanning=''):
        """ Initialise the editor. """

        super().__init__(title)

        self._package = None
        self._project = None
        self._root = None
        self._title = title

        layout = QHBoxLayout()

        self._package_edit = QTreeWidget()
        self._package_edit.header().hide()
        self._package_edit.itemChanged.connect(self._package_changed)
        layout.addWidget(self._package_edit, stretch=1)

        scan_layout = QVBoxLayout()

        text = "Scan"
        if scanning != '':
            text += ' '
            text += scanning

        scan_layout.addWidget(QPushButton(text, clicked=self._scan))

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

    def configure(self, package, project, root=None):
        """ Configure the editor with the contents of the given package,
        project and optional root directory.
        """

        # Save the configuration.
        self._package = package
        self._project = project
        self._root = root

        # Set the package itself.
        self._visualise()

        # Set the exclusions.
        self._exclusions_edit.clear()

        for exclude in package.exclusions:
            self._add_exclusion_item(QTreeWidgetItem([exclude]))

        # Add one to be edited to create a new entry.
        self._add_exclusion_item(QTreeWidgetItem())

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

        package = self._package
        project = self._project

        # Get the root directory to scan if there is not a fixed root.
        if self._root is not None:
            root = self._root
        else:
            orig = default = package.name
            if default != '':
                default = project.absolute_path(default)

            root = QFileDialog.getExistingDirectory(self._package_edit,
                    self._title, default)

            if root == '':
                return

            package.name = project.relative_path(root)

        # Save the included state of any existing contents so that they can be
        # restored after the scan.
        old_state = {}
        it = QTreeWidgetItemIterator(self._package_edit)

        # Skip the root of the tree.
        it += 1

        itm = it.value()
        while itm is not None:
            rel_path = [itm.data(0, Qt.DisplayRole)]

            parent = itm.parent()
            while parent is not None:
                rel_path.append(parent.data(0, Qt.DisplayRole))
                parent = parent.parent()

            rel_path.reverse()

            old_state[os.path.join(*rel_path)] = (itm.checkState(0) == Qt.Checked)

            it += 1
            itm = it.value()

        # Walk the package.
        self._add_to_container(package, root, os.listdir(root), [], old_state)
        self._visualise()

        self.package_changed.emit()

    def _add_to_container(self, container, path, path_contents, dir_stack, old_state):
        """ Add the files and directories of a package or sub-package to a
        container.
        """

        dir_stack.append(os.path.basename(path))
        contents = []

        for name in path_contents:
            # Apply any exclusions.
            for exc in self._package.exclusions:
                if fnmatch.fnmatch(name, exc):
                    name = None
                    break

            if name is None:
                continue

            # See if we already know the included state.
            rel_path = os.path.join(os.path.join(*dir_stack), name)
            included = old_state.get(rel_path)

            # Add the content.
            full_name = os.path.join(path, name)

            if os.path.isdir(full_name):
                # Look ahead to see if the directory is a sub-package.  If not,
                # and it is new in this scan, then we exclude it.
                new_path_contents = os.listdir(full_name)

                if included is None:
                    included = ('__init__.py' in new_path_contents)

                mfs = MfsDirectory(name, included)

                self._add_to_container(mfs, full_name, new_path_contents,
                        dir_stack, old_state)
            elif os.path.isfile(full_name):
                if included is None:
                    included = True

                mfs = MfsFile(name, included)
            else:
                continue

            contents.append(mfs)

        contents.sort(key=lambda mfs: mfs.name.lower())
        container.contents = contents
        dir_stack.pop()

    def _visualise(self):
        """ Update the GUI with the package content. """

        blocked = self._package_edit.blockSignals(True)

        self._package_edit.clear()

        if self._root is not None:
            parent = self._package_edit
        else:
            parent = QTreeWidgetItem([self._package.name])
            self._package_edit.addTopLevelItem(parent)
            parent.setExpanded(True)

        self._visualise_contents(self._package.contents, parent)

        self._package_edit.blockSignals(blocked)

    def _visualise_contents(self, contents, parent):
        """ Visualise the contents for a parent. """

        for content in contents:
            itm = QTreeWidgetItem(parent, [content.name])
            itm.setCheckState(0, Qt.Checked if content.included else Qt.Unchecked)
            itm._mfs_item = content

            if isinstance(content, MfsDirectory):
                self._visualise_contents(content.contents, itm)
                itm.setExpanded(content.included)

    def _package_changed(self, itm, column):
        """ Invoked when part of the package changes. """

        itm._mfs_item.included = (itm.checkState(0) == Qt.Checked)

        self.package_changed.emit()
