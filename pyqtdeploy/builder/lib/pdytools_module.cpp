// Copyright (c) 2018, Riverbank Computing Limited
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
//    this list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.


#include <Python.h>
#include <marshal.h>
#include <structmember.h>

#include <QByteArray>
#include <QChar>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QString>
#include <QStringList>
#include <QVector>

#include "pyqtdeploy_version.h"


#if QT_VERSION < 0x040200
#error "Qt v4.2.0 or later is required"
#endif


extern "C" {

#if PY_MAJOR_VERSION >= 3
#if PY_MINOR_VERSION < 3
#error "Python v3.3 or later is required"
#endif

#define PYQTDEPLOY_INIT                 PyInit_pdytools
#define PYQTDEPLOY_TYPE                 PyObject *
#define PYQTDEPLOY_MODULE_DISCARD(m)    Py_DECREF(m)
#define PYQTDEPLOY_FATAL(s)             return NULL
#define PYQTDEPLOY_RETURN(m)            return (m)
#define PYQTDEPLOY_PARSE_STR            "U"
#define CONST_CAST(s)                   s

// The module definition structure.
static struct PyModuleDef pdytoolsmodule = {
    PyModuleDef_HEAD_INIT,
    "pdytools",
    NULL,
    -1,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL
};
#else
#if PY_MINOR_VERSION < 7
#error "Python v2.7 or later is required"
#endif

#define PYQTDEPLOY_INIT                 initpdytools
#define PYQTDEPLOY_TYPE                 void
#define PYQTDEPLOY_MODULE_DISCARD(m)
#define PYQTDEPLOY_FATAL(s)             Py_FatalError(s)
#define PYQTDEPLOY_RETURN(m)
#define PYQTDEPLOY_PARSE_STR            "S"
#define CONST_CAST(s)                   const_cast<char *>(s)
#endif


#if defined(Q_OS_WIN)
static const char extension_module_extension[] = ".pyd";
#else
static const char extension_module_extension[] = ".so";
#endif


// C linkage forward declarations.
PYQTDEPLOY_TYPE PYQTDEPLOY_INIT();

static int qrcimporter_init(PyObject *self, PyObject *args, PyObject *kwds);
static void qrcimporter_dealloc(PyObject *self);
#if PY_MAJOR_VERSION >= 3
static PyObject *qrcimporter_find_loader(PyObject *self, PyObject *args);
#endif
static PyObject *qrcimporter_find_module(PyObject *self, PyObject *args);
static PyObject *qrcimporter_get_code(PyObject *self, PyObject *args);
static PyObject *qrcimporter_get_data(PyObject *self, PyObject *args);
#if PY_VERSION_HEX >= 0x03070000
static PyObject *qrcimporter_get_resource_reader(PyObject *self,
        PyObject *arg);
#endif
static PyObject *qrcimporter_get_source(PyObject *self, PyObject *args);
static PyObject *qrcimporter_is_package(PyObject *self, PyObject *args);
static PyObject *qrcimporter_load_module(PyObject *self, PyObject *args);


// The importer object structure.
typedef struct _qrcimporter
{
    PyObject_HEAD

    // The path that the importer handles.  It will be the name of a directory.
    QString *path;

    // The component parts of the path.
    QStringList *path_parts;
} QrcImporter;


// The importer method table.
static PyMethodDef qrcimporter_methods[] = {
#if PY_MAJOR_VERSION >= 3
    {"find_loader", qrcimporter_find_loader, METH_VARARGS, NULL},
#endif
    {"find_module", qrcimporter_find_module, METH_VARARGS, NULL},
    {"get_code", qrcimporter_get_code, METH_VARARGS, NULL},
    {"get_data", qrcimporter_get_data, METH_VARARGS, NULL},
#if PY_VERSION_HEX >= 0x03070000
    {"get_resource_reader", qrcimporter_get_resource_reader, METH_O, NULL},
#endif
    {"get_source", qrcimporter_get_source, METH_VARARGS, NULL},
    {"is_package", qrcimporter_is_package, METH_VARARGS, NULL},
    {"load_module", qrcimporter_load_module, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};


// The importer type structure.
static PyTypeObject QrcImporter_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "pdytools.qrcimporter",
    sizeof (QrcImporter),
    0,                                          // tp_itemsize
    qrcimporter_dealloc,                        // tp_dealloc
    0,                                          // tp_print
    0,                                          // tp_getattr
    0,                                          // tp_setattr
    0,                                          // tp_reserved
    0,                                          // tp_repr
    0,                                          // tp_as_number
    0,                                          // tp_as_sequence
    0,                                          // tp_as_mapping
    0,                                          // tp_hash
    0,                                          // tp_call
    0,                                          // tp_str
    0,                                          // tp_getattro
    0,                                          // tp_setattro
    0,                                          // tp_as_buffer
    Py_TPFLAGS_DEFAULT,                         // tp_flags
    0,                                          // tp_doc
    0,                                          // tp_traverse
    0,                                          // tp_clear
    0,                                          // tp_richcompare
    0,                                          // tp_weaklistoffset
    0,                                          // tp_iter
    0,                                          // tp_iternext
    qrcimporter_methods,                        // tp_methods
    0,                                          // tp_members
    0,                                          // tp_getset
    0,                                          // tp_base
    0,                                          // tp_dict
    0,                                          // tp_descr_get
    0,                                          // tp_descr_set
    0,                                          // tp_dictoffset
    qrcimporter_init,                           // tp_init
    0,                                          // tp_alloc
    0,                                          // tp_new
    0,                                          // tp_free
    0,                                          // tp_is_gc
    0,                                          // tp_bases
    0,                                          // tp_mro
    0,                                          // tp_cache
    0,                                          // tp_subclasses
    0,                                          // tp_weaklist
    0,                                          // tp_del
    0,                                          // tp_version_tag
#if PY_VERSION_HEX >= 0x03040000
    0,                                          // tp_finalize
#endif
};


#if PY_VERSION_HEX >= 0x03070000
// The reader object structure.
typedef struct _qrcreader
{
    PyObject_HEAD

    // The pathname containing the resources handled by this reader.
    QString *pathname;
} QrcReader;


// The reader method declarations.
static int qrcreader_init(PyObject *self, PyObject *args, PyObject *kwds);
static void qrcreader_dealloc(PyObject *self);
static PyObject *qrcreader_contents(PyObject *self, PyObject *);
static PyObject *qrcreader_is_resource(PyObject *self, PyObject *args);
static PyObject *qrcreader_open_resource(PyObject *self, PyObject *arg);
static PyObject *qrcreader_resource_path(PyObject *self, PyObject *arg);


// The reader method table.
static PyMethodDef qrcreader_methods[] = {
    {"contents", qrcreader_contents, METH_NOARGS, NULL},
    {"is_resource", qrcreader_is_resource, METH_VARARGS, NULL},
    {"open_resource", qrcreader_open_resource, METH_O, NULL},
    {"resource_path", qrcreader_resource_path, METH_O, NULL},
    {NULL, NULL, 0, NULL}
};


// The reader type structure.
static PyTypeObject QrcReader_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "pdytools.qrcreader",
    sizeof (QrcReader),
    0,                                          // tp_itemsize
    qrcreader_dealloc,                          // tp_dealloc
    0,                                          // tp_print
    0,                                          // tp_getattr
    0,                                          // tp_setattr
    0,                                          // tp_reserved
    0,                                          // tp_repr
    0,                                          // tp_as_number
    0,                                          // tp_as_sequence
    0,                                          // tp_as_mapping
    0,                                          // tp_hash
    0,                                          // tp_call
    0,                                          // tp_str
    0,                                          // tp_getattro
    0,                                          // tp_setattro
    0,                                          // tp_as_buffer
    Py_TPFLAGS_DEFAULT,                         // tp_flags
    0,                                          // tp_doc
    0,                                          // tp_traverse
    0,                                          // tp_clear
    0,                                          // tp_richcompare
    0,                                          // tp_weaklistoffset
    0,                                          // tp_iter
    0,                                          // tp_iternext
    qrcreader_methods,                          // tp_methods
    0,                                          // tp_members
    0,                                          // tp_getset
    0,                                          // tp_base
    0,                                          // tp_dict
    0,                                          // tp_descr_get
    0,                                          // tp_descr_set
    0,                                          // tp_dictoffset
    qrcreader_init,                             // tp_init
    0,                                          // tp_alloc
    0,                                          // tp_new
    0,                                          // tp_free
    0,                                          // tp_is_gc
    0,                                          // tp_bases
    0,                                          // tp_mro
    0,                                          // tp_cache
    0,                                          // tp_subclasses
    0,                                          // tp_weaklist
    0,                                          // tp_del
    0,                                          // tp_version_tag
    0,                                          // tp_finalize
};


