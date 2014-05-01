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


from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QButtonGroup, QFileDialog, QGridLayout,
        QHBoxLayout, QRadioButton, QWidget)

from .better_form import BetterForm
from .filename_editor import FilenameEditor
from .qrc_package_editor import QrcPackageEditor


class ApplicationPage(QWidget):
    """ The GUI for the application page of a project. """

    # The page's label.
    label = "Application Source"

    # Emitted when the user changes the PyQt version.
    pyqt_version_changed = pyqtSignal(bool)

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value
            self._script_edit.set_project(value)
            self._package_edit.set_project(value)
            self._update_page()

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None

        # Create the page's GUI.
        layout = QGridLayout()

        form = BetterForm()

        self._script_edit = FilenameEditor("Application Script",
                placeholderText="Application script",
                whatsThis="The name of the application's main script file.",
                textEdited=self._script_changed)
        form.addRow("Main script file", self._script_edit)

        layout.addLayout(form, 0, 0)

        versions_layout = QHBoxLayout()
        self._pyqt_versions_bg = QButtonGroup()

        for version in ('PyQt5', 'PyQt4'):
            rb = QRadioButton(version)
            versions_layout.addWidget(rb)
            self._pyqt_versions_bg.addButton(rb)

        self._pyqt_versions_bg.buttonToggled.connect(
                self._pyqt_version_changed)

        layout.addLayout(versions_layout, 0, 1)

        self._package_edit = _ApplicationPackageEditor()
        self._package_edit.package_changed.connect(self._package_changed)
        layout.addWidget(self._package_edit, 1, 0, 1, 2)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._script_edit.setText(project.application_script)
        self._package_edit.configure(project.application_package, project)

        self._pyqt_versions_bg.blockSignals(True)

        for rb in self._pyqt_versions_bg.buttons():
            if rb.text() == 'PyQt5':
                rb.setChecked(project.application_is_pyqt5)
            else:
                rb.setChecked(not project.application_is_pyqt5)

        self._pyqt_versions_bg.blockSignals(False)

    def _pyqt_version_changed(self, button, checked):
        """ Invoked when the user changes the PyQt version number. """

        if button.text() == 'PyQt5':
            self.project.application_is_pyqt5 = checked
            self.project.modified = True

            self.pyqt_version_changed.emit(checked)

    def _script_changed(self, value):
        """ Invoked when the user edits the application script name. """

        self.project.application_script = value
        self.project.modified = True

    def _package_changed(self):
        """ Invoked when the user edits the application package. """

        self.project.modified = True


class _ApplicationPackageEditor(QrcPackageEditor):
    """ A memory filesystem package editor for the application package. """

    # The editor title.
    _title = "Application Package"

    def __init__(self):
        """ Initialise the editor. """

        super().__init__(self._title, show_root=True, scan="Scan...")

        self._project = None

    def get_root_dir(self):
        """ Get the name of the application directory. """

        project = self._project
        application_package = project.application_package

        orig = default = application_package.name
        if default != '':
            default = project.absolute_path(default)

        root = QFileDialog.getExistingDirectory(self, self._title, default)

        if root != '':
            application_package.name = project.relative_path(root)

        return root

    def set_project(self, project):
        """ Set the project. """

        self._project = project
