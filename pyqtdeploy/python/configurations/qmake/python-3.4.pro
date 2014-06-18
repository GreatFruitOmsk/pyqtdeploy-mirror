PYQTDEPLOY_PYVERSION = 3.4
PYQTDEPLOY_ABIFLAGS = m
PYQTDEPLOY_SYSROOT = /Users/phil/usr/sysroot

TEMPLATE = lib

TARGET = python$$PYQTDEPLOY_PYVERSION$$PYQTDEPLOY_ABIFLAGS

CONFIG -= qt
CONFIG += warn_off staticlib release

OBJECTS_DIR = .obj

DEFINES += NDEBUG Py_BUILD_CORE

INCLUDEPATH += Include

!win32 {
    QMAKE_CFLAGS -= -O2
    QMAKE_CFLAGS += -fwrapv -O3
}

target.path = $$PYQTDEPLOY_SYSROOT/lib

headers.path = $$PYQTDEPLOY_SYSROOT/include/python$$PYQTDEPLOY_PYVERSION$$PYQTDEPLOY_ABIFLAGS
headers.files = pyconfig.h Include/*.h

stdlib.path = $$PYQTDEPLOY_SYSROOT/lib/python$$PYQTDEPLOY_PYVERSION
stdlib.files = Lib/*

INSTALLS += target headers stdlib

PARSER_SOURCES = \
    Parser/myreadline.c Parser/parsetok.c Parser/tokenizer.c \
    Parser/acceler.c \
    Parser/grammar1.c \
    Parser/listnode.c \
    Parser/node.c \
    Parser/parser.c \
    Parser/bitset.c \
    Parser/metagrammar.c \
    Parser/firstsets.c \
    Parser/grammar.c \
    Parser/pgen.c

OBJECT_SOURCES =\
    Objects/abstract.c \
    Objects/accu.c \
    Objects/boolobject.c \
    Objects/bytes_methods.c \
    Objects/bytearrayobject.c \
    Objects/bytesobject.c \
    Objects/cellobject.c \
    Objects/classobject.c \
    Objects/codeobject.c \
    Objects/complexobject.c \
    Objects/descrobject.c \
    Objects/enumobject.c \
    Objects/exceptions.c \
    Objects/genobject.c \
    Objects/fileobject.c \
    Objects/floatobject.c \
    Objects/frameobject.c \
    Objects/funcobject.c \
    Objects/iterobject.c \
    Objects/listobject.c \
    Objects/longobject.c \
    Objects/dictobject.c \
    Objects/memoryobject.c \
    Objects/methodobject.c \
    Objects/moduleobject.c \
    Objects/namespaceobject.c \
    Objects/object.c \
    Objects/obmalloc.c \
    Objects/capsule.c \
    Objects/rangeobject.c \
    Objects/setobject.c \
    Objects/sliceobject.c \
    Objects/structseq.c \
    Objects/tupleobject.c \
    Objects/typeobject.c \
    Objects/unicodeobject.c \
    Objects/unicodectype.c \
    Objects/weakrefobject.c

PYTHON_SOURCES = \
    Python/_warnings.c \
    Python/Python-ast.c \
    Python/asdl.c \
    Python/ast.c \
    Python/bltinmodule.c \
    Python/ceval.c \
    Python/compile.c \
    Python/codecs.c \
    Python/errors.c \
    Python/frozenmain.c \
    Python/future.c \
    Python/getargs.c \
    Python/getcompiler.c \
    Python/getcopyright.c \
    Python/getplatform.c \
    Python/getversion.c \
    Python/graminit.c \
    Python/import.c \
    Python/marshal.c \
    Python/modsupport.c \
    Python/mystrtoul.c \
    Python/mysnprintf.c \
    Python/peephole.c \
    Python/pyarena.c \
    Python/pyctype.c \
    Python/pyfpe.c \
    Python/pyhash.c \
    Python/pymath.c \
    Python/pystate.c \
    Python/pythonrun.c \
    Python/pytime.c \
    Python/random.c \
    Python/structmember.c \
    Python/symtable.c \
    Python/sysmodule.c \
    Python/traceback.c \
    Python/getopt.c \
    Python/pystrcmp.c \
    Python/pystrtod.c \
    Python/dtoa.c \
    Python/formatter_unicode.c \
    Python/fileutils.c

win32 {
    PYTHON_SOURCES += Python/thread_nt.c
} else {
    PYTHON_SOURCES += Python/thread.c
}

MODULE_SOURCES = \
    Modules/config.c \
    Modules/getpath.c \
    Modules/main.c \
    Modules/gcmodule.c

MOD_SOURCES = \
    Modules/_threadmodule.c \
    Modules/signalmodule.c \
    Modules/posixmodule.c \
    Modules/errnomodule.c \
    Modules/pwdmodule.c \
    Modules/_sre.c \
    Modules/_codecsmodule.c \
    Modules/_weakref.c \
    Modules/_functoolsmodule.c \
    Modules/_operator.c \
    Modules/_collectionsmodule.c \
    Modules/itertoolsmodule.c \
    Modules/atexitmodule.c \
    Modules/_stat.c \
    Modules/_localemodule.c \
    Modules/_io/_iomodule.c \
    Modules/_io/iobase.c \
    Modules/_io/fileio.c \
    Modules/_io/bytesio.c \
    Modules/_io/bufferedio.c \
    Modules/_io/textio.c \
    Modules/_io/stringio.c \
    Modules/zipimport.c \
    Modules/faulthandler.c \
    Modules/_tracemalloc.c \
    Modules/hashtable.c \
    Modules/symtablemodule.c \
    Modules/xxsubtype.c

SOURCES = Modules/getbuildinfo.c Python/frozen.c
SOURCES += $$PARSER_SOURCES
SOURCES += $$OBJECT_SOURCES
SOURCES += $$PYTHON_SOURCES
SOURCES += $$MODULE_SOURCES
SOURCES += $$MOD_SOURCES
