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


#include <locale.h>
#include <stdio.h>
#include <string.h>

#include <Python.h>

#include "frozen_bootstrap.h"
#include "frozen_main.h"


#if PY_MAJOR_VERSION >= 3
#define BOOTSTRAP_MODULE    "_frozen_importlib"
#define PYQTDEPLOY_INIT     PyInit_pyqtdeploy
#define PYMAIN_TYPE         wchar_t
extern PyObject *PyInit_pyqtdeploy(void);
#else
#define BOOTSTRAP_MODULE    "__bootstrap__"
#define PYQTDEPLOY_INIT     initpyqtdeploy
#define PYMAIN_TYPE         char
extern void initpyqtdeploy(void);
#endif


int pyqtdeploy_start(int argc, char **argv, PYMAIN_TYPE *py_main,
        struct _inittab *extension_modules)
{
    // The replacement table of frozen modules.
    static struct _frozen modules[] = {
        {BOOTSTRAP_MODULE, frozen_pyqtdeploy_bootstrap, sizeof (frozen_pyqtdeploy_bootstrap)},
        {"__main__", frozen_pyqtdeploy_main, sizeof (frozen_pyqtdeploy_main)},
        {NULL, NULL, 0}
    };

#if PY_MAJOR_VERSION >= 3
    wchar_t **w_argv;
    int i;
    char *saved_locale;
#endif

    Py_FrozenFlag = 1;
    Py_NoSiteFlag = 1;

    PyImport_FrozenModules = modules;

    // Add the importer to the table of builtins.
    if (PyImport_AppendInittab("pyqtdeploy", PYQTDEPLOY_INIT) < 0)
    {
        fprintf(stderr, "PyImport_AppendInittab() failed\n");
        return 1;
    }

    // Add any extension modules.
    if (extension_modules != NULL)
        if (PyImport_ExtendInittab(extension_modules) < 0)
        {
            fprintf(stderr, "PyImport_ExtendInittab() failed\n");
            return 1;
        }

#if PY_MAJOR_VERSION >= 3
    // Convert the argument list to wide characters.
    if ((w_argv = PyMem_Malloc(sizeof (wchar_t *) * argc)) == NULL)
    {
        fprintf(stderr, "PyMem_Malloc() failed\n");
        return 1;
    }

    w_argv[0] = py_main;

    saved_locale = setlocale(LC_ALL, NULL);
    setlocale(LC_ALL, "");

    for (i = 1; i < argc; i++)
    {
#ifdef HAVE_BROKEN_MBSTOWCS
        size_t len = strlen(argv[i]);
#else
        size_t len = mbstowcs(NULL, argv[i], 0);
#endif

        if (len == (size_t)-1)
        {
            fprintf(stderr, "Could not convert argument %d to string\n", i);
            return 1;
        }

        if ((w_argv[i] = PyMem_Malloc((len + 1) * sizeof (wchar_t))) == NULL)
        {
            fprintf(stderr, "PyMem_Malloc() failed\n");
            return 1;
        }

        if (mbstowcs(w_argv[i], argv[i], len + 1) == (size_t)-1)
        {
            fprintf(stderr, "Could not convert argument %d to string\n", i);
            return 1;
        }
    }

    setlocale(LC_ALL, saved_locale);

    // Initialise the Python v3 interpreter.
    Py_SetProgramName(w_argv[0]);
    Py_Initialize();
    PySys_SetArgv(argc, w_argv);
#else
    argv[0] = py_main;

    // Initialise the Python v2 interpreter.
    Py_SetProgramName(argv[0]);
    Py_Initialize();
    PySys_SetArgv(argc, argv);

    // Initialise the path hooks.
    if (PyImport_ImportFrozenModule(BOOTSTRAP_MODULE) < 0)
    {
        PyErr_Print();
        return 1;
    }
#endif

    // Import the main module, ie. execute the application.
    if (PyImport_ImportFrozenModule("__main__") < 0)
    {
        PyErr_Print();
        return 1;
    }

    // Tidy up.
    Py_Finalize();

    return 0;
}
