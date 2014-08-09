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
from PyQt5.QtWidgets import (QLabel, QStackedWidget, QTreeView, QVBoxLayout,
        QWidget)

from ..metadata import ExtensionModule, get_python_metadata
from ..project import QrcFile, StdlibModule


class StandardLibraryPage(QStackedWidget):
    """ The GUI for the standard library page of a project. """

    # The page's label.
    label = "Standard Library"

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

            if self._tab_widget is None:
                self._tab_widget = self.parent().parent()
                self._tab_widget.currentChanged.connect(self._tab_changed)

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None
        self._tab_widget = None

        # Create the page's GUI.
        layout = QVBoxLayout()

        self._stdlib_edit = QTreeView()

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(
                ["Name", "DEFINES", "INCLUDEPATH", "LIBS"])
        model.itemChanged.connect(self._item_changed)

        self._stdlib_edit.setEditTriggers(
                QTreeView.DoubleClicked|QTreeView.SelectedClicked|
                QTreeView.EditKeyPressed)

        self._stdlib_edit.setModel(model)

        layout.addWidget(self._stdlib_edit)
        self._stdlib_subpage = QWidget()
        self._stdlib_subpage.setLayout(layout)
        self.addWidget(self._stdlib_subpage)

        self._warning = QLabel()
        self._warning.setAlignment(Qt.AlignCenter)
        self.addWidget(self._warning)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        major, minor = project.python_target_version

        if major is None:
            warning_text = "The Python version cannot be obtained from the " \
                    "<b>Python library</b> field of the <b>Locations</b> tab."
        elif major == 3 and minor < 3:
            warning_text = "You seem to be using Python v{0}.{1}. When " \
                    "targetting Python v3, Python v3.3 or later is " \
                    "required.".format(major, minor)
        elif major == 2 and minor < 6:
            warning_text = "You seem to be using Python v{0}.{1}. When " \
                    "targetting Python v2, Python v2.6 or later is " \
                    "required.".format(major, minor)
        else:
            warning_text = ''

        if warning_text == '':
            self.setCurrentWidget(self._stdlib_subpage)

            # Configure the editor if it is empty.
            if self._stdlib_edit.model().rowCount() == 0:
                self._configure_stdlib_editor()
        else:
            self._warning.setText(warning_text)
            self.setCurrentWidget(self._warning)

    def _tab_changed(self, idx):
        """ Invoked when the current tab of the containing widget changes. """

        if self._tab_widget.widget(idx) is self:
            self._update_page()

    def _configure_stdlib_editor(self):
        """ Configure the standard library editor for the current project. """

        project = self.project

        # Set the extension modules.
        modules = get_python_metadata(*project.python_target_version).modules
        modules = sorted(modules,
                key=lambda m: m.name[1:].lower() if m.name.startswith('_') else m.name.lower())

        model = self._stdlib_edit.model()
        model.removeRows(0, model.rowCount())

        for row, metadata in enumerate(modules):
            # Core modules are permanently disabled.
            flags = Qt.NoItemFlags if metadata.core else Qt.ItemIsEnabled

            col0 = self._new_item(metadata.name, flags|Qt.ItemIsUserCheckable)

            # See if the module is enabled.
            for project_module in project.standard_library:
                if project_module.name == metadata.name:
                    defines = project_module.defines
                    includepath = project_module.includepath
                    libs = project_module.libs
                    check_state = Qt.Checked

                    # The module can't be core if we are here.
                    flags |= Qt.ItemIsEditable

                    break
            else:
                project_module = None
                defines = metadata.defines
                includepath = ''
                libs = metadata.libs
                check_state = Qt.Checked if metadata.core else Qt.Unchecked

            col0.setCheckState(check_state)

            col1 = self._new_item(defines, flags)
            col2 = self._new_item(includepath, flags)
            col3 = self._new_item(libs, flags)

            model.appendRow([col0, col1, col2, col3])

            # Save for later.
            col0._module_metadata = metadata
            col0._module = project_module

        self._stdlib_edit.resizeColumnToContents(0)

    def _new_item(self, text, flags):
        """ Create a new model item. """

        itm = QStandardItem(text)
        itm.setFlags(flags)

        return itm

    def _item_changed(self, itm):
        """ Invoked when an item has changed. """

        project = self.project
        model = self._stdlib_edit.model()

        # Convert to a row and column.
        idx = model.indexFromItem(itm)
        row = idx.row()
        col = idx.column()

        if col == 0:
            blocked = model.blockSignals(True)

            metadata = itm._module_metadata
            new_flags = Qt.ItemIsEnabled

            if itm.checkState() == Qt.Checked:
                # Add the module.
                module = StdlibModule(metadata.name, metadata.defines, '',
                        metadata.libs)
                project.standard_library.append(module)
                new_flags |= Qt.ItemIsEditable
                itm._module = module
            else:
                # Remove the module.
                project.standard_library.remove(itm._module)
                defines = metadata.defines
                libs = metadata.libs

                itm._module = None

                # Reset the other columns to the meta-data defaults.
                model.item(row, 1).setText(defines)
                model.item(row, 2).setText('')
                model.item(row, 3).setText(libs)

            # Update the editable state of the other columns in the row.
            for c in range(1, 4):
                model.item(row, c).setFlags(new_flags)

            model.blockSignals(blocked)
        else:
            # The module must be an extension module in the project.
            text = itm.text().strip()
            module = model.item(row, 0)._module

            if col == 1:
                module.defines = text
            elif col == 2:
                module.includepath = text
            elif col == 3:
                module.libs = text

        project.modified = True
