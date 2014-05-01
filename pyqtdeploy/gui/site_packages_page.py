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


import os

from PyQt5.QtWidgets import QMessageBox, QVBoxLayout, QWidget

from .qrc_package_editor import QrcPackageEditor


class SitePackagesPage(QWidget):
    """ The GUI for the site packages page of a project. """

    # The page's label.
    label = "Site Packages"

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

        self._package_edit = _SitePackagesPackageEditor()
        self._package_edit.package_changed.connect(self._package_changed)
        layout.addWidget(self._package_edit)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._package_edit.configure(project.site_packages_package, project)

    def _package_changed(self):
        """ Invoked when the user edits the standard library package. """

        self.project.modified = True


class _SitePackagesPackageEditor(QrcPackageEditor):
    """ A memory filesystem package editor for the Python site packages
    package.
    """

    # The editor title.
    _title = "Site Packages"

    def __init__(self):
        """ Initialise the editor. """

        super().__init__(self._title)

        self._project = None

    def get_root_dir(self):
        """ Get the name of the Python site packages directory. """

        project = self._project

        stdlib_dir = project.absolute_path(project.python_target_stdlib_dir)

        if stdlib_dir == '':
            QMessageBox.warning(self, self._title,
                    "site-packages cannot be scanned because the directory "
                    "name of the standard library has not been set in the "
                    "Locations tab.")
            return ''

        return os.path.join(stdlib_dir, 'site-packages')

    def filter(self, name):
        """ Reimplemented to filter out the PyQt related stuff. """

        if name in ('libsip.a', 'sip.so', 'sip.lib', 'sip.pyd', 'PyQt5', 'PyQt4'):
            return True

        return super().filter(name)

    def set_project(self, project):
        """ Set the project. """

        self._project = project
