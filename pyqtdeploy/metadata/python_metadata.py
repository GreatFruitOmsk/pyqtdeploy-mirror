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


class BaseMetadata:
    """ Encapsulate the meta-data common to all types of module. """

    def __init__(self, min_version=None, version=None, max_version=None, internal=False, windows=None, deps=(), core=False, defines='', libs=''):
        """ Initialise the object. """

        # A meta-datum is uniquely identified by a range of version numbers.  A
        # version number is a 2-tuple of major and minor version number.  It is
        # an error if version numbers for a particular module overlaps.
        if version is not None:
            if isinstance(version, tuple):
                self.min_version = self.max_version = version
            else:
                # A single digit is interpreted as a range.
                self.min_version = (version, 0)
                self.max_version = (version, 99)
        else:
            if min_version is not None:
                self.min_version = min_version
            else:
                self.min_version = (2, 0)

            if max_version is not None:
                self.max_version = max_version
            else:
                self.max_version = (3, 99)

        # Set if the module is internal.
        self.internal = internal

        # True if the module is Windows-specific, False if non-Windows and None
        # if present on all platforms.
        self.windows = windows

        # The sequence of modules that this one is dependent on.
        self.deps = (deps, ) if isinstance(deps, str) else deps

        # Set if the module is always compiled in to the interpreter library
        # (if it is an extension module) or if it is required (if it is a
        # Python module).
        self.core = core

        # The DEFINES to add to the .pro file.
        self.defines = defines

        # The LIBS to add to the .pro file.
        self.libs = libs


class ExtensionModule(BaseMetadata):
    """ Encapsulate the meta-data for a single extension module. """

    def __init__(self, source, subdir='', min_version=None, version=None, max_version=None, internal=None, windows=None, deps=(), core=False, defines='', libs=''):
        """ Initialise the object. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, internal=internal, windows=windows,
                deps=deps, core=core, defines=defines, libs=libs)

        # The sequence of source files relative to the Modules directory.
        self.source = (source, ) if isinstance(source, str) else source

        # A sub-directory of the Modules directory to add to INCLUDEPATH.
        self.subdir = subdir


class CoreExtensionModule(ExtensionModule):
    """ Encapsulate the meta-data for an extension module that is always
    compiled in to the interpreter library.
    """

    def __init__(self, min_version=None, version=None, max_version=None, internal=None, windows=None, deps=()):
        """ Initialise the object. """

        super().__init__(source=(), min_version=min_version, version=version,
                max_version=max_version, internal=internal, windows=windows,
                deps=deps, core=True)


class PythonModule(BaseMetadata):
    """ Encapsulate the meta-data for a single Python module. """

    def __init__(self, min_version=None, version=None, max_version=None, internal=None, windows=None, deps=(), core=False, modules=None):
        """ Initialise the object. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, internal=internal, windows=windows,
                deps=deps, core=core)

        # The dict of modules or sub-packages if this is a package, otherwise
        # None.
        self.modules = modules


class CorePythonModule(PythonModule):
    """ Encapsulate the meta-data for a Python module that is always required
    an application.
    """

    def __init__(self, min_version=None, version=None, max_version=None, internal=None, windows=None, deps=(), modules=None):
        """ Initialise the object. """

        super().__init__(min_version=min_version, version=version,
                max_version=max_version, internal=internal, windows=windows,
                deps=deps, core=True, modules=modules)