// The resource object structure.
typedef struct _qrcresource
{
    PyObject_HEAD

    // The resource itself.
    QFile *resource;
} QrcResource;


// The resource method declarations.
static int qrcresource_init(PyObject *self, PyObject *args, PyObject *kwds);
static void qrcresource_dealloc(PyObject *self);
static PyObject *qrcresource_close(PyObject *self, PyObject *);
static PyObject *qrcresource_flush(PyObject *self, PyObject *);
static PyObject *qrcresource_read(PyObject *self, PyObject *args);
static PyObject *qrcresource_readable(PyObject *self, PyObject *);
static PyObject *qrcresource_seekable(PyObject *self, PyObject *);
static PyObject *qrcresource_writable(PyObject *self, PyObject *);


// The resource method table.
static PyMethodDef qrcresource_methods[] = {
    {"close", qrcresource_close, METH_NOARGS, NULL},
    {"flush", qrcresource_flush, METH_NOARGS, NULL},
    {"read", qrcresource_read, METH_VARARGS, NULL},
    {"readable", qrcresource_readable, METH_NOARGS, NULL},
    {"seekable", qrcresource_seekable, METH_NOARGS, NULL},
    {"writable", qrcresource_writable, METH_NOARGS, NULL},
    {NULL, NULL, 0, NULL}
};


