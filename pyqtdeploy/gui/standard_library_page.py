# Copyright (c) 2018, Riverbank Computing Limited
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


from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QCheckBox, QGroupBox, QSplitter, QTabWidget,
        QTreeView, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,
        QVBoxLayout, QWidget)

from ..metadata import (external_libraries_metadata, get_python_metadata,
        get_targeted_value)
from ..platforms import Architecture, Platform
from ..project import ExternalLibrary


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

        # Create the page's GUI.
        plat_pane = QWidget()
        plat_layout = QVBoxLayout()

        stdlib_pane = QWidget()
        stdlib_layout = QVBoxLayout()

        self._stdlib_edit = QTreeWidget(
                whatsThis="This shows the packages and modules in the target "
                        "Python version's standard library. Check those "
                        "packages and modules that are explicitly imported by "
                        "the application. A module will be partially checked "
                        "(and automatically included) if another module "
                        "requires it.")
        self._stdlib_edit.setHeaderLabels(["Package"])
        self._stdlib_edit.itemChanged.connect(self._module_changed)

        stdlib_layout.addWidget(self._stdlib_edit)

        stdlib_pane.setLayout(stdlib_layout)
        self.addWidget(stdlib_pane)

        self._plat_guis = QTabWidget()
        host = Architecture.architecture().platform
        host_gui = None

        for platform in Platform.all_platforms:
            plat_gui = _PlatformGui(platform.name)
            self._plat_guis.addTab(plat_gui, platform.full_name)

            if host.name == platform.name:
                host_gui = plat_gui

        self._plat_guis.setCurrentWidget(host_gui)

        plat_layout.addWidget(self._plat_guis)
        plat_pane.setLayout(plat_layout)

        self.addWidget(plat_pane)

    @pyqtSlot()
    def python_target_version_changed(self):
        """ Configure the page after the Python target version has changed. """

        self._update_page()

    def _update_page(self):
        """ Update the page using the current project. """

        for i in range(self._plat_guis.count()):
            self._plat_guis.widget(i).update_from_project(self.project)

        self._update_stdlib_editor()

    def _update_stdlib_editor(self):
        """ Update the standard library module editor. """

        project = self.project
        editor = self._stdlib_edit

        metadata = get_python_metadata(project.python_target_version)

        blocked = editor.blockSignals(True)

        editor.clear()

        def add_module(name, module, parent):
            itm = QTreeWidgetItem(parent, name.split('.')[-1:])
            itm.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)
            itm._name = name

            # Handle any sub-modules.
            if module.modules is not None:
                for submodule_name in module.modules:
                    # We assume that a missing sub-module is because it is not
                    # in the current version rather than bad meta-data.
                    submodule = metadata.get(submodule_name)
                    if submodule is not None:
                        add_module(submodule_name, submodule, itm)

        for name, module in metadata.items():
            if not module.internal and '.' not in name:
                add_module(name, module, editor)

        editor.sortItems(0, Qt.AscendingOrder)

        editor.blockSignals(blocked)

        self._set_dependencies()

    def _set_dependencies(self):
        """ Set the dependency information. """

        project = self.project
        editor = self._stdlib_edit

        required_modules, required_libraries = project.get_stdlib_requirements()

        blocked = editor.blockSignals(True)

        it = QTreeWidgetItemIterator(editor)
        itm = it.value()
        while itm is not None:
            explicit = required_modules.get(itm._name)
            expanded = False
            if explicit is None:
                state = Qt.Unchecked
            elif explicit:
                state = Qt.Checked
                expanded = True
            else:
                state = Qt.PartiallyChecked

            itm.setCheckState(0, state)

            # Make sure every explicitly checked item is visible.
            if expanded:
                parent = itm.parent()
                while parent is not None:
                    parent.setExpanded(True)
                    parent = parent.parent()

            it += 1
            itm = it.value()

        editor.blockSignals(blocked)

        for i in range(self._plat_guis.count()):
            self._plat_guis.widget(i).update_from_required_libraries(
                    required_libraries)

    def _module_changed(self, itm, col):
        """ Invoked when a standard library module has changed. """

        project = self._project

        # Get all the names to add or remove.
        names = []

        def add_name(subitm):
            names.append(subitm._name)

            for i in range(subitm.childCount()):
                add_name(subitm.child(i))

        add_name(itm)

        if itm.checkState(col) == Qt.Checked:
            # Add the names if they aren't already present.
            for name in names:
                if name not in project.standard_library:
                    project.standard_library.append(name)
        else:
            # Remove the names if they are present.
            for name in names:
                try:
                    project.standard_library.remove(name)
                except ValueError:
                    pass

            itm.setExpanded(False)

        self._set_dependencies()

        project.modified = True


