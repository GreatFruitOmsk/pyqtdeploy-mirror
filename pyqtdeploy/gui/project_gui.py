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


from PyQt5.QtCore import QPoint, QSettings, QSize
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow


class ProjectGUI(QMainWindow):
    """ The GUI for a project. """

    def __init__(self):
        """ Initialise the project GUI. """

        super().__init__()

        self._project = None

        self._create_menus()
        self._load_settings()

    def closeEvent(self, event):
        """ Handle a close event. """

        if self._current_project_done():
            self._save_settings()
            event.accept()
        else:
            event.ignore()

    def _create_menus(self):
        """ Create the menus. """

        # TODO - set the inttial state of the actions.
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New", self._new_project, QKeySequence.New)
        file_menu.addAction("&Open...", self._open_project, QKeySequence.Open)
        file_menu.addAction("&Save", self._save_project, QKeySequence.Save)
        file_menu.addAction("Save &As...", self._save_as_project,
                QKeySequence.SaveAs)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, QKeySequence.Quit)

    def _new_project(self):
        print("Handle new project")

    def _open_project(self):
        print("Handle open project")

    def _save_project(self):
        print("Handle save project")

    def _save_as_project(self):
        print("Handle save as project")

    def _current_project_done(self):
        """ Return True if the user has finished with any current project. """

        # TODO
        return True

    def _load_settings(self):
        """ Load the user specific settings. """

        settings = QSettings()

        self.resize(settings.value('size', QSize(400, 400)))
        self.move(settings.value('pos', QPoint(200, 200)))

    def _save_settings(self):
        """ Save the user specific settings. """

        settings = QSettings()

        settings.setValue('size', self.size())
        settings.setValue('pos', self.pos())
