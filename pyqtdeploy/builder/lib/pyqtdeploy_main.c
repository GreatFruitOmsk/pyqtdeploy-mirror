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


// Forward declarations.
extern PyObject *PyInit_mfsimport(void);


int pyqtdeploy_main(int argc, char **argv, wchar_t *py_main,
        struct _inittab *extension_modules)
{
    const struct _frozen *fm;
    wchar_t **w_argv;
    int i;
    char *saved_locale;

    // The replacement table of frozen modules with a reserved place for
    // _frozen_importlib.
    static struct _frozen modules[] = {
        {"__bootstrap__", frozen___bootstrap__, sizeof (frozen___bootstrap__)},
        {"__main__", frozen___main__, sizeof (frozen___main__)},
        {NULL, NULL, 0},
        {NULL, NULL, 0}
    };

    // Plugin _frozen_importlib.

    for (fm = PyImport_FrozenModules; fm->name != NULL; ++fm)
    {
        if (strcmp(fm->name, "_frozen_importlib") == 0)
        {
            modules[2] = *fm;
            break;
        }
    }

    PyImport_FrozenModules = modules;

    // Add the importer to the table of builtins.
    if (PyImport_AppendInittab("mfsimport", PyInit_mfsimport) < 0)
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

    // Initialise the interpreter.
    Py_SetProgramName(w_argv[0]);
    Py_Initialize();
    PySys_SetArgv(argc, w_argv);

    // Initialise the path hooks.
    if (PyImport_ImportFrozenModule("__bootstrap__") < 0)
    {
        PyErr_Print();
        return 1;
    }

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
