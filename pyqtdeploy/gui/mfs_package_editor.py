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


import fnmatch
import os

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import (QGridLayout, QGroupBox, QPushButton, QTreeWidget,
        QTreeWidgetItem, QTreeWidgetItemIterator)

from ..project import MfsDirectory, MfsFile


class MfsPackageEditor(QGroupBox):
    """ A memory file system package editor. """

    # Emitted when the package has changed.
    package_changed = pyqtSignal()

    def __init__(self, title, show_root=False, scanning='', additional_exclusions=None):
        """ Initialise the editor. """

        super().__init__(title)

        self._package = None
        self._project = None
        self._title = title
        self._show_root = show_root
        self._additional_exclusions = additional_exclusions

        layout = QGridLayout()

        self._package_edit = QTreeWidget()
        self._package_edit.header().hide()
        self._package_edit.itemChanged.connect(self._package_changed)
        layout.addWidget(self._package_edit, 0, 0, 3, 1)

        text = "Scan"
        if scanning != '':
            text += ' '
            text += scanning

        layout.addWidget(QPushButton(text, clicked=self._scan), 0, 1, 1, 2)
        layout.addWidget(QPushButton("Include all", clicked=self._include_all),
                1, 1)
        layout.addWidget(QPushButton("Exclude all", clicked=self._exclude_all),
                1, 2)

        self._exclusions_edit = QTreeWidget()
        self._exclusions_edit.setHeaderLabels(["Exclusions"])
        self._exclusions_edit.setEditTriggers(
                QTreeWidget.DoubleClicked|QTreeWidget.SelectedClicked|
                        QTreeWidget.EditKeyPressed)
        self._exclusions_edit.setRootIsDecorated(False)
        self._exclusions_edit.itemChanged.connect(self._exclusion_changed)

        layout.addWidget(self._exclusions_edit, 2, 1, 1, 2)

        self.setLayout(layout)

    def configure(self, package, project):
        """ Configure the editor with the contents of the given package and
        project.
        """

        # Save the configuration.
        self._package = package
        self._project = project

        # Set the package itself.
        self._visualise()

        # Set the exclusions.
        self._exclusions_edit.clear()

        for exclude in package.exclusions:
            self._add_exclusion_item(exclude)

        # Add one to be edited to create a new entry.
        self._add_exclusion_item()

    def get_root_dir(self):
        """ Return the root directory to scan, or '' if there was an error or
        the user cancelled.
        """

        raise NotImplementedError

    def _add_exclusion_item(self, exclude=''):
        """ Add a QTreeWidgetItem that holds an exclusion. """

        itm = QTreeWidgetItem([exclude])

        itm.setFlags(
                Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled|
                        Qt.ItemNeverHasChildren)

        self._exclusions_edit.addTopLevelItem(itm)

    def _exclusion_changed(self, itm, _):
        """ Invoked when an exclusion has changed. """

        exc_edit = self._exclusions_edit

        new_exc = itm.data(0, Qt.DisplayRole).strip()
        itm_index = exc_edit.indexOfTopLevelItem(itm)

        if new_exc != '':
            # See if we have added a new one.
            if itm_index == exc_edit.topLevelItemCount() - 1:
                self._add_exclusion_item()
        else:
            # It is empty so remove it.
            exc_edit.takeTopLevelItem(itm_index)

        # Save the new exclusions.
        self._package.exclusions = [
                exc_edit.topLevelItem(i).data(0, Qt.DisplayRole).strip()
                        for i in range(exc_edit.topLevelItemCount() - 1)]

        self.package_changed.emit()

    def _get_items(self):
        """ Return an iterator over the tree widget items. """

        it = QTreeWidgetItemIterator(self._package_edit)

        if not self._show_root:
            it += 1

        itm = it.value()
        while itm is not None:
            yield itm
            it += 1
            itm = it.value()

    def _include_all(self, _):
        """ Invoked when the user clicks on the include all button. """

        for itm in self._get_items():
            itm.setCheckState(0, Qt.Checked)

    def _exclude_all(self, _):
        """ Invoked when the user clicks on the exclude all button. """

        for itm in self._get_items():
            itm.setCheckState(0, Qt.Unchecked)
            itm.setExpanded(False)

    def _scan(self, _):
        """ Invoked when the user clicks on the scan button. """

        project = self._project
        package = self._package

        # Get the root directory to scan.
        root = self.get_root_dir()
        if root == '':
            return

        # Save the included state of any existing contents so that they can be
        # restored after the scan.
        old_state = {}

        for itm in self._get_items():
            rel_path = [itm.data(0, Qt.DisplayRole)]

            parent = itm.parent()
            while parent is not None:
                rel_path.append(parent.data(0, Qt.DisplayRole))
                parent = parent.parent()

            rel_path.reverse()

            old_state[os.path.join(*rel_path)] = (itm.checkState(0) == Qt.Checked)

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

            # Apply any additional exclusions if we are at the top level.
            if self._additional_exclusions is not None and len(dir_stack) == 1:
                for exc in self._additional_exclusions:
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

        if self._show_root:
            parent = QTreeWidgetItem([self._package.name])
            self._package_edit.addTopLevelItem(parent)
            parent.setExpanded(True)
        else:
            parent = self._package_edit

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