// The resource get/set declarations.
static PyObject *qrcresource_get_closed(PyObject *self, void *);


// The resource get/set table.
static PyGetSetDef qrcresource_getset[] = {
    {"closed", qrcresource_get_closed, NULL, NULL},
    {NULL, NULL, NULL, NULL}
};


// The resource type structure.
static PyTypeObject QrcResource_Type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "pdytools.qrcresource",
    sizeof (QrcResource),
    0,                                          // tp_itemsize
    qrcresource_dealloc,                        // tp_dealloc
    0,                                          // tp_print
    0,                                          // tp_getattr
    0,                                          // tp_setattr
    0,                                          // tp_reserved
    0,                                          // tp_repr
    0,                                          // tp_as_number
    0,                                          // tp_as_sequence
    0,                                          // tp_as_mapping
    0,                                          // tp_hash
    0,                                          // tp_call
    0,                                          // tp_str
    0,                                          // tp_getattro
    0,                                          // tp_setattro
    0,                                          // tp_as_buffer
    Py_TPFLAGS_DEFAULT,                         // tp_flags
    0,                                          // tp_doc
    0,                                          // tp_traverse
    0,                                          // tp_clear
    0,                                          // tp_richcompare
    0,                                          // tp_weaklistoffset
    0,                                          // tp_iter
    0,                                          // tp_iternext
    qrcresource_methods,                        // tp_methods
    0,                                          // tp_members
    qrcresource_getset,                         // tp_getset
    0,                                          // tp_base
    0,                                          // tp_dict
    0,                                          // tp_descr_get
    0,                                          // tp_descr_set
    0,                                          // tp_dictoffset
    qrcresource_init,                           // tp_init
    0,                                          // tp_alloc
    0,                                          // tp_new
    0,                                          // tp_free
    0,                                          // tp_is_gc
    0,                                          // tp_bases
    0,                                          // tp_mro
    0,                                          // tp_cache
    0,                                          // tp_subclasses
    0,                                          // tp_weaklist
    0,                                          // tp_del
    0,                                          // tp_version_tag
    0,                                          // tp_finalize
};
#endif

}


// The different results that can be returned by find_module().
enum ModuleType {
    ModuleNotFound,
    ModuleIsModule,
    ModuleIsPackage,
    ModuleIsNamespace,
    ModuleIsAdjacentExtensionModule
};


// The internal API.
void pdytools_init_executable_dir(const QString &argv0);
const QDir &pdytools_get_executable_dir();


// Other forward declarations.
static ModuleType find_module(QrcImporter *self, const QString &fqmn,
        QString &pathname, QString &filename);
static bool read_data(const QString &filename, QByteArray &data);
static PyObject *get_code_object(const QString &filename);
static void raise_import_error(const QString &fqmn);
static QString str_to_qstring(PyObject *str);
static PyObject *qstring_to_str(const QString &qstring);
static bool parse_qstring(PyObject *args, const char *fmt, QString &qstring,
        PyObject **str_obj = 0);
#if PY_VERSION_HEX >= 0x03070000
static QString get_resource_path(QrcReader *reader, const QString &resource);
#endif


// The directory containing the application executable.
static QDir *executable_dir = 0;


// The importer initialisation function.
static int qrcimporter_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    // It's not clear if this is part of the public API.
    if (!_PyArg_NoKeywords("qrcimporter()", kwds))
        return -1;

    PyObject *path;

#if PY_MAJOR_VERSION >= 3
    if (!PyArg_ParseTuple(args, "O&:qrcimporter", PyUnicode_FSDecoder, &path))
        return -1;
#else
    if (!PyArg_ParseTuple(args, PYQTDEPLOY_PARSE_STR ":qrcimporter", &path))
        return -1;
