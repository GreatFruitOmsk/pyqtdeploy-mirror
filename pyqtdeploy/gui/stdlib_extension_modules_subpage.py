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
from PyQt5.QtWidgets import (QTableWidget, QTableWidgetItem, QVBoxLayout,
        QWidget)

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

        em_edit = QTableWidget()
        self._extension_modules_edit = em_edit

        em_edit.setColumnCount(4)
        em_edit.setHorizontalHeaderLabels(
                ["Name", "DEFINES", "INCLUDEPATH", "LIBS"])
        h_header = em_edit.horizontalHeader()
        h_header.setDefaultAlignment(Qt.AlignLeft)
        h_header.setStretchLastSection(True)
        h_header.setHighlightSections(False)
        em_edit.verticalHeader().hide()

        em_edit.setEditTriggers(
                QTableWidget.DoubleClicked|QTableWidget.SelectedClicked|
                QTableWidget.EditKeyPressed)
        em_edit.cellChanged.connect(self._cell_changed)

        layout.addWidget(em_edit)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project
        em_edit = self._extension_modules_edit

        # Set the extension modules.
        em_edit.clearContents()

        modules = get_python_metadata(*project.python_target_version).modules
        modules = sorted(modules,
                key=lambda m: m.name[1:] if m.name.startswith('_') else m.name)

        blocked = em_edit.blockSignals(True)

        em_edit.setRowCount(len(modules))

        for row, module in enumerate(modules):
            self._add_cell(module.name, row, 0)
            self._add_cell(module.defines, row, 1)
            self._add_cell(module.includepath, row, 2)
            self._add_cell(module.libs, row, 3)

        em_edit.resizeColumnToContents(0)

        em_edit.blockSignals(blocked)

    def _add_cell(self, text, row, col):
        """ Add a cell to the table. """

        itm = QTableWidgetItem(text)

        if col == 0:
            itm.setCheckState(Qt.Unchecked)
            flags = Qt.ItemIsUserCheckable|Qt.ItemIsEnabled
        else:
            flags = Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled

        itm.setFlags(flags)

        self._extension_modules_edit.setItem(row, col, itm)

    def _cell_changed(self, row, col):
        """ Invoked when a cell has changed. """

        print(row, col)
