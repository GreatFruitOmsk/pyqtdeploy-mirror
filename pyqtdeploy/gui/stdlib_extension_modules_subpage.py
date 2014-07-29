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


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QTreeView, QVBoxLayout, QWidget

from ..metadata import get_python_metadata


class StdlibExtensionModulesSubpage(QWidget):
    """ The GUI for the standard library extension modules sub-page of a
    project.
    """

    # The page's label.
    label = "Extension Modules"

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value
            self._update_page()

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None

        # Create the page's GUI.
        layout = QVBoxLayout()

        em_edit = QTreeView()
        self._extension_modules_edit = em_edit

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
                ["Name", "DEFINES", "INCLUDEPATH", "LIBS"])
        model.itemChanged.connect(self._item_changed)

        em_edit.setEditTriggers(
                QTreeView.DoubleClicked|QTreeView.SelectedClicked|
                QTreeView.EditKeyPressed)

        em_edit.setModel(model)

        layout.addWidget(em_edit)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project
        em_edit = self._extension_modules_edit

        # Set the extension modules.
        modules = get_python_metadata(*project.python_target_version).modules
        modules = sorted(modules,
                key=lambda m: m.name[1:] if m.name.startswith('_') else m.name)

        model = em_edit.model()
        model.removeRows(0, model.rowCount())

        for row, module in enumerate(modules):
            col0 = QStandardItem(module.name)
            col0.setCheckState(Qt.Unchecked)
            flags = col0.flags()
            flags &= ~Qt.ItemIsEditable
            flags |= Qt.ItemIsUserCheckable
            col0.setFlags(flags)

            col1 = QStandardItem(module.defines)
            col2 = QStandardItem(module.includepath)
            col3 = QStandardItem(module.libs)

            model.appendRow([col0, col1, col2, col3])

        em_edit.resizeColumnToContents(0)

    def _item_changed(self, itm):
        """ Invoked when an item has changed. """

        print(itm)
