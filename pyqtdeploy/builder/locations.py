# Copyright (c) 2015, Riverbank Computing Limited
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

from ..user_exception import UserException


class Locations():
    """ Encapsulate the Python host and target locations for a project. """

    def __init__(self, project, include_dir, interpreter, python_library, source_dir, standard_library_dir):
        """ Initialise the object. """

        self.project = project
        self._include_dir = include_dir
        self._interpreter = interpreter
        self._python_library = python_library
        self._source_dir = source_dir
        self._standard_library_dir = standard_library_dir

    @classmethod
    def get_locations(cls, project, include_dir, interpreter, python_library, source_dir, standard_library_dir):
        """ Create a sub-class instance to handle the locations for a project.
        """

        factory = WindowsLocations if project.is_standard_windows_build() else CustomLocations

        return factory(project, include_dir, interpreter, python_library,
                source_dir, standard_library_dir)

    @property
    def include_dir(self):
        """ The target include directory getter. """

        return self.get_include_dir() if self._include_dir is None else self._include_dir

    def get_include_dir(self):
        """ This must be re-implemented to return the target include directory.
        """

        raise NotImplementedError

    @property
    def interpreter(self):
        """ The host interpreter getter. """

        return self.get_interpreter() if self._interpreter is None else self._interpreter

    def get_interpreter(self):
        """ This must be re-implemented to return the host interpreter. """

        raise NotImplementedError

    @property
    def python_library(self):
        """ The target Python library getter. """

        return self.get_python_library() if self._python_library is None else self._python_library

    def get_python_library(self):
        """ This must be re-implemented to return the target Python library.
        """

        raise NotImplementedError

    @property
    def python_dll(self):
        """ The target Python DLL getter. """

        return self.get_python_dll() if self._python_dll is None else self._python_dll

    def get_python_dll(self):
        """ This must be re-implemented to return the target Python DLL.
        """

        raise NotImplementedError

    @property
    def source_dir(self):
        """ The host source directory getter. """

        return self.get_source_dir() if self._source_dir is None else self._source_dir

    def get_source_dir(self):
        """ This must be re-implemented to return the host source directory.
        """

        raise NotImplementedError

    @property
    def standard_library_dir(self):
        """ The target standard library directory getter. """

        return self.get_standard_library_dir() if self._standard_library_dir is None else self._standard_library_dir

    def get_standard_library_dir(self):
        """ This must be re-implemented to return the target standard library
        directory.
        """

        raise NotImplementedError


class WindowsLocations(Locations):
    """ Encapsulate the locations for a Windows installation. """

    def __init__(self, project, include_dir, interpreter, python_library, source_dir, standard_library_dir):
        """ Initialise the object. """

        super().__init__(project, include_dir, interpreter, python_library,
                source_dir, standard_library_dir)

        self._major, self._minor, _ = project.python_target_version

        from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, QueryValue

        sub_key = 'Software\\Python\\PythonCore\\%d.%d\\InstallPath' % (self._major, self._minor)

        install_path = None

        for key in (HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE):
            try:
                install_path = QueryValue(key, sub_key)
            except OSError:
                pass
            else:
                break

        if install_path is None:
            raise UserException(
                    "Unable to find an installation of Python v%d.%d" % (
                            self._major, self._minor))

        self._install_path = install_path

    def get_include_dir(self):
        """ Re-implemented to return the target include directory. """

        return self._install_path + 'include'

    def get_interpreter(self):
        """ Re-implemented to return the host interpreter. """

        return self._install_path + 'python'

    def get_python_dll(self):
        """ Re-implemented to return the target Python DLL. """

        dll = 'python%d%d.dll' % (self._major, self._minor)

        if self._major >= 3 and self._minor >= 5:
            return self._install_path + dll

        return os.path.expandvars('%SYSTEMROOT%\\System32\\' + dll)

    def get_python_library(self):
        """ Re-implemented to return the target Python library. """

        lib = 'libs\\python%d%d.lib' % (self._major, self._minor)

        return self._install_path + lib

    def get_source_dir(self):
        """ Re-implemented to return the host source directory. """

        # There is no source code with a standard Windows installation.
        return ''

    def get_standard_library_dir(self):
        """ Re-implemented to return the target standard library directory. """

        return self._install_path + 'Lib'


class CustomLocations(Locations):
    """ Encapsulate the locations for a custom installation on any platform.
    """

    def get_include_dir(self):
        """ Re-implemented to return the target include directory. """

        return self.project.path_from_user(
                self.project.python_target_include_dir)

    def get_interpreter(self):
        """ Re-implemented to return the host interpreter. """

        # Note that we assume a relative filename is on PATH rather than being
        # relative to the project file.
        return os.path.expandvars(self.project.python_host_interpreter)

    def get_python_dll(self):
        """ Re-implemented to return the target Python DLL. """

        return self.project.path_from_user(self.project.python_target_dll)

    def get_python_library(self):
        """ Re-implemented to return the target Python library. """

        return self.project.path_from_user(self.project.python_target_library)

    def get_source_dir(self):
        """ Re-implemented to return the host source directory. """

        return self.project.path_from_user(self.project.python_source_dir)

    def get_standard_library_dir(self):
        """ Re-implemented to return the target standard library directory. """

        return self.project.path_from_user(
                self.project.python_target_stdlib_dir)
