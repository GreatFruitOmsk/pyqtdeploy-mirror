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
from xml.etree.ElementTree import Element, ElementTree, SubElement

from PyQt5.QtCore import QObject, pyqtSignal

from ..user_exception import UserException


class Project(QObject):
    """ The encapsulation of a project. """

    # The current project version.
    version = 0

    # Emitted when the application name of the project changes.
    application_name_changed = pyqtSignal(str)

    @property
    def application_name(self):
        """ The application name property getter. """

        return self._application_name

    @application_name.setter
    def application_name(self, value):
        """ The application name property setter. """

        if self._application_name != value:
            self._application_name = value
            self.application_name_changed.emit(value)

    # Emitted when the modification state of the project changes.
    modified_changed = pyqtSignal(bool)

    @property
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

    @property
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

        self._application_name = ''

    @classmethod
    def load(cls, filename):
        """ Return a new project loaded from the given file.  Raise a
        UserException if there was an error.
        """

        abs_filename = os.path.abspath(filename)

        tree = ElementTree()

        try:
            root = tree.parse(abs_filename)
        except Exception as e:
            raise UserException(
                "There was an error reading the project file.", str(e))

        cls._assert(root.tag == 'project',
                "Unexpected root tag '{0}', 'project' expected.".format(
                        root.tag))

        # Check the project version number.
        version = root.get('version')
        cls._assert(version is not None, "Missing 'version'.")

        try:
            version = int(version)
        except:
            version = None

        cls._assert(version is not None, "Invalid 'version'.")

        if version != cls.version:
            raise UserException(
                    "The project's format is version {0} but only version {1} is supported.".format(version, cls.version))

        # Create the project and populate it.
        project = cls()
        project._set_project_name(abs_filename)

        application = root.find('application')
        cls._assert(application is not None, "Missing 'application' tag.")

        application_name = application.get('name')
        cls._assert(application_name is not None, "Missing 'name'.")

        project._application_name = application_name

        return project

    def save(self):
        """ Save the project.  Raise a UserException if there was an error. """

        self._save_project(self._abs_filename)

    def save_as(self, filename):
        """ Save the project to the given file and make the file the
        destination of subsequent saves.  Raise a UserException if there was an
        error.
        """

        abs_filename = os.path.abspath(filename)

        self._save_project(abs_filename)

        # Only do this after the project has been successfully saved.
        self._set_project_name(abs_filename)

    def _set_project_name(self, abs_filename):
        """ Set the name of the project. """

        self._abs_filename = abs_filename
        self.name = os.path.basename(abs_filename)

    def _save_project(self, abs_filename):
        """ Save the project to the given file.  Raise a UserException if there
        was an error.
        """

        root = Element('project', attrib={
            'version': str(self.version)})

        application = SubElement(root, 'application', attrib={
            'name': self.application_name})

        tree = ElementTree(root)

        try:
            tree.write(abs_filename, encoding='unicode', xml_declaration=True)
        except Exception as e:
            raise UserException(
                    "There was an error writing the project file.", str(e))

        self.modified = False

    @staticmethod
    def _assert(ok, detail):
        """ Validate an assertion and raise a UserException if it failed. """

        if not ok:
            raise UserException("The project file is invalid.", detail)