#endif

    QString *q_path = new QString(str_to_qstring(path));

    if (!q_path->startsWith(QChar(':')) || !QFileInfo(*q_path).isDir())
    {
        delete q_path;

        PyErr_SetString(PyExc_ImportError, "qrcimporter: not a qrc file");
        return -1;
    }

    if (!q_path->endsWith(QChar('/')))
        q_path->append(QChar('/'));

    ((QrcImporter *)self)->path = q_path;

    ((QrcImporter *)self)->path_parts = new QStringList(
            q_path->mid(2, q_path->length() - 3).split(QChar('/'),
                    QString::SkipEmptyParts));

    return 0;
}


// The importer deallocation function.
static void qrcimporter_dealloc(PyObject *self)
{
    if (((QrcImporter *)self)->path)
    {
        delete ((QrcImporter *)self)->path;
        ((QrcImporter *)self)->path = 0;
    }

    if (((QrcImporter *)self)->path_parts)
    {
        delete ((QrcImporter *)self)->path_parts;
        ((QrcImporter *)self)->path_parts = 0;
    }

    Py_TYPE(self)->tp_free(self);
}


#if PY_MAJOR_VERSION >= 3
// Implement the standard find_loader() method for the importer.
static PyObject *qrcimporter_find_loader(PyObject *self, PyObject *args)
{
    QString fqmn;

    if (!parse_qstring(args, PYQTDEPLOY_PARSE_STR ":qrcimporter.find_loader", fqmn))
        return NULL;

    QString pathname, filename;
    PyObject *result;

    switch (find_module((QrcImporter *)self, fqmn, pathname, filename))
    {
    case ModuleIsModule:
    case ModuleIsPackage:
    case ModuleIsAdjacentExtensionModule:
        result = Py_BuildValue("O[]", self);
        break;

    case ModuleIsNamespace:
        {
            PyObject *py_pathname = qstring_to_str(pathname);
            if (!py_pathname)
                return NULL;

            result = Py_BuildValue("O[N]", Py_None, py_pathname);
            break;
        }

    case ModuleNotFound:
        {
            static bool recursing = false;

            // If we have failed to find a sub-package then it may be because
            // it is a builtin so start a high-level search for it while
            // watching for recursing back here.
            if (fqmn.contains(QChar('.')) && !recursing)
            {
                static PyObject *find_loader = 0;

                if (!find_loader)
                {
                    PyObject *importlib = PyImport_ImportModule("importlib");

                    if (!importlib)
                        return NULL;

                    find_loader = PyObject_GetAttrString(importlib,
                            "find_loader");

                    Py_DECREF(importlib);

                    if (!find_loader)
                        return NULL;
                }

                recursing = true;
                PyObject *loader = PyObject_CallObject(find_loader, args);
                recursing = false;

                if (!loader)
                    return NULL;

                result = Py_BuildValue("N[]", loader);
            }
            else
            {
                result = Py_BuildValue("O[]", Py_None);
            }
        }

        break;
    }

    return result;
}
#endif


// Implement the standard find_module() method for the importer.  Note that we
// implement this for Python v3 as well as v2 to support things (like
// pkg_resources) that are still using the old API.
static PyObject *qrcimporter_find_module(PyObject *self, PyObject *args)
{
    PyObject *py_fqmn, *path;

    if (!PyArg_ParseTuple(args, PYQTDEPLOY_PARSE_STR "|O:qrcimporter.find_module", &py_fqmn, &path))
        return NULL;

    QString fqmn = str_to_qstring(py_fqmn);
    QString pathname, filename;
    PyObject *result;

    if (find_module((QrcImporter *)self, fqmn, pathname, filename) == ModuleNotFound)
    {
        result = Py_None;

        // If we have failed to find a sub-package then it may be because it is
        // a builtin.
        if (fqmn.contains(QChar('.')))
            for (struct _inittab *p = PyImport_Inittab; p->name; ++p)
                if (fqmn == p->name)
                {
                    result = self;
                    break;
                }
    }
    else
    {
        result = self;
    }

    Py_INCREF(result);
    return result;
}


