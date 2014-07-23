// Copyright (c) 2014, Riverbank Computing Limited
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


#include <stdio.h>

#include <Python.h>

#include <QByteArray>
#include <QDir>
#include <QString>
#include <QRegExp>
#include <QTextCodec>

#include "frozen_bootstrap.h"
#include "frozen_main.h"


#if PY_MAJOR_VERSION >= 3
#define BOOTSTRAP_MODULE    "_frozen_importlib"
#define PYQTDEPLOY_INIT     PyInit_pyqtdeploy
extern "C" PyObject *PyInit_pyqtdeploy(void);
#else
#define BOOTSTRAP_MODULE    "__bootstrap__"
#define PYQTDEPLOY_INIT     initpyqtdeploy
extern "C" void initpyqtdeploy(void);
#endif


// We use Qt as the source of the locale information, partly because it
// officially supports Android.
static QTextCodec *locale_codec;


// Foward declarations.
static int append_ascii_strings(PyObject *list, const char **ascii_strings);
static int append_path_dirs(PyObject *list, const char **path_dirs,
        const QDir &exec_dir);
#if PY_MAJOR_VERSION < 3
static PyObject *string_from_qstring(const QString &qs);
#endif


extern "C" int pyqtdeploy_start(int argc, char **argv,
        const char *py_main_filename, struct _inittab *extension_modules,
        const char **path_dirs)
{
    // The replacement table of frozen modules.
    static struct _frozen modules[] = {
        {BOOTSTRAP_MODULE, frozen_pyqtdeploy_bootstrap, sizeof (frozen_pyqtdeploy_bootstrap)},
        {"__main__", frozen_pyqtdeploy_main, sizeof (frozen_pyqtdeploy_main)},
        {NULL, NULL, 0}
    };

    // The minimal (ASCII) sys.path.
    static const char *minimal_path[] = {
        ":/",
        ":/stdlib",
        ":/site-packages",
        NULL
    };

    // Get the codec for the locale.
    locale_codec = QTextCodec::codecForLocale();

    if (!locale_codec)
    {
        fprintf(stderr, "%s: no locale codec found\n", argv[0]);
        return 1;
    }

    // Initialise some Python globals.
    Py_FrozenFlag = 1;
    Py_NoSiteFlag = 1;

#if PY_MAJOR_VERSION >= 3
    QByteArray locale_codec_name = locale_codec->name();
    Py_FileSystemDefaultEncoding = locale_codec_name.data();
#endif

    PyImport_FrozenModules = modules;

    // Add the importer to the table of builtins.
    if (PyImport_AppendInittab("pyqtdeploy", PYQTDEPLOY_INIT) < 0)
    {
        fprintf(stderr, "%s: PyImport_AppendInittab() failed\n", argv[0]);
        return 1;
    }

    // Add any extension modules.
    if (extension_modules != NULL)
        if (PyImport_ExtendInittab(extension_modules) < 0)
        {
            fprintf(stderr, "%s: PyImport_ExtendInittab() failed\n", argv[0]);
            return 1;
        }

#if PY_MAJOR_VERSION >= 3
    // Convert the argument list to wide characters using the locale codec.
    wchar_t *w_argv[argc + 1];

    for (int i = 0; i < argc; i++)
    {
        QString qs_arg = locale_codec->toUnicode(argv[i]);

        wchar_t *w_arg = new wchar_t[qs_arg.length() + 1];

        w_arg[qs_arg.toWCharArray(w_arg)] = 0;

        w_argv[i] = w_arg;
    }

    w_argv[argc] = NULL;

    // Initialise the Python v3 interpreter.
    Py_SetProgramName(w_argv[0]);
    Py_Initialize();
    PySys_SetArgv(argc, w_argv);
#else
    // Initialise the Python v2 interpreter.
    Py_SetProgramName(argv[0]);
    Py_Initialize();
    PySys_SetArgv(argc, argv);

    // Initialise the path hooks.
    if (PyImport_ImportFrozenModule(BOOTSTRAP_MODULE) < 0)
        goto py_error;
#endif

    // Configure sys.path.
    PyObject *py_path;

    if ((py_path = PyList_New(0)) == NULL)
        goto py_error;

    if (append_ascii_strings(py_path, minimal_path) < 0)
        goto py_error;

    if (path_dirs != NULL)
    {
        // Get the directory containing the executable.
        QDir exec_dir(locale_codec->toUnicode(argv[0]));
        exec_dir.makeAbsolute();
        exec_dir.cdUp();

        if (append_path_dirs(py_path, path_dirs, exec_dir) < 0)
            goto py_error;
    }

    if (PySys_SetObject("path", py_path) < 0)
        goto py_error;

    // Set the __file__ attribute of the main module.
    PyObject *mod, *mod_dict, *py_filename;

    if ((mod = PyImport_AddModule("__main__")) == NULL)
        goto py_error;

    mod_dict = PyModule_GetDict(mod);

#if PY_MAJOR_VERSION >= 3
    py_filename = PyUnicode_FromString(py_main_filename);
#else
    py_filename = string_from_qstring(QString::fromUtf8(py_main_filename));
#endif

    if (py_filename == NULL)
        goto py_error;

    if (PyDict_SetItemString(mod_dict, "__file__", py_filename) < 0)
        goto py_error;

    Py_DECREF(py_filename);

    // Import the main module, ie. execute the application.
    if (PyImport_ImportFrozenModule("__main__") < 0)
        goto py_error;

    // Tidy up.
    Py_Finalize();

    return 0;

py_error:
    fprintf(stderr, "%s: a Python exception occurred:\n", argv[0]);
    PyErr_Print();
    return 1;
}


