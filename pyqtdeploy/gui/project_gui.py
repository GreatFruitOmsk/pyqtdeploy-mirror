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
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox

from ..project import Project
from ..user_exception import UserException


class ProjectGUI(QMainWindow):
    """ The GUI for a project. """

    # The filter string to use with file dialogs.
    file_dialog_filter = "Projects (*.pdy)"

    def __init__(self, project):
        """ Initialise the GUI for a project. """

        super().__init__()

        self._create_menus()
        self._load_settings()

        self._set_project(project)

    @classmethod
    def load(cls, filename):
        """ Create a project from the given file.  Return None if there was an
        error.
        """

        return cls._load_project(filename)

    def closeEvent(self, event):
        """ Handle a close event. """

        if self._current_project_done():
            self._save_settings()
            event.accept()
        else:
            event.ignore()

    def _set_project(self, project):
        """ Set the GUI's project. """

        self._project = project

        self._project.modified_changed.connect(self.setWindowModified)
        self._project.name_changed.connect(self._name_changed)

        self._name_changed(self._project.name)

    def _name_changed(self, name):
        """ Invoked when the project's name changes. """

        # Update the window title.
        title = name if name != '' else "Unnamed"
        self.setWindowTitle(title + '[*]')

        # Update the state of the actions.
        self._save_action.setEnabled(name != '')

    def _create_menus(self):
        """ Create the menus. """

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction("&New", self._new_project, QKeySequence.New)
        file_menu.addAction("&Open...", self._open_project, QKeySequence.Open)
        self._save_action = file_menu.addAction("&Save", self._save_project,
                QKeySequence.Save)
        file_menu.addAction("Save &As...", self._save_as_project,
                QKeySequence.SaveAs)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, QKeySequence.Quit)

    def _new_project(self):
        """ Create a new, unnamed project. """

        if self._current_project_done():
            self._set_project(Project())

    def _open_project(self):
        """ Open an existing project. """

        if self._current_project_done():
            filename, _ = QFileDialog.getOpenFileName(self, "Open",
                    filter=self.file_dialog_filter)

            if filename != '':
                project = self._load_project(filename, self)
                if project is not None:
                    self._set_project(project)

    def _save_project(self):
        """ Save the project and return True if it was saved. """

        try:
            self._project.save()
        except UserException as e:
            self._handle_exception(e, "Save", self)
            return False

        return True

    def _save_as_project(self):
        """ Save the project under a new name and return True if it was saved.
        """

        filename, _ = QFileDialog.getSaveFileName(self, "Save As",
                    filter=self.file_dialog_filter)

        if filename == '':
            return False

        try:
            self._project.save_as(filename)
        except UserException as e:
            self._handle_exception(e, "Save", self)
            return False

        return True

    @classmethod
    def _load_project(cls, filename, parent=None):
        """ Create a project from the given file.  Return None if there was an
        error.
        """

        try:
            project = Project.load(filename)
        except UserException as e:
            cls._handle_exception(e, "Open", parent)
            project = None

        return project

    @staticmethod
    def _handle_exception(e, title, parent):
        """ Handle a UserException. """

        msg_box = QMessageBox(QMessageBox.Warning, title, e.text,
                parent=parent)

        if e.detail != '':
            msg_box.setDetailedText(e.detail)

        msg_box.exec()

    def _current_project_done(self):
        """ Return True if the user has finished with any current project. """

        if self._project.modified:
            msg_box = QMessageBox(QMessageBox.Question, "Save",
                    "The project has been modified.",
                    QMessageBox.Save|QMessageBox.Discard|QMessageBox.Cancel,
                    parent=self)

            msg_box.setDefaultButton(QMessageBox.Save)
            msg_box.setInformativeText("Do you want to save your changes?")

            ans = msg_box.exec()

            if ans == QMessageBox.Cancel:
                return False

            if ans == QMessageBox.Save:
                return self._save_project() if self._project.name != "" else self._save_as_project()

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
