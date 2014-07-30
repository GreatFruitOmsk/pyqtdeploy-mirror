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

    def __init__(self, name, sources=None, defines='', libs='', subdir=''):
        """ Initialise the object. """

        # The name of the module.
        self.name = name

        # The sequence of the source files relative to the Modules directory.
        if sources is None:
            sources = [name + 'module.c']

        self.sources = sources

        # The DEFINES to add to the .pro file.
        self.defines = defines

        # The LIBS to add to the .pro file.
        self.libs = libs

        # A sub-directory of the Modules directory to add to INCLUDEPATH.
        self.subdir = subdir


class PythonMetadata:
    """ Encapsulate the meta-data for a single Python version. """

    # These modules are common to all Python versions.  The order is the same
    # as that in setup.py to make it easier to check for updates.
    _common_modules = (
        ModuleMetadata('array'),
        ModuleMetadata('_struct', sources=['_struct.c']),
        ModuleMetadata('time', libs='-lm'),
        ModuleMetadata('_random'),
        ModuleMetadata('_bisect'),
        ModuleMetadata('_heapq'),
        ModuleMetadata('_json'),
        ModuleMetadata('_testcapi'),
        ModuleMetadata('_lsprof', sources=['_lsprof.c', 'rotatingtree.c']),
        ModuleMetadata('unicodedata', sources=['unicodedata.c']),
        ModuleMetadata('fcntl'),
        ModuleMetadata('pwd'),
        ModuleMetadata('grp'),
        ModuleMetadata('spwd'),
        ModuleMetadata('select'),
        ModuleMetadata('parser'),
        ModuleMetadata('mmap'),
        ModuleMetadata('syslog'),
        ModuleMetadata('audioop', sources=['audioop.c']),
        ModuleMetadata('readline', sources=['readline.c'],
                libs='-lreadline -ltermcap'),
        ModuleMetadata('_crypt', libs='-lcrypt'),
        ModuleMetadata('_csv', sources=['_csv.c']),
        ModuleMetadata('_ssl', sources=['_ssl.c'], libs='-lssl -lcrypto'),
        ModuleMetadata('_hashlib', sources=['_hashopenssl.c'],
                libs='-lssl -lcrypto'),
        ModuleMetadata('_sha256', sources=['sha256module.c']),
        ModuleMetadata('_sha512', sources=['sha512module.c']),
        ModuleMetadata('_sqlite3',
                sources=['_sqlite/cache.c', '_sqlite/connection.c',
                        '_sqlite/cursor.c', '_sqlite/microprotocols.c',
                        '_sqlite/module.c', '_sqlite/prepare_protocol.c',
                        '_sqlite/row.c', '_sqlite/statement.c',
                        '_sqlite/util.c'],
                defines='SQLITE_OMIT_LOAD_EXTENSION', subdir='_sqlite'),
        ModuleMetadata('termios', sources=['termios.c']),
        ModuleMetadata('resource', sources=['resource.c']),
        ModuleMetadata('nis', libs='-lnsl'),
        ModuleMetadata('_curses', libs='-lcurses -ltermcap'),
        ModuleMetadata('_curses_panel', sources=['_curses_panel.c'],
                libs='-lpanel -lcurses'),
        ModuleMetadata('zlib', libs='-lz'),
        ModuleMetadata('binascii', sources=['binascii.c'],
                defines='USE_ZLIB_CRC32', libs='-lz'),
        ModuleMetadata('pyexpat',
                sources=['expat/xmlparse.c', 'expat/xmlrole.c',
                        'expat/xmltok.c', 'pyexpat.c'],
                defines='HAVE_EXPAT_CONFIG_H', subdir='expat'),
        ModuleMetadata('_elementtree', sources=['_elementtree.c'],
                defines='HAVE_EXPAT_CONFIG_H USE_PYEXPAT_CAPI'),
        ModuleMetadata('_multibytecodec',
                sources=['cjkcodecs/_multibytecodec.c']),
        ModuleMetadata('_codecs_cn', sources=['cjkcodecs/_codecs_cn.c']),
        ModuleMetadata('_codecs_hk', sources=['cjkcodecs/_codecs_hk.c']),
        ModuleMetadata('_codecs_iso2022',
                sources=['cjkcodecs/_codecs_iso2022.c']),
        ModuleMetadata('_codecs_jp', sources=['cjkcodecs/_codecs_jp.c']),
        ModuleMetadata('_codecs_kr', sources=['cjkcodecs/_codecs_kr.c']),
        ModuleMetadata('_codecs_tw', sources=['cjkcodecs/_codecs_tw.c']),
        ModuleMetadata('ossaudiodev', sources=['ossaudiodev.c']),
    )

    def __init__(self, required, modules):
        """ Initialise the object. """

        # The sequence of the names of standard library packages that are
        # required by every application.
        self.required = required

        # The sequence of standard library extension modules meta-data.
        self.modules = modules + self._common_modules


