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


class PythonMetadata:
    """ Encapsulate the meta-data for a single Python version. """

    def __init__(self, required):
        """ Initialise the object. """

        # The sequence of the names of standard library packages that are
        # required by every application.
        self.required = required


class Python3Metadata(PythonMetadata):
    """ Encapsulate the meta-data for a single Python v3 minor version. """

    # The required Python v3 modules.
    _required = ('_weakrefset.py', 'abc.py', 'codecs.py',
        'encodings/__init__.py', 'encodings/aliases.py', 'encodings/ascii.py',
        'encodings/cp437.py', 'encodings/latin_1.py', 'encodings/mbcs.py',
        'encodings/utf_8.py', 'importlib/__init__.py', 'io.py', 'types.py',
        'warnings.py')

    def __init__(self):
        """ Initialise the object. """

        super().__init__(self._required)


class Python2Metadata(PythonMetadata):
    """ Encapsulate the meta-data for a single Python v2 minor version. """

    # The required Python v2 modules.
    _required = ('atexit.py', )

    def __init__(self):
        """ Initialise the object. """

        super().__init__(self._required)


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
