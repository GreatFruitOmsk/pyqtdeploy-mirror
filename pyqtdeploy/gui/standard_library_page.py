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
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QFormLayout, QSplitter,
        QTreeView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ..metadata import (ExtensionModule, external_libraries_metadata,
        get_python_metadata)
from ..project import QrcFile, ExternalLibrary


SUPPORTED_PYTHON_VERSIONS = ((2, 6), (2, 7), (3, 3), (3, 4))


class StandardLibraryPage(QSplitter):
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

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None
        self._modules = None

        # Create the page's GUI.
        stdlib_pane = QWidget()
        stdlib_layout = QVBoxLayout()

        self._stdlib_edit = QTreeWidget()
        self._stdlib_edit.setHeaderLabels(["Module"])
        self._stdlib_edit.itemChanged.connect(self._module_changed)

        stdlib_layout.addWidget(self._stdlib_edit)

        stdlib_pane.setLayout(stdlib_layout)
        self.addWidget(stdlib_pane)

        extlib_pane = QWidget()
        extlib_layout = QVBoxLayout()
        extlib_sublayout = QFormLayout()

        self._version_edit = QComboBox()
        self._version_edit.addItems(
                ['{0}.{1}'.format(major, minor)
                        for major, minor in SUPPORTED_PYTHON_VERSIONS])
        self._version_edit.currentIndexChanged.connect(self._version_changed)
        extlib_sublayout.addRow("Target Python version", self._version_edit)

        self._ssl_edit = QCheckBox(stateChanged=self._ssl_changed)
        extlib_sublayout.addRow("Use SSL support", self._ssl_edit)

        extlib_layout.addLayout(extlib_sublayout)

        self._extlib_edit = QTreeView()
        self._extlib_edit.setEditTriggers(
                QTreeView.DoubleClicked|QTreeView.SelectedClicked|
                QTreeView.EditKeyPressed)

        model = QStandardItemModel(self._extlib_edit)
        model.setHorizontalHeaderLabels(
                ("External Library", 'DEFINES', 'INCLUDEPATH', 'LIBS'))
        #model.itemChanged.connect(self._extlib_model_changed)

        for extlib in external_libraries_metadata:
            col0 = QStandardItem(extlib.user_name)
            col0.setFlags(Qt.NoItemFlags)

            col1 = QStandardItem()
            col2 = QStandardItem()
            col3 = QStandardItem()

            model.appendRow((col0, col1, col2, col3))

        self._extlib_edit.setModel(model)

        for col in range(3):
            self._extlib_edit.resizeColumnToContents(col)

        extlib_layout.addWidget(self._extlib_edit)

        extlib_pane.setLayout(extlib_layout)
        self.addWidget(extlib_pane)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._modules = get_python_metadata(*project.python_target_version)

        blocked = self._version_edit.blockSignals(True)
        self._version_edit.setCurrentIndex(
                SUPPORTED_PYTHON_VERSIONS.index(project.python_target_version))
        self._version_edit.blockSignals(blocked)

        blocked = self._ssl_edit.blockSignals(True)
        self._ssl_edit.setCheckState(
                Qt.Checked if project.python_ssl else Qt.Unchecked)
        self._ssl_edit.blockSignals(blocked)

        self._update_stdlib_editor()
        self._update_extlib_editor()

    @staticmethod
    def _reset_dependency_state(module, itm=None):
        """ Reset a module's dependency state. """

        module._item = itm
        module._explicit = False
        module._implicit = False
        module._visit = -1

    def _update_stdlib_editor(self):
        """ Update the standard library module editor. """

        project = self.project
        editor = self._stdlib_edit

        blocked = editor.blockSignals(True)

        editor.clear()

        def add_module(name, module, parent):
            itm = QTreeWidgetItem(parent, name.split('.')[-1:])
            itm.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)

            itm._name = name
            self._reset_dependency_state(module, itm)

            # Handle any sub-modules.
            if module.modules is not None:
                for submodule in module.modules:
                    add_module(submodule, self._modules[submodule], itm)

        for name, module in self._modules.items():
            if module.internal:
                self._reset_dependency_state(module)
            elif '.' not in name:
                add_module(name, module, editor)

        editor.sortItems(0, Qt.AscendingOrder)

        # Apply the project data and the dependencies.
        def add_dependency(name, module, visit, is_dep=False):
            if module._visit == visit:
                return

            module._visit = visit

            this_is_dep = False

            if name in project.standard_library:
                module._explicit = True
                this_is_dep = True

            if module.core or is_dep:
                module._implicit = True
                this_is_dep = True

            for dep in module.deps:
                add_dependency(dep, self._modules[dep], visit, this_is_dep)

        visit = 0
        for name, module in self._modules.items():
            add_dependency(name, module, visit)
            visit += 1

        for name, module in self._modules.items():
            itm = module._item
            if itm is not None:
                if module._explicit:
                    state = Qt.Checked
                elif module._implicit:
                    state = Qt.PartiallyChecked
                else:
                    state = Qt.Unchecked

                itm.setCheckState(0, state)

        editor.blockSignals(blocked)

    def _update_extlib_editor(self):
        """ Update the external library editor. """

        project = self.project

        if 0:
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

    def _version_changed(self, idx):
        """ Invoked when the target Python version changes. """

        project = self.project

        project.python_target_version = SUPPORTED_PYTHON_VERSIONS[idx]
        self._update_page()

        project.modified = True

    def _ssl_changed(self, state):
        """ Invoked when the SSL support changes. """

        project = self.project

        project.python_ssl = (state == Qt.Checked)
        self._update_dependencies()

        project.modified = True

    def _module_changed(self, itm, col):
        """ Invoked when an item has changed. """

        print("Item changed:", itm, col)
        return

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
