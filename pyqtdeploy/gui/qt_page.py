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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QVBoxLayout, QWidget


class QtPage(QWidget):
    """ The GUI for the Qt configuration page of a project. """

    # The page's label.
    label = "Qt Configuration"

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

        self._shared_edit = QCheckBox("Qt libraries are shared",
                whatsThis="Set this if your Qt installation uses shared, "
                        "rather than static, libraries.",
                stateChanged=self._shared_changed)
        layout.addWidget(self._shared_edit)

        self.setLayout(layout)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self.project

        self._shared_edit.setCheckState(Qt.Checked if project.qt_is_shared else Qt.Unchecked)

    def _shared_changed(self, value):
        """ Invoked when the user edits the shared state. """

        self.project.qt_is_shared = (value == Qt.Checked)
        self.project.modified = True