# The meta-data for each module.
_metadata = {
    # These are the public modules.
    '__future__':       PythonModule(),
    '_thread':          CoreExtensionModule(version=3),

    'abc': (            PythonModule(version=(2, 6)),
                        PythonModule(version=(2, 7),
                                deps=('types', '_weakrefset')),
                        PythonModule(version=3,
                                deps='_weakrefset')),
    'array':            ExtensionModule(source='arraymodule.c'),
    'atexit': (         CorePythonModule(version=2,
                                deps='traceback'),
                        ExtensionModule(version=(3, 3),
                                source='atexitmodule.c'),
                        CoreExtensionModule(min_version=(3, 4))),
    'audioop':          ExtensionModule(source='audioop.c'),

    'binascii':         ExtensionModule(source='binascii.c',
                                defines='USE_ZLIB_CRC32', libs='-lz'),
    'bz2': (            ExtensionModule(version=2,
                                source='bz2module.c', libs='-lbz2'),
                        PythonModule(version=3,
                                deps=('_thread', '_bz2', 'io', 'warnings'))),

    'calendar':         PythonModule(deps=('datetime', 'locale')),
    'cmath': (          ExtensionModule(version=(2, 6),
                                source='cmathmodule.c', libs='-lm'),
                        ExtensionModule(version=(2, 7),
                                source=['cmathmodule.c', '_math.c'],
                                libs='-lm'),
                        ExtensionModule(version=3,
                                source=['cmathmodule.c', '_math.c'],
                                libs='-lm')),
    'codecs':           PythonModule(deps='_codecs'),
    'copy_reg':         PythonModule(version=2, deps='types'),
    'copyreg':          PythonModule(version=3),
    'cPickle':          ExtensionModule(version=2, source='cPickle.c'),
    'crypt': (          ExtensionModule(version=2,
                                source='cryptmodule.c', libs='-lcrypt'),
                        PythonModule(version=3,
                                deps=('collections', '_crypt', 'random',
                                        'string'))),
    'cStringIO':        ExtensionModule(version=2, source='cStringIO.c'),

    'datetime': (       ExtensionModule(version=2,
                                source=('datetimemodule.c', 'timemodule.c'),
                                deps='_strptime'),
                        PythonModule(version=3,
                                deps=('_datetime', 'math', '_strptime',
                                        'time'))),
    'dbm': (            ExtensionModule(version=2,
                                source='dbmmodule.c',
                                defines='HAVE_NDBM_H', libs='-lndbm'),
                        PythonModule(version=3,
                                deps=('io', 'os', 'struct'),
                                modules={
                                    'dumb': PythonModule(deps=('collections',
                                                    'io', 'os')),
                                    'gnu':  PythonModule(deps='_gdbm'),
                                    'ndbm': PythonModule(deps='_dbm')})),
    # TODO - the non-core encodings.
    'encodings': (      PythonModule(version=2,
                                deps=('codecs', 'encodings.aliases'),
                                modules={
                                    'aliases':  PythonModule(),
                                    'ascii':    PythonModule(),
                                    'cp437':    PythonModule(),
                                    'latin_1':  PythonModule(),
                                    'mbcs':     PythonModule(),
                                    'utf_8':    PythonModule()}),
                        CorePythonModule(version=3,
                                deps=('codecs', 'encodings.aliases'),
                                modules={
                                    'aliases':  CorePythonModule(),
                                    'ascii':    CorePythonModule(),
                                    'cp437':    CorePythonModule(),
                                    'latin_1':  CorePythonModule(),
                                    'mbcs':     CorePythonModule(),
                                    'utf_8':    CorePythonModule()})),
    'errno':            CoreExtensionModule(),
    'exceptions':       CoreExtensionModule(version=2),

    'faulthandler':     CoreExtensionModule(version=3),
    'fcntl':            ExtensionModule(source='fcntlmodule.c'),
    'functools': (      PythonModule(version=2,
                                deps='_functools'),
                        PythonModule(version=(3, 3),
                                deps=('collections', '_functools', '_thread')),
                        PythonModule(min_version=(3, 4),
                                deps=('abc', 'collections', '_functools',
                                        '_thread', 'types', 'weakref'))),
    'future_builtins':  ExtensionModule(version=2, source='future_builtins.c'),

    'gc':               CoreExtensionModule(),
    'gdbm':             ExtensionModule(version=2, source='gdbmmodule.c',
                                libs='-lgdbm'),
    'genericpath':      PythonModule(internal=True, deps=('os', 'stat')),
    'grp':              ExtensionModule(source='grpmodule.c'),

    'imageop':          ExtensionModule(version=2, source='imageop.c'),
    'imp': (            CoreExtensionModule(version=2),
                        PythonModule(version=(3, 3),
                                deps=('_imp', 'importlib', 'os', 'tokenize',
                                        'warnings')),
                        PythonModule(min_version=(3, 4),
                                deps=('_imp', 'importlib', 'os', 'tokenize',
                                        'types', 'warnings'))),

    'importlib': (      PythonModule(version=(2, 7),
                                modules={}),
                        CorePythonModule(version=3,
                                deps=('types', 'warnings'), modules={})),
    'io': (             PythonModule(version=(2, 6),
                                deps=('__future__', 'abc', 'array', '_bytesio',
                                        'codecs', '_fileio', 'locale',
                                        'threading', 'os')),
                        PythonModule(version=(2, 7),
                                deps=('abc', '_io')),
                        CorePythonModule(version=3,
                                deps=('abc', '_io'))),
    'itertools': (      ExtensionModule(version=2, source='itertoolsmodule.c'),
                        CoreExtensionModule(version=3)),

    'linuxaudiodev':    ExtensionModule(version=2, source='linuxaudiodev.c'),
    'locale': (         PythonModule(version=2,
                                deps=('encodings', 'encodings.aliases',
                                        'functools', '_locale', 'os',
                                        'operator', 're')),
                        PythonModule(version=3,
                                deps=('collections', 'encodings',
                                        'encodings.aliases', 'functools',
                                        '_locale', 'os', 're'))),

    'marshal':          CoreExtensionModule(),
    'math': (           ExtensionModule(version=(2, 6),
                                source='mathmodule.c', libs='-lm'),
                        ExtensionModule(version=(2, 7),
                                source=('mathmodule.c', '_math.c'),
                                libs='-lm'),
                        ExtensionModule(version=3,
                                source=('mathmodule.c', '_math.c'),
                                libs='-lm')),
    'mmap':             ExtensionModule(source='mmapmodule.c'),
    # TODO - msvcrt on Windows
    'msvcrt':           ExtensionModule(source='TODO', windows=True),

    'nis':              ExtensionModule(source='nismodule.c', libs='-lnsl'),

    'operator': (       ExtensionModule(version=2,
                                source='operator.c'),
                        CoreExtensionModule(version=(3, 3)),
                        PythonModule(min_version=(3, 4),
                                deps='_operator')),
    'os': (             PythonModule(version=2,
                                deps=('copy_reg', 'errno', 'nt', 'ntpath',
                                        'posix', 'posixpath', 'subprocess',
                                        'warnings')),
                        PythonModule(version=3,
                                deps=('collections', 'copyreg', 'errno', 'io',
                                        'nt', 'ntpath', 'posix', 'posixpath',
                                        'stat', 'subprocess', 'warnings'))),
    'ossaudiodev':      ExtensionModule(source='ossaudiodev.c'),

    'parser':           ExtensionModule(source='parsermodule.c'),
    'pickle': (         PythonModule(version=2,
                                deps=('binascii', 'copy_reg', 'cStringIO',
                                        'marshal', 're', 'struct', 'types')),
                        PythonModule(version=(3, 3),
                                deps=('codecs', '_compat_pickle', 'copyreg',
                                        'io', 'marshal', '_pickle', 're',
                                        'struct', 'types')),
                        PythonModule(min_version=(3, 4),
                                deps=('codecs', '_compat_pickle', 'copyreg',
                                        'io', 'itertools', 'marshal',
                                        '_pickle', 're', 'struct', 'types'))),
    'pwd':              CoreExtensionModule(),
    'pyexpat':          ExtensionModule(
                                source=('expat/xmlparse.c', 'expat/xmlrole.c',
                                        'expat/xmltok.c', 'pyexpat.c'),
                                defines='HAVE_EXPAT_CONFIG_H', subdir='expat'),

    'random': (         PythonModule(version=(2, 6),
                                deps=('__future__', 'binascii', 'math', 'os',
                                        '_random', 'time', 'types',
                                        'warnings')),
                        PythonModule(version=(2, 7),
                                deps=('__future__', 'binascii', 'hashlib',
                                        'math', 'os', '_random', 'time',
                                        'types', 'warnings')),
                        PythonModule(version=(3, 3),
                                deps=('collections', 'hashlib', 'math', 'os',
                                        '_random', 'time', 'types',
                                        'warnings')),
                        PythonModule(version=(3, 4),
                                deps=('_collections_abc', 'hashlib', 'math',
                                        'os', '_random', 'time', 'types',
                                        'warnings'))),
    're': (             PythonModule(version=2,
                                deps=('copy_reg', 'sre_compile',
                                        'sre_constants', 'sre_parse')),
                        PythonModule(version=(3, 3),
                                deps=('copyreg', 'functools', 'sre_compile',
                                        'sre_constants', 'sre_parse')),
                        PythonModule(min_version=(3, 4),
                                deps=('copyreg', 'sre_compile',
                                        'sre_constants', 'sre_parse'))),
    'readline':         ExtensionModule(source='readline.c',
                                libs='-lreadline -ltermcap'),
    'resource':         ExtensionModule(source='resource.c'),

    'select':           ExtensionModule(source='selectmodule.c'),
    'signal':           CoreExtensionModule(),
    'spwd':             ExtensionModule(source='spwdmodule.c'),
    'stat': (           PythonModule(version=2),
                        PythonModule(version=(3, 3)),
                        PythonModule(min_version=(3, 4),
                                deps='_stat')),
    'struct':           PythonModule(deps='_struct'),
    'subprocess': (     PythonModule(version=2,
                                deps=('errno', 'fcntl', 'gc', 'msvcrt', 'os',
                                        'pickle', 'select', 'signal',
                                        '_subprocess', 'threading',
                                        'traceback', 'types')),
                        PythonModule(version=(3, 3),
                                deps=('errno', 'gc', 'io', 'msvcrt', 'os',
                                        '_posixsubprocess', 'select', 'signal',
                                        'threading', 'time', 'traceback',
                                        'warnings', '_winapi')),
                        PythonModule(min_version=(3, 4),
                                deps=('errno', 'gc', 'io', 'msvcrt', 'os',
                                        '_posixsubprocess', 'select',
                                        'selectors', 'signal', 'threading',
                                        'time', 'traceback', 'warnings',
                                        '_winapi'))),
    'syslog':           ExtensionModule(source='syslogmodule.c'),

    'termios':          ExtensionModule(source='termios.c'),
    'thread':           CoreExtensionModule(version=2),
    'time':             ExtensionModule(source='timemodule.c', libs='-lm'),
    'threading': (      PythonModule(version=(2, 6),
                                deps=('collections', 'functools', 'random',
                                        'thread', 'time', 'traceback',
                                        'warnings')),
                        PythonModule(version=(2, 7),
                                deps=('collections', 'random', 'thread',
                                        'time', 'traceback', 'warnings')),
                        PythonModule(version=(3, 3),
                                deps=('_thread', 'time', 'traceback',
                                        '_weakrefset')),
                        PythonModule(min_version=(3, 4),
                                deps=('_collections', 'itertools', '_thread',
                                        'time', 'traceback', '_weakrefset'))),
    'tokenize': (       PythonModule(version=(2, 6),
                                deps=('re', 'string', 'token')),
                        PythonModule(version=(2, 7),
                                deps=('itertools', 're', 'string', 'token')),
                        PythonModule(version=3,
                                deps=('codecs', 'collections', 'io',
                                        'itertools', 're', 'token'))),
    'traceback': (      PythonModule(version=2,
                                deps=('linecache', 'types')),
                        PythonModule(version=(3, 3),
                                deps='linecache'),
                        PythonModule(min_version=(3, 4),
                                deps=('linecache', 'operator'))),
    'types':            PythonModule(),

    'unicodedata':      ExtensionModule(source='unicodedata.c'),

    'warnings': (       PythonModule(version=2,
                                deps=('linecache', 'types', 're',
                                        '_warnings')),
                        PythonModule(version=3,
                                deps=('linecache', 're', '_warnings'))),

    'zipimport':        CoreExtensionModule(),
    'zlib':             ExtensionModule(source='zlibmodule.c', libs='-lz'),

    # These are internal modules.
    '_ast':             CoreExtensionModule(internal=True),

    '_bisect':          ExtensionModule(internal=True,
                                source='_bisectmodule.c'),
    '_bsdb':            ExtensionModule(version=2,
                                internal=True, source='_bsddb.c', libs='-ldb'),
    '_bytesio':         ExtensionModule(version=(2, 6),
                                internal=True, source='_bytesio.c'),
    '_bz2':             ExtensionModule(version=3, internal=True,
                                source='_bz2mocule.c', libs='-lbz2'),

    '_codecs':          CoreExtensionModule(internal=True),
    '_codecs_cn':       ExtensionModule(internal=True,
                                source='cjkcodecs/_codecs_cn.c'),
    '_codecs_hk':       ExtensionModule(internal=True,
                                source='cjkcodecs/_codecs_hk.c'),
    '_codecs_iso2022':  ExtensionModule(internal=True,
                                source='cjkcodecs/_codecs_iso2022.c'),
    '_codecs_jp':       ExtensionModule(internal=True,
                                source='cjkcodecs/_codecs_jp.c'),
    '_codecs_kr':       ExtensionModule(internal=True,
                                source='cjkcodecs/_codecs_kr.c'),
    '_codecs_tw':       ExtensionModule(internal=True,
                                source='cjkcodecs/_codecs_tw.c'),
    '_collections': (   ExtensionModule(version=2,
                                internal=True, source='_collectionsmodule.c'),
                        CoreExtensionModule(version=3,
                                internal=True)),
    '_collections_abc': PythonModule(min_version=(3, 4),
                                internal=True, deps='abc'),
    '_compat_pickle':   PythonModule(version=3, internal=True),
    '_crypt':           ExtensionModule(version=3, internal=True,
                                source='_cryptmodule.c', libs='-lcrypt'),
    '_csv':             ExtensionModule(internal=True, source='_csv.c'),
    '_curses':          ExtensionModule(internal=True,
                                source='_cursesmodule.c',
                                libs='-lcurses -ltermcap'),
    '_curses_panel':    ExtensionModule(internal=True,
                                source='_curses_panel.c',
                                libs='-lpanel -lcurses'),

    '_datetime':        ExtensionModule(version=3,
                                internal=True, source='_datetimemodule.c'),
    '_dbm':             ExtensionModule(version=3, source='_dbmmodule.c',
                                defines='HAVE_NDBM_H', libs='-lndbm'),

    '_elementtree': (   ExtensionModule(version=2,
                                internal=True, source='_elementtree.c',
                                defines='HAVE_EXPAT_CONFIG_H USE_PYEXPAT_CAPI',
                                deps='pyexpat'),
                        ExtensionModule(version=3,
                                internal=True, source='_elementtree.c',
                                defines='HAVE_EXPAT_CONFIG_H USE_PYEXPAT_CAPI',
                                deps=('copy', 'pyexpat',
                                        'xml.etree.ElementPath'))),

    '_fileio':          ExtensionModule(version=(2, 6),
                                internal=True, source='_fileio.c'),
    '_functools': (     ExtensionModule(version=2,
                                internal=True, source='_functoolsmodule.c'),
                        CoreExtensionModule(version=3,
                                internal=True)),

    '_gdbm':            ExtensionModule(version=3, internal=True,
                                source='_gdbmmodule.c', libs='-lgdbm'),

    '_hashlib':         ExtensionModule(internal=True, source='_hashopenssl.c',
                                libs='-lssl -lcrypto'),
    '_heapq':           ExtensionModule(internal=True,
                                source='_heapqmodule.c'),
    '_hotshot':         ExtensionModule(version=2, internal=True,
                                source='_hotshotmodule.c'),

    '_imp':             CoreExtensionModule(version=3, internal=True),
    '_io': (            ExtensionModule(version=(2, 7),
                                internal=True,
                                source=('_io/bufferedio.c', '_io/bytesio.c',
                                        '_io/fileio.c', '_io/iobase.c',
                                        '_io/_iomodule.c', '_io/stringio.c',
                                        '_io/textio.c'),
                                subdir='_io'),
                        CoreExtensionModule(version=3,
                                internal=True)),

    '_json':            ExtensionModule(internal=True, source='_jsonmodule.c'),

    '_locale': (        ExtensionModule(version=2,
                                internal=True, source='_localemodule.c',
                                libs='-lintl'),
                        CoreExtensionModule(version=3,
                                internal=True)),
    '_lsprof':          ExtensionModule(internal=True,
                                source=('_lsprof.c', 'rotatingtree.c')),
    '_lzma':            ExtensionModule(version=3, internal=True,
                                source='_lzmamodule.c', libs='-llzma'),

    '_md5': (           ExtensionModule(version=2,
                                internal=True,
                                source=('md5module.c', 'md5.c')),
                        ExtensionModule(version=3,
                                internal=True, source='md5module.c')),
    '_multibytecodec':  ExtensionModule(internal=True,
                                source='cjkcodecs/_multibytecodec.c'),

    # TODO - nt on Windows
    'nt':               ExtensionModule(internal=True, source='TODO',
                                windows=True),
    'ntpath':           PythonModule(internal=True, windows=True,
                                deps=('genericpath', 'nt', 'os', 'stat',
                                        'string', 'warnings')),

    '_opcode':          ExtensionModule(min_version=(3, 4),
                                internal=True, source='_opcode.c'),
    '_operator':        CoreExtensionModule(min_version=(3, 4)),

    '_pickle':          ExtensionModule(version=3, source='_pickle.c'),
    'posix':            CoreExtensionModule(internal=True, windows=False),
    'posixpath':        PythonModule(internal=True, windows=False,
                                deps=('genericpath', 'os', 'pwd', 're', 'stat',
                                        'warnings')),
    '_posixsubprocess': ExtensionModule(version=3, internal=True,
                                windows=False, source='_posixsubprocess.c'),

    '_random':          ExtensionModule(source='_randommodule.c'),

    '_sha':             ExtensionModule(version=2, internal=True,
                                source='shamodule.c'),
    '_sha1':            ExtensionModule(version=3, internal=True,
                                source='sha1module.c'),
    '_sha256':          ExtensionModule(internal=True,
                                source='sha256module.c'),
    '_sha512':          ExtensionModule(internal=True,
                                source='sha512module.c'),

    '_socket': (        ExtensionModule(version=(2, 6),
                                internal=True, source='socketmodule.c'),
                        ExtensionModule(version=(2, 7),
                                internal=True,
                                source=('socketmodule.c', 'timemodule.c')),
                        ExtensionModule(version=3,
                                internal=True, source='socketmodule.c')),
    '_sqlite3':         ExtensionModule(internal=True,
                                source=('_sqlite/cache.c',
                                        '_sqlite/connection.c',
                                        '_sqlite/cursor.c',
                                        '_sqlite/microprotocols.c',
                                        '_sqlite/module.c',
                                        '_sqlite/prepare_protocol.c',
                                        '_sqlite/row.c', '_sqlite/statement.c',
                                        '_sqlite/util.c'),
                                defines='SQLITE_OMIT_LOAD_EXTENSION',
                                subdir='_sqlite'),
    '_sre':             CoreExtensionModule(),
    'sre_compile':      PythonModule(internal=True,
                                deps=('array', '_sre', 'sre_constants',
                                        'sre_parse')),
    'sre_constants': (  PythonModule(version=(2, 6),
                                internal=True),
                        PythonModule(version=(2, 7),
                                internal=True, deps='_sre'),
                        PythonModule(version=3,
                                internal=True, deps='_sre')),
    'sre_parse': (      PythonModule(version=2,
                                internal=True, deps='sre_constants'),
                        PythonModule(version=3,
                                internal=True,
                                deps=('sre_constants', 'warnings'))),
    '_ssl':             ExtensionModule(internal=True, source='_ssl.c',
                                libs='-lssl -lcrypto'),
    '_stat':            CoreExtensionModule(min_version=(3, 4), internal=True),
    '_string':          CoreExtensionModule(version=3, internal=True),
    '_strptime': (      PythonModule(version=2,
                                internal=True,
                                deps=('calendar', 'datetime', 'locale', 're',
                                        'thread', 'time')),
                        PythonModule(version=3,
                                internal=True,
                                deps=('calendar', 'datetime', 'locale', 're',
                                        '_thread', 'time'))),
    '_struct':          ExtensionModule(internal=True, source='_struct.c'),
    # TODO - _subprocess on Windows
    '_subprocess':      ExtensionModule(version=2, internal=True,
                                source='TODO', windows=True),
    '_symtable':        CoreExtensionModule(internal=True),

    '_testcapi':        ExtensionModule(internal=True,
                                source='_testcapimodule.c'),
    '_tracemalloc':     CoreExtensionModule(min_version=(3, 4), internal=True),

    '_warnings':        CoreExtensionModule(internal=True),
    '_weakref': (       ExtensionModule(version=(2, 6),
                                internal=True, source='_weakref.c'),
                        CoreExtensionModule(version=(2, 7),
                                internal=True),
                        CoreExtensionModule(version=3)),
    '_weakrefset': (    PythonModule(version=(2, 7),
                                internal=True, deps='_weakref'),
                        PythonModule(version=3,
                                internal=True, deps='_weakref')),
    # TODO - _winapi on Windows
    '_winapi':          ExtensionModule(version=3, internal=True,
                                source='TODO', windows=True),
}