// Implement the standard load_module() method for the importer.
static PyObject *qrcimporter_load_module(PyObject *self, PyObject *args)
{
    QString fqmn;
    PyObject *py_fqmn;

    if (!parse_qstring(args, PYQTDEPLOY_PARSE_STR ":qrcimporter.load_module", fqmn, &py_fqmn))
        return NULL;

    QString pathname, filename;
    PyObject *code, *py_filename, *mod_dict;

    ModuleType mt = find_module((QrcImporter *)self, fqmn, pathname, filename);

#if PY_MAJOR_VERSION < 3
    if (mt == ModuleNotFound)
    {
        // We use the imp module to load sub-packages that are statically
        // linked extension modules.
        static PyObject *init_builtin = 0;

        if (!init_builtin)
        {
            PyObject *imp_module = PyImport_ImportModule("imp");
            if (!imp_module)
                return NULL;

            init_builtin = PyObject_GetAttrString(imp_module, "init_builtin");
            Py_DECREF(imp_module);

            if (!init_builtin)
                return NULL;
        }

        return PyObject_CallObject(init_builtin, args);
    }
#endif

    if (mt == ModuleIsAdjacentExtensionModule)
    {
        // We use the imp module to load sub-packages that are dynamically
        // linked extension modules installed in the same directory as the
        // executable.
        // TODO - Reimplement without using the imp module for Python v3.4 and
        // later.  Change the meta-data for the imp module for Python v3.4 to
        // be PythonModule rather than CorePythonModule.
        static PyObject *load_module = NULL;
        static PyObject *open_file = NULL;

        if (!load_module)
        {
            PyObject *imp_module = PyImport_ImportModule("imp");
            if (!imp_module)
                return NULL;

            load_module = PyObject_GetAttrString(imp_module, "load_module");
            Py_DECREF(imp_module);

            if (!load_module)
                return NULL;
        }

        if (!open_file)
        {
            PyObject *builtins = PyEval_GetBuiltins();
            if (!builtins)
                return NULL;

            open_file = PyDict_GetItemString(builtins, "open");
            if (!open_file)
                return NULL;
        }

        py_filename = qstring_to_str(filename);
        if (!py_filename)
            return NULL;

        PyObject *module_file = PyObject_CallFunction(open_file,
                CONST_CAST("Os"), py_filename, "rb");

        if (!module_file)
        {
            Py_DECREF(py_filename);
            return NULL;
        }

        PyObject *module = PyObject_CallFunction(load_module,
                CONST_CAST("OOO(ssi)"), py_fqmn, module_file, py_filename,
                extension_module_extension, "rb", 3);

        Py_DECREF(module_file);
        Py_DECREF(py_filename);

        return module;
    }

    if (mt != ModuleIsModule && mt != ModuleIsPackage)
    {
        raise_import_error(fqmn);
        return NULL;
    }

    // Read in the code object from the file.
    code = get_code_object(filename);
    if (!code)
        return NULL;

    // Get the module object and its dict.
#if PY_MAJOR_VERSION >= 3
    PyObject *mod = PyImport_AddModuleObject(py_fqmn);
#else
    PyObject *mod = PyImport_AddModule(PyString_AS_STRING(py_fqmn));
#endif
    if (!mod)
        goto error;

    mod_dict = PyModule_GetDict(mod);

    // Set the loader object.
    if (PyDict_SetItemString(mod_dict, "__loader__", self) != 0)
        goto error;

    if (mt == ModuleIsPackage)
    {
        // Add __path__ to the module before the code gets executed.

        PyObject *py_pathname = qstring_to_str(pathname);
        if (!py_pathname)
            goto error;

        PyObject *path_list = Py_BuildValue("[N]", py_pathname);
        if (!path_list)
            goto error;

        int rc = PyDict_SetItemString(mod_dict, "__path__", path_list);
        Py_DECREF(path_list);

        if (rc != 0)
            goto error;
    }

    py_filename = qstring_to_str(filename);
    if (!py_filename)
        goto error;

#if PY_MAJOR_VERSION >= 3
    mod = PyImport_ExecCodeModuleObject(py_fqmn, code, py_filename, NULL);
#else
    mod = PyImport_ExecCodeModuleEx(PyString_AS_STRING(py_fqmn), code,
            PyString_AS_STRING(py_filename));
#endif

    Py_DECREF(py_filename);
    Py_DECREF(code);

    return mod;

error:
    Py_DECREF(code);
    return NULL;
}


// Implement the optional get_code() method for the importer.
static PyObject *qrcimporter_get_code(PyObject *self, PyObject *args)
{
    QString fqmn;

    if (!parse_qstring(args, PYQTDEPLOY_PARSE_STR ":qrcimporter.get_code", fqmn))
        return NULL;

    QString pathname, filename;
    PyObject *result;

    switch (find_module((QrcImporter *)self, fqmn, pathname, filename))
    {
    case ModuleNotFound:
        raise_import_error(fqmn);
        return NULL;

    case ModuleIsModule:
    case ModuleIsPackage:
        result = get_code_object(filename);
        break;

    default:
        result = Py_None;
        Py_INCREF(result);
    }

    return result;
}


#if PY_VERSION_HEX >= 0x03070000
// Implement the optional get_resource_reader() method for the importer.
static PyObject *qrcimporter_get_resource_reader(PyObject *self, PyObject *arg)
{
    return PyObject_CallFunctionObjArgs((PyObject *)&QrcReader_Type, self,
            arg, NULL);
}