class Python_3_Metadata(PythonMetadata):
    """ Encapsulate the meta-data common to all Python v3 versions. """

    _py_3_modules = (
        ModuleMetadata('cmath', sources=['cmathmodule.c', '_math.c'],
                libs='-lm'),
        ModuleMetadata('math', sources=['mathmodule.c', '_math.c'],
                libs='-lm'),
        ModuleMetadata('_datetime'),
        ModuleMetadata('_pickle', sources=['_pickle.c']),
        ModuleMetadata('atexit'),
        ModuleMetadata('_posixsubprocess', sources=['_posixsubprocess.c']),
        ModuleMetadata('_socket', sources=['socketmodule.c']),
        ModuleMetadata('_md5', sources=['md5module.c']),
        ModuleMetadata('_sha1', sources=['sha1module.c']),
        ModuleMetadata('_dbm', defines='HAVE_NDBM_H', libs='-lndbm'),
        ModuleMetadata('_gdbm', libs='-lgdbm'),
        ModuleMetadata('_bz2', libs='-lbz2'),
        ModuleMetadata('_lzma', libs='-llzma'),
    )

    # The required Python v3 modules.
    _py_3_required = ('_weakrefset.py', 'abc.py', 'codecs.py',
        'encodings/__init__.py', 'encodings/aliases.py', 'encodings/ascii.py',
        'encodings/cp437.py', 'encodings/latin_1.py', 'encodings/mbcs.py',
        'encodings/utf_8.py', 'importlib/__init__.py', 'io.py', 'types.py',
        'warnings.py')

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(required=self._py_3_required,
                modules=modules + self._py_3_modules)


class Python_3_3_Metadata(Python_3_Metadata):
    """ Encapsulate the meta-data for Python v3.3. """


class Python_3_4_Metadata(Python_3_Metadata):
    """ Encapsulate the meta-data for Python v3.4. """

    _py_3_4_modules = (
        ModuleMetadata('_opcode', sources=['_opcode.c']),
    )

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(modules=modules + self._py_3_4_modules)


class Python_2_Metadata(PythonMetadata):
    """ Encapsulate the meta-data common to all Python v2 versions. """

    _py_2_modules = (
        ModuleMetadata('strop'),
        ModuleMetadata('datetime',
                sources=['datetimemodule.c', 'timemodule.c']),
        ModuleMetadata('itertools'),
        ModuleMetadata('future_builtins', sources=['future_builtins.c']),
        ModuleMetadata('_collections'),
        ModuleMetadata('operator', sources=['operator.c']),
        ModuleMetadata('_functools'),
        ModuleMetadata('_hotshot'),
        ModuleMetadata('_locale', libs='-lintl'),
        ModuleMetadata('cStringIO', sources=['cStringIO.c']),
        ModuleMetadata('cPickle', sources=['cPickle.c']),
        ModuleMetadata('imageop', sources=['imageop.c']),
        ModuleMetadata('_sha', sources=['shamodule.c']),
        ModuleMetadata('_md5', sources=['md5module.c', 'md5.c']),
        ModuleMetadata('_bsddb', sources=['_bsddb.c'], libs='-ldb'),
        ModuleMetadata('bsddb185', sources=['bsddbmodule.c'], libs='-ldb'),
        ModuleMetadata('dbm', defines='HAVE_NDBM_H', libs='-lndbm'),
        ModuleMetadata('gdbm', libs='-lgdbm'),
        ModuleMetadata('bz2', libs='-lbz2'),
        ModuleMetadata('linuxaudiodev', sources=['linuxaudiodev.c']),
    )

    # The required Python v2 modules.
    _py_2_required = ('atexit.py', )

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(required=self._py_2_required,
                modules=modules + self._py_2_modules)


class Python_2_6_Metadata(Python_2_Metadata):
    """ Encapsulate the meta-data for Python v2.6. """

    _py_2_6_modules = (
        ModuleMetadata('_weakref', sources=['_weakref.c']),
        ModuleMetadata('cmath', libs='-lm'),
        ModuleMetadata('math', libs='-lm'),
        ModuleMetadata('_fileio', sources=['_fileio.c']),
        ModuleMetadata('_bytesio', sources=['_bytesio.c']),
        ModuleMetadata('_socket', sources=['socketmodule.c']),
    )

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(modules=modules + self._py_2_6_modules)


class Python_2_7_Metadata(Python_2_Metadata):
    """ Encapsulate the meta-data for Python v2.7. """

    # Note that this for Python v2.7.8 (but should be fine for earlier
    # versions) so that we don't have to have meta-data for individual patch
    # versions.
    _py_2_7_modules = (
        ModuleMetadata('cmath', sources=['cmathmodule.c', '_math.c'],
                libs='-lm'),
        ModuleMetadata('math', sources=['mathmodule.c', '_math.c'],
                libs='-lm'),
        ModuleMetadata('_io',
                sources=['_io/bufferedio.c', '_io/bytesio.c', '_io/fileio.c',
                        '_io/iobase.c', '_io/_iomodule.c', '_io/stringio.c',
                        '_io/textio.c'],
                subdir='_io'),
        ModuleMetadata('_socket', sources=['socketmodule.c', 'timemodule.c']),
    )

    def __init__(self, modules=()):
        """ Initialise the object. """

        super().__init__(modules=modules + self._py_2_7_modules)


# The version-specific meta-data.
_python_metadata = {
    (3, 4):     Python_3_4_Metadata(),
    (3, 3):     Python_3_3_Metadata(),
    (2, 7):     Python_2_7_Metadata(),
    (2, 6):     Python_2_6_Metadata()
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