// Extend a list with an array of ASCII encoded strings.  Return -1 if there
// was an error.
static int append_ascii_strings(PyObject *list, const char **ascii_strings)
{
    const char *ascii;

    while ((ascii = *ascii_strings++) != NULL)
    {
        // Convert to a Python string.
        PyObject *py_str;

#if PY_MAJOR_VERSION >= 3
        py_str = PyUnicode_FromString(ascii);
#else
        py_str = PyString_FromString(ascii);
#endif

        if (!py_str)
            return -1;

        // Append to the list.
        int rc = PyList_Append(list, py_str);
        Py_DECREF(py_str);

        if (rc < 0)
            return -1;
    }

    return 0;
}


// Extend a list with an array of UTF-8 encoded path directory names.  Return
// -1 if there was an error.
static int append_path_dirs(PyObject *list, const char **path_dirs,
        const QDir &exec_dir)
{
    const char *path_dir_utf8;

    while ((path_dir_utf8 = *path_dirs++) != NULL)
    {
        // Convert to a QString.
        QString path_dir(QString::fromUtf8(path_dir_utf8));

        // Expand any (locale encoded) environment variables.
        QRegExp env_var_name_re("\\$([A-Za-z0-9_]+)");

        int i;

        while ((i = env_var_name_re.indexIn(path_dir)) != -1)
        {
            QByteArray name(locale_codec->fromUnicode(env_var_name_re.cap(1)));
            QByteArray value(qgetenv(name.data()));

            path_dir.replace(i, env_var_name_re.matchedLength(),
                    locale_codec->toUnicode(value));
        }

        // Make sure the path is absolute.
        if (QDir::isRelativePath(path_dir))
            path_dir = exec_dir.filePath(path_dir);

        // Convert to the native format.  (Note that we don't resolve symbolic
        // links.
        path_dir = QDir::toNativeSeparators(QDir::cleanPath(path_dir));

        // Convert to a Python string.
        PyObject *py_path_dir;

#if PY_MAJOR_VERSION >= 3
        QByteArray utf8(path_dir.toUtf8());
        py_path_dir = PyUnicode_FromStringAndSize(utf8.data(), utf8.length());
#else
        py_path_dir = string_from_qstring(path_dir);
#endif

        if (!py_path_dir)
            return -1;

        // Append to the list.
        int rc = PyList_Append(list, py_path_dir);
        Py_DECREF(py_path_dir);

        if (rc < 0)
            return -1;
    }

    return 0;
}


#if PY_MAJOR_VERSION < 3
// Convert a QString to a Python v2 locale encoded str object.
static PyObject *string_from_qstring(const QString &qs)
{
    QByteArray locale_s(locale_codec->fromUnicode(qs));

    return PyString_FromStringAndSize(locale_s, locale_s.length());
}
#endif