class _PlatformGui(QWidget):
    """ The platform-specific GUI. """

    def __init__(self, platform_name):
        """ Initialise the object. """

        super().__init__()

        self._project = None
        self._target = Architecture.architecture(platform_name)

        self._ignore_extlib_changes = False

        layout = QVBoxLayout()

        self._pyshlib_cb = QCheckBox("Use standard Python shared library",
                whatsThis="Use the standard Python shared library rather than "
                        "a statically compiled library.",
                stateChanged=self._pyshlib_changed)
        layout.addWidget(self._pyshlib_cb)

        self._extlib_edit = QTreeView(
                whatsThis="This is the list of external libraries that must "
                        "be linked with the application for this platform. A "
                        "library will only be enabled if a module in the "
                        "standard library uses it. Double-click in the "
                        "<b>DEFINES</b>, <b>INCLUDEPATH</b> and <b>LIBS</b> "
                        "columns to modify the corresponding <tt>qmake</tt> "
                        "variable as required.")
        self._extlib_edit.setRootIsDecorated(False)
        self._extlib_edit.setEditTriggers(
                QTreeView.DoubleClicked|QTreeView.SelectedClicked|
                QTreeView.EditKeyPressed)

        model = QStandardItemModel(self._extlib_edit)
        model.setHorizontalHeaderLabels(
                ("External Library", 'DEFINES', 'INCLUDEPATH', 'LIBS'))
        model.itemChanged.connect(self._extlib_changed)

        model._items = {}

        for extlib in external_libraries_metadata:
            if extlib.get_libs(self._target.platform.name) == '':
                continue

            name_itm = QStandardItem(extlib.user_name)

            items = (name_itm, QStandardItem(), QStandardItem(),
                    QStandardItem())

            model.appendRow(items)

            model._items[extlib.name] = items

        self._extlib_edit.setModel(model)

        for col in range(3):
            self._extlib_edit.resizeColumnToContents(col)

        layout.addWidget(self._extlib_edit)

        self.setLayout(layout)

    def update_from_project(self, project):
        """ Update the GUI to reflect the current state of the project. """

        self._project = project

        platform_name = self._target.platform.name

        # Update the shared library state.
        blocked = self._pyshlib_cb.blockSignals(True)
        self._pyshlib_cb.setCheckState(
                Qt.Checked if platform_name in project.python_use_platform
                        else Qt.Unchecked)
        self._pyshlib_cb.blockSignals(blocked)

        # Update the external libraries.
        model = self._extlib_edit.model()

        blocked = model.blockSignals(True)

        external_libs = project.external_libraries.get(platform_name, [])

        for extlib in external_libraries_metadata:
            if extlib.get_libs(self._target.platform.name) == '':
                continue

            _, defs, incp, libs = model._items[extlib.name]

            for prj_extlib in external_libs:
                if prj_extlib.name == extlib.name:
                    defs.setText(prj_extlib.defines)
                    incp.setText(prj_extlib.includepath)
                    libs.setText(prj_extlib.libs)
                    break
            else:
                defs.setText(extlib.defines)
                incp.setText(extlib.includepath)
                libs.setText(extlib.get_libs(platform_name))

        model.blockSignals(blocked)

    def update_from_required_libraries(self, required_libraries):
        """ Update the GUI as the required external libraries changes. """

        # Only look at required libraries that are targeted for this platform.
        targeted_libraries = []
        for required_lib in required_libraries:
            targeted_lib = get_targeted_value(required_lib, self._target)
            if targeted_lib is not None:
                targeted_libraries.append(targeted_lib)

        items = self._extlib_edit.model()._items

        # Note that we can't simply block the model's signals as this would
        # interfere with the model/view interactions.
        self._ignore_extlib_changes = True

        for extlib in external_libraries_metadata:
            if extlib.get_libs(self._target.platform.name) == '':
                continue

            if extlib.name in targeted_libraries:
                for idx, itm in enumerate(items[extlib.name]):
                    itm.setFlags(
                            Qt.ItemIsEnabled|Qt.ItemIsEditable if idx != 0
                                    else Qt.ItemIsEnabled)
            else:
                for itm in items[extlib.name]:
                    itm.setFlags(Qt.NoItemFlags)

        self._ignore_extlib_changes = False

    def _pyshlib_changed(self, state):
        """ Invoked when the shared library state changes. """

        project = self._project
        platform_name = self._target.platform.name

        if state == Qt.Checked:
            project.python_use_platform.append(platform_name)
        else:
            project.python_use_platform.remove(platform_name)

        project.modified = True

    def _extlib_changed(self, itm):
        """ Invoked when an external library has changed. """

        if self._ignore_extlib_changes:
            return

        self._ignore_extlib_changes = True

        project = self._project
        platform_name = self._target.platform.name

        idx = self._extlib_edit.model().indexFromItem(itm)
        extlib = external_libraries_metadata[idx.row()]
        col = idx.column()

        # Get the project entry, creating it if necessary.
        external_libs = project.external_libraries.get(platform_name, [])

        for prj_extlib in external_libs:
            if prj_extlib.name == extlib.name:
                break
        else:
            prj_extlib = ExternalLibrary(extlib.name, '', '',
                    extlib.get_libs(platform_name))
            external_libs.append(prj_extlib)
            project.external_libraries[platform_name] = external_libs

        # Update the project.
        text = itm.text().strip()

        if col == 1:
            prj_extlib.defines = text
        elif col == 2:
            prj_extlib.includepath = text
        elif col == 3:
            prj_extlib.libs = text

        # If the project entry corresponds to the default then remove it.
        if prj_extlib.defines == extlib.defines and prj_extlib.includepath == extlib.includepath and prj_extlib.libs == extlib.get_libs(platform_name):
            external_libs.remove(prj_extlib)
            if len(external_libs) == 0:
                del project.external_libraries[platform_name]

        project.modified = True

        self._ignore_extlib_changes = False
