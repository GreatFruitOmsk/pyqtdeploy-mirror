/*
 * Copyright (c) 2018, Riverbank Computing Limited
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * 
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 * 
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */


#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif


/*
 * Declare the module initialisation functions for all core extension modules
 * (see python_metadata.py).
 */

/* The public modules. */

extern PyObject *PyInit__thread(void);
#if PY_MINOR_VERSION >= 4
extern PyObject *PyInit_atexit(void);
#endif
extern PyObject *PyInit_errno(void);
extern PyObject *PyInit_faulthandler(void);
extern PyObject *PyInit_gc(void);
extern PyObject *PyInit_itertools(void);
extern PyObject *PyMarshal_Init(void);
#if PY_MINOR_VERSION >= 5
extern PyObject *PyInit_mmap(void);
#endif
#if PY_MINOR_VERSION >= 5 && defined(MS_WINDOWS)
extern PyObject *PyInit_msvcrt(void);
#endif
#if PY_MINOR_VERSION == 3
extern PyObject *PyInit_operator(void);
#endif
#if !defined(MS_WINDOWS)
extern PyObject *PyInit_posix(void);
#endif
#if !defined(MS_WINDOWS)
extern PyObject *PyInit_pwd(void);
#endif
#if PY_MINOR_VERSION <= 4
extern PyObject* PyInit_signal(void);
#endif
#if PY_MINOR_VERSION >= 5
extern PyObject *PyInit_time(void);
#endif
#if defined(MS_WINDOWS)
extern PyObject *PyInit_winreg(void);
#endif
#if PY_MINOR_VERSION >= 7
extern PyObject *PyInit_zipimport(void);
#endif

/* The internal modules. */

extern PyObject *PyInit__ast(void);
extern PyObject *PyInit__codecs(void);
extern PyObject *PyInit__collections(void);
extern PyObject *PyInit__functools(void);
#if PY_MINOR_VERSION >= 7
extern PyObject *PyInit__imp(void);
#else
extern PyObject *PyInit_imp(void);
#endif
#if PY_MINOR_VERSION >= 3
extern PyObject *PyInit__io(void);
#endif
extern PyObject *PyInit__locale(void);
#if defined(MS_WINDOWS)
extern PyObject *PyInit_nt(void);
#endif
#if PY_MINOR_VERSION >= 4
extern PyObject *PyInit__operator(void);
#endif
#if PY_MINOR_VERSION >= 5
extern PyObject *PyInit__signal(void);
#endif
extern PyObject *PyInit__sre(void);
#if PY_MINOR_VERSION >= 4
extern PyObject *PyInit__stat(void);
#endif
extern PyObject *PyInit__string(void);
extern PyObject *PyInit__symtable(void);
#if PY_MINOR_VERSION >= 4
extern PyObject *PyInit__tracemalloc(void);
#endif
extern PyObject *_PyWarnings_Init(void);
extern PyObject *PyInit__weakref(void);


/* The corresponding module import table. */

struct _inittab _PyImport_Inittab[] = {
    /* The public modules. */

    {"_thread", PyInit__thread},
#if PY_MINOR_VERSION >= 4
    {"atexit", PyInit_atexit},
#endif
    {"errno", PyInit_errno},
    {"faulthandler", PyInit_faulthandler},
    {"gc", PyInit_gc},
    {"itertools", PyInit_itertools},
    {"marshal", PyMarshal_Init},
#if PY_MINOR_VERSION >= 5
    {"mmap", PyInit_mmap},
#endif
#if PY_MINOR_VERSION >= 5 && defined(MS_WINDOWS)
    {"msvcrt", PyInit_msvcrt},
#endif
#if PY_MINOR_VERSION == 3
    {"operator", PyInit_operator},
#endif
#if !defined(MS_WINDOWS)
    {"posix", PyInit_posix},
#endif
#if !defined(MS_WINDOWS)
    {"pwd", PyInit_pwd},
#endif
#if PY_MINOR_VERSION <= 4
    {"signal", PyInit_signal},
#endif
#if PY_MINOR_VERSION >= 5
    {"time", PyInit_time},
#endif
#if defined(MS_WINDOWS)
    {"winreg", PyInit_winreg},
#endif
#if PY_MINOR_VERSION >= 7
    {"zipimport", PyInit_zipimport},
#endif

    /* The internal modules. */

    {"_ast", PyInit__ast},
    {"_codecs", PyInit__codecs},
    {"_collections", PyInit__collections},
    {"_functools", PyInit__functools},
#if PY_MINOR_VERSION >= 7
    {"_imp", PyInit__imp},
#else
    {"_imp", PyInit_imp},
#endif
#if PY_MINOR_VERSION >= 3
    {"_io", PyInit__io},
#endif
    {"_locale", PyInit__locale},
#if defined(MS_WINDOWS)
    {"nt", PyInit_nt},
#endif
#if PY_MINOR_VERSION >= 4
    {"_operator", PyInit__operator},
#endif
#if PY_MINOR_VERSION >= 5
    {"_signal", PyInit__signal},
#endif
    {"_sre", PyInit__sre},
#if PY_MINOR_VERSION >= 4
    {"_stat", PyInit__stat},
#endif
    {"_string", PyInit__string},
    {"_symtable", PyInit__symtable},
#if PY_MINOR_VERSION >= 4
    {"_tracemalloc", PyInit__tracemalloc},
#endif
    {"_warnings", _PyWarnings_Init},
    {"_weakref", PyInit__weakref},

    /* These entries are here for sys.builtin_module_names. */
    {"builtins", NULL},
    {"sys", NULL},

    /* Sentinel. */
    {0, 0}
};


#ifdef __cplusplus
}
#endif
