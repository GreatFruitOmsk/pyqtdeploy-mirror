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

extern void initerrno(void);
extern void initgc(void);
extern void initimp(void);
extern void PyMarshal_Init(void);
#if !defined(MS_WINDOWS)
extern void initposix(void);
#endif
#if !defined(MS_WINDOWS)
extern void initpwd(void);
#endif
extern void initsignal(void);
extern void initthread(void);

/* The internal modules. */

extern void init_ast(void);
extern void init_codecs(void);
#if defined(MS_WINDOWS)
extern void initnt(void);
#endif
extern void init_sre(void);
extern void init_symtable(void);
extern void _PyWarnings_Init(void);
extern void init_weakref(void);


/* The corresponding module import table. */

struct _inittab _PyImport_Inittab[] = {
    /* The public modules. */

    {"errno", initerrno},
    {"exceptions", NULL},
    {"gc", initgc},
    {"imp", initimp},
    {"marshal", PyMarshal_Init},
#if !defined(MS_WINDOWS)
    {"posix", initposix},
#endif
#if !defined(MS_WINDOWS)
    {"pwd", initpwd},
#endif
    {"signal", initsignal},
    {"thread", initthread},

    /* The internal modules. */

    {"_ast", init_ast},
    {"_codecs", init_codecs},
#if defined(MS_WINDOWS)
    {"nt", initnt},
#endif
    {"_sre", init_sre},
    {"_symtable", init_symtable},
    {"_warnings", _PyWarnings_Init},
    {"_weakref", init_weakref},

    {"__main__", NULL},
    {"__builtin__", NULL},
    {"sys", NULL},

    /* Sentinel. */
    {0, 0}
};


#ifdef __cplusplus
}
#endif
