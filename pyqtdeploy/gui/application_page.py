# Copyright (c) 2014 Riverbank Computing Limited.
#
# This file is part of pyqtdeploy.
#
# This file may be used under the terms of the GNU General Public License
# v2 or v3 as published by the Free Software Foundation which can be found in
# the files LICENSE-GPL2.txt and LICENSE-GPL3.txt included in this package.
# In addition, as a special exception, Riverbank gives you certain additional
# rights.  These rights are described in the Riverbank GPL Exception, which
# can be found in the file GPL-Exception.txt in this package.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


from PyQt5.QtWidgets import QFormLayout, QLineEdit, QWidget


class ApplicationPage(QWidget):
    """ The GUI for the application page of a project. """

    # The page's label.
    label = "Application Source"

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
        form = QFormLayout()

        self._script_edit = QLineEdit(placeholderText="Application script",
                whatsThis="The name of the application's main script file.",
                textEdited=self._script_changed)
        form.addRow("Main script file", self._script_edit)

        self.setLayout(form)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._script_edit.setText(project.application_script)

    def _script_changed(self, value):
        """ Invoked when the user edits the application script name. """

        self.project.application_script = value
        self.project.modified = True
