#!/usr/bin/env python3

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


import marshal
import modulefinder


# The default for Python v3.3 is 2, v3.4 is 4.
MARSHAL_VERSION = 2


def freeze_as_data(py_file, is_main, output):

    _, code = _get_marshalled_code(py_file, is_main)

    output.buffer.write(code)


def freeze_as_c(py_file, is_main, output):

    name, code = _get_marshalled_code(py_file, is_main)

    output.write(
            'static unsigned char frozen_%s[] = {' % name.replace('.', '_'))

    for i in range(0, len(code), 16):
        output.write('\n    ')
        for j in code[i:i + 16]:
            output.write('%d,' % j)

    output.write('\n};\n')


def _get_marshalled_code(py_file, is_main):

    mf = modulefinder.ModuleFinder()

    if is_main:
        mf.run_script(py_file)
    else:
        mf.load_file(py_file)

    # Find the module corresponding to the Python file.
    for name, mod in mf.modules.items():
        if mod.__code__.co_filename == py_file:
            return name, marshal.dumps(mod.__code__, MARSHAL_VERSION)

    return None, None


if __name__ == '__main__':

    import argparse
    import sys

    # Parse the command line.
    parser = argparse.ArgumentParser()

    parser.add_argument("--main", help="the module is __main__",
            action='store_true', default=False)
    parser.add_argument("--freeze", help="freeze PY-FILE to a data file",
            metavar='PY-FILE')
    parser.add_argument("--freeze-c", help="freeze PY-FILE to a C file",
            metavar='PY-FILE')
    parser.add_argument("-o", "--output",
            help="write the output to FILE instead of stdout", metavar='FILE')

    args = parser.parse_args()

    # Handle the generic arguments.
    if args.output is not None:
        output = open(args.output, 'w')
    else:
        output = sys.stdout

    # Handle the specific actions.
    if args.freeze is not None:
        freeze_as_data(args.freeze, args.main, output)

    if args.freeze_c is not None:
        freeze_as_c(args.freeze_c, args.main, output)

    # All done.
    sys.exit()
