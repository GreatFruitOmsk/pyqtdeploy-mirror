# Copyright (c) 2014 Riverbank Computing Limited.
#
# This file is part of pyqtdeploy.
#
# This file may be used under the terms of the GNU General Public License
# v2 or v3 as published by the Free Software Foundation which can be found in
# the files LICENSE-GPL2.txt and LICENSE-GPL3.txt included in this package.
# In addition, as a special exception, Riverbank gives you certain additional
# rights.  These rights are described in the Riverbank GPL Exception, which
# can be found in the file GPL-Exception.txt in this package.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


import argparse
import marshal
import os


def freeze_as_data(py_filename, data_filename):
    """ Freeze a Python source file and save it as data. """

    code = _get_marshalled_code(py_filename)

    data_file = open(data_filename, 'wb')
    data_file.write(code)
    data_file.close()


def freeze_as_c(py_filename, c_filename, main):
    """ Freeze a Python source file and save it as C source code. """

    code = _get_marshalled_code(py_filename)

    if main:
        name = '__main__'
    else:
        name, _ = os.path.splitext(os.path.basename(py_filename))

    c_file = open(c_filename, 'wt')

    c_file.write(
            'static unsigned char frozen_%s[] = {' % name)

    for i in range(0, len(code), 16):
        c_file.write('\n    ')
        for j in code[i:i + 16]:
            c_file.write('%d,' % j)

    c_file.write('\n};\n')

    c_file.close()


def _get_marshalled_code(py_filename):
    """ Convert a Python source file to a marshalled code object. """

    source_file = open(py_filename)
    source = source_file.read()
    source_file.close()

    co = compile(source, py_filename, 'exec')

    return marshal.dumps(co)


# Parse the command line.
parser = argparse.ArgumentParser()

parser.add_argument('py_file', help="the name of the Python source file",
        metavar="PYFILE")
parser.add_argument('--as-c',
        help="freeze the Python source as C code in FILE", metavar="FILE")
parser.add_argument('--as-data',
        help="freeze the Python source as data in FILE", metavar="FILE")
parser.add_argument('--main', help="the frozen module is __main__",
        action='store_true')

args = parser.parse_args()

# Handle the specific actions.
if args.as_c is not None:
    freeze_as_c(args.py_file, args.as_c, args.main)

if args.as_data is not None:
    freeze_as_data(args.py_file, args.as_data)