// The reader initialisation function.
static int qrcreader_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    // It's not clear if this is part of the public API.
    if (!_PyArg_NoKeywords("qrcreader()", kwds))
        return -1;

    QrcImporter *importer;
    PyObject *py_package;

    if (!PyArg_ParseTuple(args, "O" PYQTDEPLOY_PARSE_STR ":qrcreader", &importer, &py_package))
        return -1;

    QString package = str_to_qstring(py_package);
    QString pathname, filename;

    if (find_module(importer, package, pathname, filename) != ModuleIsPackage)
    {
        PyErr_Format(PyExc_ImportError, "qrcreader: %s is not a package",
                package.toLatin1().constData());

        return -1;
    }

    ((QrcReader *)self)->pathname = new QString(pathname);

    return 0;
}


// The reader deallocation function.
static void qrcreader_dealloc(PyObject *self)
{
    if (((QrcReader *)self)->pathname)
    {
        delete ((QrcReader *)self)->pathname;
        ((QrcReader *)self)->pathname = 0;
    }

    Py_TYPE(self)->tp_free(self);
}


// Implement the contents() method for the reader.
static PyObject *qrcreader_contents(PyObject *self, PyObject *)
{
    QStringList contents(QDir(*((QrcReader *)self)->pathname).entryList());

    PyObject *py_contents = PyTuple_New(contents.size());
    if (!py_contents)
        return NULL;

    for (int i = 0; i < contents.size(); ++i)
    {
        PyObject *py_name = qstring_to_str(contents.at(i));
        if (!py_name)
        {
            Py_DECREF(py_contents);
            return NULL;
        }

        PyTuple_SET_ITEM(py_contents, i, py_name);
    }

    return py_contents;
}


// Implement the is_resource() method for the reader.
static PyObject *qrcreader_is_resource(PyObject *self, PyObject *args)
{
    QString resource;
    PyObject *py_resource;

    if (!parse_qstring(args, PYQTDEPLOY_PARSE_STR ":qrcreader.is_resource", resource, &py_resource))
        return NULL;

    QFileInfo resource_info(get_resource_path((QrcReader *)self, resource));

    if (!resource_info.exists())
    {
        PyErr_Format(PyExc_FileNotFoundError, "%R does not exist",
                py_resource);

        return NULL;
    }

    if (resource_info.isFile())
        Py_RETURN_TRUE;

    Py_RETURN_FALSE;
}


// Implement the open_resource() method for the reader.
static PyObject *qrcreader_open_resource(PyObject *self, PyObject *arg)
{
    // Note that a resource should be able to be specified as a path-like
    // object but (at the moment) we only support strings.
    return PyObject_CallFunctionObjArgs((PyObject *)&QrcResource_Type, self,
            arg, NULL);
}


// Implement the resource_path() method for the reader.
static PyObject *qrcreader_resource_path(PyObject *self, PyObject *arg)
{
    PyErr_Format(PyExc_FileNotFoundError, "%R is not on the file system", arg);

    return NULL;
}


// The resource initialisation function.
static int qrcresource_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    // It's not clear if this is part of the public API.
    if (!_PyArg_NoKeywords("qrcresource()", kwds))
        return -1;

    QrcReader *reader;
    PyObject *py_resource;

    if (!PyArg_ParseTuple(args, "O" PYQTDEPLOY_PARSE_STR ":qrcresource", &reader, &py_resource))
        return -1;

    QFile *resource = new QFile(
            get_resource_path(reader, str_to_qstring(py_resource)));

    if (!resource->open(QIODevice::ReadOnly))
    {
        delete resource;
        return -1;
    }

    ((QrcResource *)self)->resource = resource;

    return 0;
}


// The resource deallocation function.
static void qrcresource_dealloc(PyObject *self)
{
    QFile *resource = ((QrcResource *)self)->resource;

    if (resource)
    {
        if (resource->isOpen())
            resource->close();

        delete resource;
        ((QrcResource *)self)->resource = 0;
    }

    Py_TYPE(self)->tp_free(self);
}


// Implement the close() method for the resource.
static PyObject *qrcresource_close(PyObject *self, PyObject *)
{
    QFile *resource = ((QrcResource *)self)->resource;

    if (resource->isOpen())
        resource->close();

    Py_RETURN_NONE;
}


// Implement the flush() method for the resource.
static PyObject *qrcresource_flush(PyObject *self, PyObject *)
{
    Py_RETURN_NONE;
}


// Implement the read() method for the resource.
static PyObject *qrcresource_read(PyObject *self, PyObject *args)
{
    Py_ssize_t size = -1;

    if (!PyArg_ParseTuple(args, "|n:qrcresource.read", &size))
        return NULL;

    QFile *resource = ((QrcResource *)self)->resource;

    QByteArray data = (size < 0 ? resource->readAll() : resource->read(size));

#if PY_MAJOR_VERSION >= 3
    return PyBytes_FromStringAndSize(data.constData(), data.size());
#else
    return PyString_FromStringAndSize(data.constData(), data.size());
#endif
}


