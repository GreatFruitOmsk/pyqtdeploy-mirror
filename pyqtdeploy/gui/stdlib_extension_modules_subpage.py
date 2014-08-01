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
from ..project import StdlibExtensionModule


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

        self._extension_modules_edit = QTreeView()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
                ["Name", "DEFINES", "INCLUDEPATH", "LIBS"])
        model.itemChanged.connect(self._item_changed)

        self._extension_modules_edit.setEditTriggers(
                QTreeView.DoubleClicked|QTreeView.SelectedClicked|
                QTreeView.EditKeyPressed)

        self._extension_modules_edit.setModel(model)

        layout.addWidget(self._extension_modules_edit)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        # Set the extension modules.
        modules = get_python_metadata(*project.python_target_version).modules
        modules = sorted(modules,
                key=lambda m: m.name[1:].lower() if m.name.startswith('_') else m.name.lower())

        model = self._extension_modules_edit.model()
        model.removeRows(0, model.rowCount())

        for row, metadata in enumerate(modules):
            col0 = self._new_item(metadata.name)
            col0.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)

            # See if the module is enabled.
            for project_module in project.stdlib_extension_modules:
                if project_module.name == metadata.name:
                    defines = project_module.defines
                    includepath = project_module.includepath
                    libs = project_module.libs
                    break
            else:
                defines = metadata.defines
                includepath = ''
                libs = metadata.libs
                project_module = None

            col0.setCheckState(Qt.Checked if project_module is not None
                    else Qt.Unchecked)

            col1 = self._new_item(defines, project_module is not None)
            col2 = self._new_item(includepath, project_module is not None)
            col3 = self._new_item(libs, project_module is not None)

            model.appendRow([col0, col1, col2, col3])

            # Save for later.
            col0._module_metadata = metadata
            col0._module = project_module

        self._extension_modules_edit.resizeColumnToContents(0)

    def _new_item(self, text, editable=False):
        """ Create a new model item. """

        itm = QStandardItem(text)

        flags = Qt.ItemIsEnabled
        if editable:
            flags |= Qt.ItemIsEditable

        itm.setFlags(flags)

        return itm

    def _item_changed(self, itm):
        """ Invoked when an item has changed. """

        project = self.project
        model = self._extension_modules_edit.model()

        # Convert to a row and column.
        idx = model.indexFromItem(itm)
        row = idx.row()
        col = idx.column()

        if col == 0:
            blocked = model.blockSignals(True)

            if itm.checkState() == Qt.Checked:
                # Add the module.
                metadata = itm._module_metadata
                module = StdlibExtensionModule(metadata.name, metadata.defines,
                        '', metadata.libs)
                project.stdlib_extension_modules.append(module)
                itm._module = module

                new_flags = Qt.ItemIsEnabled|Qt.ItemIsEditable
            else:
                # Remove the module.
                project.stdlib_extension_modules.remove(itm._module)
                itm._module = None

                # Reset the other columns to the meta-data defaults.
                metadata = itm._module_metadata

                model.item(row, 1).setText(metadata.defines)
                model.item(row, 2).setText('')
                model.item(row, 3).setText(metadata.libs)

                new_flags = Qt.ItemIsEnabled

            # Update the editable state of the other columns in the row.
            for c in range(1, 4):
                model.item(row, c).setFlags(new_flags)

            model.blockSignals(blocked)
        else:
            # The module must be in the project.
            text = itm.text().strip()
            module = model.item(row, 0)._module

            if col == 1:
                module.defines = text
            elif col == 2:
                module.includepath = text
            elif col == 3:
                module.libs = text

        project.modified = True
