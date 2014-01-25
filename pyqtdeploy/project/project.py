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


import os
from xml.etree.ElementTree import Element, ElementTree

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal

from .project_exception import ProjectException


class Project(QObject):
    """ The encapsulation of a project. """

    # The current project version.
    version = 0

    # Emitted when the modification state of the project changes.
    modified_changed = pyqtSignal(bool)

    @pyqtProperty(bool)
    def modified(self):
        """ The modified property getter. """

        return self._modified

    @modified.setter
    def modified(self, value):
        """ The modified property setter. """

        if self._modified != value:
            self._modified = value
            self.modified_changed.emit(value)

    # Emitted when the name of the project changes.
    name_changed = pyqtSignal(str)

    @pyqtProperty(str)
    def name(self):
        """ The name property getter. """

        return self._name

    @name.setter
    def name(self, value):
        """ The name property setter. """

        if self._name != value:
            self._name = value
            self.name_changed.emit(value)

    def __init__(self):
        """ Initialise the project. """

        super().__init__()

        # Initialise the properties.
        self._modified = False
        self._abs_filename = ''
        self._name = ''

    @classmethod
    def load(cls, filename):
        """ Return a new project loaded from the given file.  Raise a
        ProjectException if there was an error.
        """

        project = cls()

        # TODO

        return project

    def save(self):
        """ Save the project.  Raise a ProjectException if there was an error.
        """

        self._save_project(self._abs_filename)

    def save_as(self, filename):
        """ Save the project to the given file and make the file the
        destination of subsequent saves.  Raise a ProjectException if there was
        an error.
        """

        abs_filename = os.path.abspath(filename)

        self._save_project(abs_filename)

        # Now that the save has been successful, update the project.
        self._abs_filename = abs_filename
        self.name = os.path.basename(abs_filename)

    def _save_project(self, abs_filename):
        """ Save the project to the given file.  Raise a ProjectException if
        there was an error.
        """

        root = Element('application')
        root.set('version', str(self.version))

        tree = ElementTree(root)

        try:
            tree.write(abs_filename, encoding='unicode', xml_declaration=True)
        except Exception as e:
            raise ProjectException(
                    "There was an error writing the project file.", str(e))

        self.modified = False