// Implement the readable() method for the resource.
static PyObject *qrcresource_readable(PyObject *self, PyObject *)
{
    Py_RETURN_TRUE;
}


// Implement the seekable() method for the resource.
static PyObject *qrcresource_seekable(PyObject *self, PyObject *)
{
    Py_RETURN_FALSE;
}


// Implement the writable() method for the resource.
static PyObject *qrcresource_writable(PyObject *self, PyObject *)
{
    Py_RETURN_FALSE;
}


// Implement the closed getter for the resource.
static PyObject *qrcresource_get_closed(PyObject *self, void *)
{
    QFile *resource = ((QrcResource *)self)->resource;

    if (resource->isOpen())
        Py_RETURN_FALSE;

    Py_RETURN_TRUE;
}


// Return the full pathname of a resource.
static QString get_resource_path(QrcReader *reader, const QString &resource)
{
    return QString("%1/%2").arg(*reader->pathname).arg(resource);
}
#endif


// Implement the optional get_source() method for the importer.
static PyObject *qrcimporter_get_source(PyObject *self, PyObject *args)
{
    Py_RETURN_NONE;
}


// Implement the optional is_package() method for the importer.
static PyObject *qrcimporter_is_package(PyObject *self, PyObject *args)
{
    QString fqmn;

    if (!parse_qstring(args, PYQTDEPLOY_PARSE_STR ":qrcimporter.is_package", fqmn))
        return NULL;

    QString pathname, filename;
    PyObject *result;

    switch (find_module((QrcImporter *)self, fqmn, pathname, filename))
    {
    case ModuleNotFound:
        raise_import_error(fqmn);
        return NULL;

    case ModuleIsPackage:
        result = Py_True;
        break;

    default:
        result = Py_False;
    }

    Py_INCREF(result);
    return result;
}


// Implement the optional get_data() method for the importer.
static PyObject *qrcimporter_get_data(PyObject *self, PyObject *args)
{
    QString filename;

    if (!parse_qstring(args, PYQTDEPLOY_PARSE_STR ":qrcimporter.get_data", filename))
        return NULL;

    QByteArray data;

    if (!read_data(filename, data))
        return NULL;

#if PY_MAJOR_VERSION >= 3
    return PyBytes_FromStringAndSize(data.constData(), data.size());
#else
    return PyString_FromStringAndSize(data.constData(), data.size());
#endif
}


// Find a fully qualified module name handled by an importer and return its
// type, path name and file name.
static ModuleType find_module(QrcImporter *self, const QString &fqmn,
        QString &pathname, QString &filename)
{
    QStringList fqmn_parts = fqmn.split(QChar('.'));
    QString fqmn_last = fqmn_parts.takeLast();

    // Reject it if the path is clearly wrong.
    if (*self->path_parts != fqmn_parts)
        return ModuleNotFound;

    pathname = *self->path + fqmn_last;

    // See if it is an ordinary module.
    filename = pathname + ".pyo";

    if (QFileInfo(filename).isFile())
        return ModuleIsModule;

    // See if it is a package.
    filename = pathname + "/__init__.pyo";

    if (QFileInfo(filename).isFile())
        return ModuleIsPackage;

    // See if it is an adjacent extension module.  Allow for the fact that we
    // can be called before we have set the executable directory.
    if (executable_dir)
    {
        const QDir &exec_dir = pdytools_get_executable_dir();

        QString em_name(fqmn);
        em_name.append(extension_module_extension);

#if defined(Q_OS_DARWIN)
        // The PlugIns directory is the prefered location for dynamic modules.
        filename = exec_dir.filePath(QString("../PlugIns/%1").arg(em_name));

        if (QFileInfo(filename).isFile())
            return ModuleIsAdjacentExtensionModule;

        filename = exec_dir.filePath(QString("../Frameworks/%1").arg(em_name));

        if (QFileInfo(filename).isFile())
            return ModuleIsAdjacentExtensionModule;
#endif

        filename = exec_dir.filePath(em_name);

        if (QFileInfo(filename).isFile())
            return ModuleIsAdjacentExtensionModule;
    }

    // See if it is a namespace.
    filename = pathname;

    if (QFileInfo(filename).isDir())
        return ModuleIsNamespace;

    // Nothing was found.
    return ModuleNotFound;
}


// Get the data from a file.
static bool read_data(const QString &filename, QByteArray &data)
{
    QFile mfile(filename);

    if (!mfile.open(QIODevice::ReadOnly))
    {
        PyErr_Format(PyExc_ImportError, "qrcimporter: error opening file %s",
                filename.toLatin1().constData());
        return false;
    }

    data = mfile.readAll();

    mfile.close();

    return true;
}


