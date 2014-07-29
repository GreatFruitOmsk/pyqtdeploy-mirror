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


class ModuleMetadata:
    """ Encapsulate the meta-data for a single extension module. """

    def __init__(self, name, source='', defines='', includepath='', libs=''):
        """ Initialise the object. """

        # The name of the module.
        self.name = name

        # The name of the source file relative to the Modules directory.
        self.source = source if source != '' else name + 'module.c'

        # The DEFINES to add to the .pro file.
        self.defines = defines

        # The INCLUDEPATH to add to the .pro file.
        self.includepath = includepath

        # The LIBS to add to the .pro file.
        self.libs = libs


class PythonMetadata:
    """ Encapsulate the meta-data for a single Python version. """

    # These modules are common to all Python versions.
    _common_modules = (
        ModuleMetadata('cmath', libs='-lm'),
    )

    def __init__(self, required, modules):
        """ Initialise the object. """

        # The sequence of the names of standard library packages that are
        # required by every application.
        self.required = required

        # The sequence of standard library extension modules meta-data.
        self.modules = modules + self._common_modules


class Python3Metadata(PythonMetadata):
    """ Encapsulate the meta-data for a single Python v3 minor version. """

    # These modules are common to all Python v3 minor versions.
    _py3_modules = (
        ModuleMetadata('_datetime'),
    )

    # The required Python v3 modules.
    _py3_required = ('_weakrefset.py', 'abc.py', 'codecs.py',
        'encodings/__init__.py', 'encodings/aliases.py', 'encodings/ascii.py',
        'encodings/cp437.py', 'encodings/latin_1.py', 'encodings/mbcs.py',
        'encodings/utf_8.py', 'importlib/__init__.py', 'io.py', 'types.py',
        'warnings.py')

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(required=self._py3_required,
                modules=modules + self._py3_modules)


class Python2Metadata(PythonMetadata):
    """ Encapsulate the meta-data for a single Python v2 minor version. """

    # These modules are common to all Python v3 minor versions.
    _py2_modules = (
        ModuleMetadata('datetime'),
    )

    # The required Python v2 modules.
    _py2_required = ('atexit.py', )

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(required=self._py2_required,
                modules=modules + self._py2_modules)


# The version-specific meta-data.
_python_metadata = {
    (3, 3):     Python3Metadata(),
    (2, 6):     Python2Metadata()
}


def get_python_metadata(major, minor):
    """ Return the PythonMetadata instance for a particular version of Python.
    It is assume that the version is valid.
    """

    # Find the most recent version that is not later than the desired version.
    version = (major, minor)
    best = None
    best_version = (0, 0)

    for key, value in _python_metadata.items():
        if version >= key and key > best_version:
            best = value
            best_version = key

    return best