def _get_module_for_version(name, major, minor):
    """ Return the module meta-data for a particular version.  None is returned
    if there is none but this should not happen with correct meta-data.
    """

    versions = _metadata.get(name)

    if versions is None:
        return None

    if not isinstance(versions, tuple):
        versions = (versions, )

    for module in versions:
        min_major, min_minor = module.min_version
        max_major, max_minor = module.max_version

        if major >= min_major and major <= max_major:
            if minor >= min_minor and minor <= max_minor:
                break
    else:
        module = None

    return module


def get_python_metadata(major, minor):
    """ Return the dict of PythonMetadata instances for a particular version of
    Python.  It is assumed that the version is valid.
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


if __name__ == '__main__':

    def check_module_for_version(name, module, major, minor, unused):
        """ Sanity check a particular module. """

        for dep in module.deps:
            dep_module = _get_module_for_version(dep, major, minor)
            if dep_module is None:
                print("Unknown module '{0}'".format(dep))
            elif dep_module.internal and not dep_module.core:
                # This internal, non-core module is used.
                unused[dep] = False

        if module.internal and not module.core and name not in unused:
            # This internal, non-core module is not used so far.
            unused[name] = True

        if isinstance(module, PythonModule) and module.modules is not None:
            check_metadata_for_version(module.modules, major, minor, unused)

    def check_metadata_for_version(metadata, major, minor, unused):
        """ Sanity check a dict of modules. """

        for name, versions in metadata.items():
            if not isinstance(versions, tuple):
                versions = (versions, )

            # Check the version numbers.
            matches = []
            for module in versions:
                min_major, min_minor = module.min_version
                max_major, max_minor = module.max_version

                if min_major > max_major:
                    print("Module '{0}' major version numbers are swapped".format(name))
                elif min_major == max_major and min_minor > max_minor:
                    print("Module '{0}' minor version numbers are swapped".format(name))

                if major >= min_major and major <= max_major:
                    if minor >= min_minor and minor <= max_minor:
                        matches.append(module)

            nr_matches = len(matches)

            if nr_matches != 1:
                if nr_matches > 1:
                    print("Module '{0}' has overlapping versions".format(name))

                continue

            check_module_for_version(name, matches[0], major, minor, unused)

    def check_version(major, minor):
        """ Carry out sanity checks for a particular version of Python. """

        print("Checking Python v{0}.{1}...".format(major, minor))

        unused = {}

        check_metadata_for_version(_metadata, major, minor, unused)

        # See if there are any internal, non-core modules that are unused.
        for name, unused_state in unused.items():
            if unused_state:
                print("Unused module '{0}'".format(name))

    # Check each supported version.
    check_version(2, 6)
    check_version(2, 7)
    check_version(3, 3)
    check_version(3, 4)
