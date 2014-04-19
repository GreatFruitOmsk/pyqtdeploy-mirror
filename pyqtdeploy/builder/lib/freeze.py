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


import marshal
import optparse
import os
import sys


def freeze_as_data(py_filename, data_filename):
    """ Freeze a Python source file and save it as data. """

    code = _get_marshalled_code(py_filename)

    data_file = open(data_filename, 'wb')
    data_file.write(code)
    data_file.close()


def freeze_as_c(py_filename, c_filename, name):
    """ Freeze a Python source file and save it as C source code. """

    code = _get_marshalled_code(py_filename)

    if not name:
        name, _ = os.path.splitext(os.path.basename(py_filename))

    c_file = open(c_filename, 'wt')

    c_file.write(
            'static unsigned char frozen_%s[] = {' % name)

    as_int = ord if sys.hexversion < 0x03000000 else lambda v: v

    for i in range(0, len(code), 16):
        c_file.write('\n    ')
        for j in code[i:i + 16]:
            c_file.write('%d,' % as_int(j))

    c_file.write('\n};\n')

    c_file.close()


def _get_marshalled_code(py_filename):
    """ Convert a Python source file to a marshalled code object. """

    source_file = open(py_filename)
    source = source_file.read()
    source_file.close()

    co = compile(source, os.path.basename(py_filename), 'exec')

    return marshal.dumps(co)


# Parse the command line.
parser = optparse.OptionParser(usage="Usage: %prog [options] PYFILE")

parser.add_option('--as-c', help="freeze the Python source as C code in FILE",
        metavar="FILE")
parser.add_option('--as-data', help="freeze the Python source as data in FILE",
        metavar="FILE")
parser.add_option('--name', help="name the C structure frozen_NAME",
        metavar="NAME")

(options, args) = parser.parse_args()

if len(args) != 1:
    parser.print_help()
    sys.exit(1)

py_file = args[0]

# Handle the specific actions.
if options.as_c is not None:
    freeze_as_c(py_file, options.as_c, options.name)

if options.as_data is not None:
    freeze_as_data(py_file, options.as_data)
