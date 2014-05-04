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
from xml.etree.ElementTree import Element, ElementTree, SubElement

from PyQt5.QtCore import QObject, pyqtSignal

from ..user_exception import UserException


class Project(QObject):
    """ The encapsulation of a project. """

    # The current project version.
    #   0: The original version.
    #   1: Added the Others element with the builddir and qmake attributes.
    version = 1

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

    @property
    def python_target_version(self):
        """ The target Python version getter. """

        if self.python_target_library != '':
            lib_name = os.path.basename(self.python_target_library)

            # Strip everything up to the leading digit.
            while lib_name != '' and not lib_name[0].isdigit():
                lib_name = lib_name[1:]

            # Strip everything after the trailing digit.
            while lib_name != '' and not lib_name[-1].isdigit():
                lib_name = lib_name[:-1]

            version_str = lib_name.replace('.', '')

            # We should now have a 2-digit string.
            try:
                version = int(version_str)

                return version // 10, version % 10
            except ValueError:
                pass

        return None, None

    def __init__(self, name=''):
        """ Initialise the project. """

        super().__init__()

        # Initialise the project meta-data.
        self._modified = False
        self._name = os.path.abspath(name) if name != '' else ''

        # Initialise the project data.
        self.application_is_pyqt5 = True
        self.application_package = QrcPackage()
        self.application_script = ''
        self.build_dir = 'build'
        self.extension_modules = []
        self.pyqt_modules = []
        self.python_host_interpreter = ''
        self.python_target_include_dir = ''
        self.python_target_library = ''
        self.python_target_stdlib_dir = ''
        self.qmake = ''
        self.site_packages_package = QrcPackage()
        self.stdlib_package = QrcPackage()

    def relative_path(self, filename):
        """ Convert a filename to one that is relative to the project
        name if possible.
        """

        filename = filename.strip()

        if os.path.isabs(filename):
            if self._name != '':
                project_dir = os.path.dirname(self._name)
                if filename.startswith(project_dir):
                    filename = os.path.relpath(filename, project_dir)

        return filename

    def absolute_path(self, filename):
        """ Convert a filename that might be relative to the project name to an
        absolute filename.
        """

        filename = os.path.expandvars(filename.strip())

        if not os.path.isabs(filename):
            filename = os.path.join(os.path.dirname(self._name), filename)

        return filename

    def application_basename(self):
        """ Return the basename of the application script (i.e. with no path or
        extension.
        """

        app_name, _ = os.path.splitext(
                os.path.basename(self.absolute_path(self.application_script)))

        return app_name

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

        cls._assert(root.tag == 'Project',
                "Unexpected root tag '{0}', 'Project' expected.".format(
                        root.tag))

        # Check the project version number.
        version = root.get('version')
        cls._assert(version is not None, "Missing 'version' attribute.")

        try:
            version = int(version)
        except:
            version = None

        cls._assert(version is not None, "Invalid 'version'.")

        if version > cls.version:
            raise UserException(
                    "The project's format is version {0} but only version {1} is supported.".format(version, cls.version))

        # Create the project and populate it.
        project = cls()
        project.name = abs_filename

        # The application specific configuration.
        application = root.find('Application')
        cls._assert(application is not None, "Missing 'Application' tag.")

        project.application_is_pyqt5 = cls._get_bool(application, 'ispyqt5',
                'Application')
        project.application_script = application.get('script', '')

        app_package = application.find('Package')
        cls._assert(app_package is not None,
                "Missing 'Application.Package' tag.")
        cls._load_package(app_package, project.application_package)

        for pyqt_m in application.iterfind('PyQtModule'):
            name = pyqt_m.get('name', '')
            cls._assert(name != '',
                    "Missing or empty 'PyQtModule.name' attribute.")
            project.pyqt_modules.append(name)

        site_packages = application.find('SitePackages')
        cls._assert(site_packages is not None,
                "Missing 'Application.SitePackages' tag.")
        site_packages_package = site_packages.find('Package')
        cls._assert(site_packages_package is not None,
                "Missing 'Application.SitePackages.Package' tag.")
        cls._load_package(site_packages_package, project.site_packages_package)

        stdlib = application.find('Stdlib')
        cls._assert(stdlib is not None, "Missing 'Application.Stdlib' tag.")
        stdlib_package = stdlib.find('Package')
        cls._assert(stdlib_package is not None,
                "Missing 'Application.Stdlib.Package' tag.")
        cls._load_package(stdlib_package, project.stdlib_package)

        for extension_module_element in application.iterfind('ExtensionModule'):
            name = extension_module_element.get('name')
            cls._assert(name is not None,
                    "Missing 'Application.ExtensionModule.name' attribute.")

            path = extension_module_element.get('path')
            cls._assert(path is not None,
                    "Missing 'Application.ExtensionModule.path' attribute.")

            project.extension_modules.append(ExtensionModule(name, path))

        # The Python specific configuration.
        python = root.find('Python')
        cls._assert(python is not None, "Missing 'Python' tag.")

        project.python_host_interpreter = python.get('hostinterpreter', '')
        project.python_target_include_dir = python.get('targetincludedir', '')
        project.python_target_library = python.get('targetlibrary', '')
        project.python_target_stdlib_dir = python.get('targetstdlibdir', '')

        # The other configuration (added in version 1).
        others = root.find('Others')
        if others is not None:
            project.build_dir = others.get('builddir', '')
            project.qmake = others.get('qmake', '')

        return project

    def save(self):
        """ Save the project.  Raise a UserException if there was an error. """

        self._save_project(self.name)

    def save_as(self, filename):
        """ Save the project to the given file and make the file the
        destination of subsequent saves.  Raise a UserException if there was an
        error.
        """

        abs_filename = os.path.abspath(filename)

        self._save_project(abs_filename)

        # Only do this after the project has been successfully saved.
        self.name = abs_filename

    @classmethod
    def _load_package(cls, package_element, package):
        """ Populate a QrcPackage instance. """

        package.name = package_element.get('name')
        cls._assert(package.name is not None,
                "Missing 'Package.name' attribute.")

        package.contents = cls._load_mfs_contents(package_element)

        package.exclusions = []

        for exclude_element in package_element.iterfind('Exclude'):
            name = exclude_element.get('name', '')
            cls._assert(name != '',
                    "Missing or empty 'Package.Exclude.name' attribute.")
            package.exclusions.append(name)

    @classmethod
    def _load_mfs_contents(cls, mfs_element):
        """ Return a list of contents for a memory-filesystem container. """

        contents = []

        for content_element in mfs_element.iterfind('PackageContent'):
            isdir = cls._get_bool(content_element, 'isdirectory',
                    'Package.PackageContent')

            name = content_element.get('name', '')
            cls._assert(name != '',
                    "Missing or empty 'Package.PackageContent.name' attribute.")

            included = cls._get_bool(content_element, 'included',
                    'Package.PackageContent')

            content = QrcDirectory(name, included) if isdir else QrcFile(name, included)

            if isdir:
                content.contents = cls._load_mfs_contents(content_element)

            contents.append(content)

        return contents

    @classmethod
    def _get_bool(cls, element, name, context):
        """ Get a boolean attribute from an element. """

        value = element.get(name)
        try:
            value = int(value)
        except:
            value = None

        cls._assert(value is not None,
                "Missing or invalid boolean value of '{0}.{1}'.".format(
                        context, name))

        return bool(value)

    def _save_project(self, abs_filename):
        """ Save the project to the given file.  Raise a UserException if there
        was an error.
        """

        root = Element('Project', attrib={
            'version': str(self.version)})

        application = SubElement(root, 'Application', attrib={
            'ispyqt5': str(int(self.application_is_pyqt5)),
            'script': self.application_script})

        self._save_package(application, self.application_package)

        for pyqt_module in self.pyqt_modules:
            SubElement(application, 'PyQtModule', attrib={
                'name': pyqt_module})

        site_packages = SubElement(application, 'SitePackages')
        self._save_package(site_packages, self.site_packages_package)

        stdlib = SubElement(application, 'Stdlib')
        self._save_package(stdlib, self.stdlib_package)

        for extension_module in self.extension_modules:
            SubElement(application, 'ExtensionModule', attrib={
                'name': extension_module.name,
                'path': extension_module.path})

        SubElement(root, 'Python', attrib={
            'hostinterpreter': self.python_host_interpreter,
            'targetincludedir': self.python_target_include_dir,
            'targetlibrary': self.python_target_library,
            'targetstdlibdir': self.python_target_stdlib_dir})

        SubElement(root, 'Others', attrib={
            'builddir': self.build_dir,
            'qmake': self.qmake})

        tree = ElementTree(root)

        try:
            tree.write(abs_filename, encoding='unicode', xml_declaration=True)
        except Exception as e:
            raise UserException(
                    "There was an error writing the project file.", str(e))

        self.modified = False

    @classmethod
    def _save_package(cls, container, package):
        """ Save a package in a container element. """

        package_element = SubElement(container, 'Package', attrib={
            'name': package.name})

        cls._save_mfs_contents(package_element, package.contents)

        for exclude in package.exclusions:
            SubElement(package_element, 'Exclude', attrib={
                'name': exclude})

    @classmethod
    def _save_mfs_contents(cls, container, contents):
        """ Save the contents of a memory-filesystem container. """

        for content in contents:
            isdir = isinstance(content, QrcDirectory)

            subcontainer = SubElement(container, 'PackageContent', attrib={
                'name': content.name,
                'included': str(int(content.included)),
                'isdirectory': str(int(isdir))})

            if isdir:
                cls._save_mfs_contents(subcontainer, content.contents)

    @staticmethod
    def _assert(ok, detail):
        """ Validate an assertion and raise a UserException if it failed. """

        if not ok:
            raise UserException("The project file is invalid.", detail)


class QrcPackage():
    """ The encapsulation of a memory-filesystem package. """

    def __init__(self):
        """ Initialise the package. """

        self.name = ''
        self.contents = []
        self.exclusions = ['*.pyc', '*.pyo', '__pycache__']

    def copy(self):
        """ Return a copy of the package. """

        copy = type(self)()

        copy.name = self.name
        copy.contents = [content.copy() for content in self.contents]
        copy.exclusions = list(self.exclusions)

        return copy


class QrcFile():
    """ The encapsulation of a memory-filesystem file. """

    def __init__(self, name, included=True):
        """ Initialise the file. """

        self.name = name
        self.included = included

    def copy(self):
        """ Return a copy of the file. """

        return type(self)(self.name, self.included)


class QrcDirectory(QrcFile):
    """ The encapsulation of a memory-filesystem directory. """

    def __init__(self, name, included=True):
        """ Initialise the directory. """

        super().__init__(name, included)

        self.contents = []

    def copy(self):
        """ Return a copy of the directory. """

        copy = super().copy()

        copy.contents = [content.copy() for content in self.contents]

        return copy


class ExtensionModule():
    """ The encapsulation of an extension module. """

    def __init__(self, name, path):
        """ Initialise the extension. """

        self.name = name
        self.path = path