// Get the code object from a file.
static PyObject *get_code_object(const QString &filename)
{
    QByteArray data;

    if (!read_data(filename, data))
        return NULL;

    return PyMarshal_ReadObjectFromString(data.data(), data.size());
}


// Parse an argument tuple for a single QString.
static bool parse_qstring(PyObject *args, const char *fmt, QString &qstring,
        PyObject **str_obj)
{
    PyObject *py_string;

    if (!PyArg_ParseTuple(args, fmt, &py_string))
        return false;

    if (str_obj)
        *str_obj = py_string;

    qstring = str_to_qstring(py_string);

    return true;
}


// Convert a Python str object to a QString.
static QString str_to_qstring(PyObject *str)
{
#if PY_MAJOR_VERSION >= 3
    Py_ssize_t len = PyUnicode_GET_LENGTH(str);

    switch (PyUnicode_KIND(str))
    {
    case PyUnicode_1BYTE_KIND:
        return QString::fromLatin1((char *)PyUnicode_1BYTE_DATA(str), len);

    case PyUnicode_2BYTE_KIND:
        // The (QChar *) cast should be safe.
        return QString((QChar *)PyUnicode_2BYTE_DATA(str), len);

    case PyUnicode_4BYTE_KIND:
        return QString::fromUcs4(PyUnicode_4BYTE_DATA(str), len);
    }

    return QString();
#else
    return QString(QLatin1String(PyString_AS_STRING(str)));
#endif
}


// Convert a QString to a Python str object.
static PyObject *qstring_to_str(const QString &qstring)
{
#if PY_MAJOR_VERSION >= 3
    QVector<uint> ucs4 = qstring.toUcs4();

    return PyUnicode_FromKindAndData(PyUnicode_4BYTE_KIND, ucs4.data(),
            ucs4.size());
#else
    return PyString_FromString(qstring.toLatin1().constData());
#endif
}


// Raise an ImportError when a module could not be found.
static void raise_import_error(const QString &fqmn)
{
    PyErr_Format(PyExc_ImportError, "qrcimporter: can't find module %s",
            fqmn.toLatin1().constData());
}


// Initialise the directory containing the executable.
void pdytools_init_executable_dir(const QString &argv0)
{
    QString name;
    PyObject *executable = PySys_GetObject(CONST_CAST("executable"));

    if (executable && executable != Py_None)
        name = str_to_qstring(executable);
    else
        name = argv0;

    executable_dir = new QDir(name);
    executable_dir->makeAbsolute();
    executable_dir->cdUp();
}


// Return the directory containing the executable.
const QDir &pdytools_get_executable_dir()
{
    return *executable_dir;
}


// The module initialisation function.
PYQTDEPLOY_TYPE PYQTDEPLOY_INIT()
{
    PyObject *mod;

    // Just in case we are linking against Python as a Windows DLL.
    QrcImporter_Type.tp_new = PyType_GenericNew;

    if (PyType_Ready(&QrcImporter_Type) < 0)
        PYQTDEPLOY_FATAL("Failed to initialise pdytools.qrcimporter type");

#if PY_VERSION_HEX >= 0x03070000
    QrcReader_Type.tp_new = PyType_GenericNew;

    if (PyType_Ready(&QrcReader_Type) < 0)
        PYQTDEPLOY_FATAL("Failed to initialise pdytools.qrcreader type");

    QrcResource_Type.tp_new = PyType_GenericNew;

    if (PyType_Ready(&QrcResource_Type) < 0)
        PYQTDEPLOY_FATAL("Failed to initialise pdytools.qrcresource type");
#endif

#if PY_MAJOR_VERSION >= 3
    mod = PyModule_Create(&pdytoolsmodule);
#else
    mod = Py_InitModule("pdytools", NULL);
#endif
    if (mod == NULL)
        PYQTDEPLOY_FATAL("Failed to initialise pdytools module");

    if (PyModule_AddIntConstant(mod, "hexversion", PYQTDEPLOY_HEXVERSION) < 0)
    {
        PYQTDEPLOY_MODULE_DISCARD(mod);
        PYQTDEPLOY_FATAL("Failed to add hexversion to pdytools module");
    }

    Py_INCREF(&QrcImporter_Type);
    if (PyModule_AddObject(mod, "qrcimporter", (PyObject *)&QrcImporter_Type) < 0)
    {
        PYQTDEPLOY_MODULE_DISCARD(mod);
        PYQTDEPLOY_FATAL("Failed to add qrcimporter to pdytools module");
    }

    PYQTDEPLOY_RETURN(mod);
}
