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


from PyQt5.QtWidgets import QMessageBox, QWidget

from ..metadata import get_python_metadata

from .qrc_package_editor import QrcPackageEditor


class StdlibPackagesSubpage(QWidget):
    """ The GUI for the standard library packages sub-page of a project. """

    # The page's label.
    label = "Packages"

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value
            self._package_edit.set_project(value)
            self._update_page()

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None

        # Create the page's GUI.
        self._package_edit = _StdlibPackageEditor()
        self._package_edit.package_changed.connect(self._package_changed)

        self.setLayout(self._package_edit)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._package_edit.configure(project.stdlib_package, project)

    def _package_changed(self):
        """ Invoked when the user edits the standard library package. """

        self.project.modified = True


class _StdlibPackageEditor(QrcPackageEditor):
    """ A memory filesystem package editor for the Python standard library
    package.
    """

    # The editor title.
    title = "Standard Library Packages"

    def __init__(self):
        """ Initialise the editor. """

        super().__init__()

        self._project = None
        self._py_metadata = None

    def get_root_dir(self):
        """ Get the name of the Python standard library directory. """

        project = self._project

        major, minor = project.python_target_version

        if major is None:
            QMessageBox.warning(self.parentWidget(), self.title,
                    "The standard library cannot be scanned because the "
                    "Python version cannot be obtained from the Python "
                    "library name in the Locations tab.")
            return ''

        if major == 3 and minor < 3:
            QMessageBox.warning(self.parentWidget(), self.title,
                    "When targetting Python v3, Python v3.3 or later is "
                    "required.")
            return ''

        if major == 2 and minor < 6:
            QMessageBox.warning(self.parentWidget(), self.title,
                    "When targetting Python v2, Python v2.6 or later is "
                    "required.")
            return ''

        stdlib_dir = project.absolute_path(project.python_target_stdlib_dir)

        if stdlib_dir == '':
            QMessageBox.warning(self.parentWidget(), self.title,
                    "The standard library cannot be scanned because its "
                    "directory name has not been set in the Locations tab.")
            return ''

        return stdlib_dir

    def filter(self, name):
        """ Reimplemented to filter out site-packages. """

        if name == 'site-packages':
            return True

        return super().filter(name)

    def required(self, name):
        """ See if a name is required. """

        if self._py_metadata is None:
            self._py_metadata = get_python_metadata(
                    *self._project.python_target_version)

        if name in self._py_metadata.required:
            return True

        return super().filter(name)

    def set_project(self, project):
        """ Set the project. """

        self._project = project

        self._py_metadata = None
