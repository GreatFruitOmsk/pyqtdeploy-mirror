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


def freeze_as_data(py_filename, data_filename):
    """ Freeze a Python source file and save it as data. """

    code, _ = _get_marshalled_code(py_file)

    data_file = open(data_filename, 'wb')

    data_file.write(code)

    data_file.close()


def freeze_as_c(py_filename, c_filename):
    """ Freeze a Python source file and save it as C source code. """

    code, name = _get_marshalled_code(py_filename)

    c_file = open(c_filename, 'wt')

    c_file.write(
            'static unsigned char frozen_%s[] = {' % name.replace('.', '_'))

    for i in range(0, len(code), 16):
        c_file.write('\n    ')
        for j in code[i:i + 16]:
            c_file.write('%d,' % j)

    c_file.write('\n};\n')

    c_file.close()


def _get_marshalled_code(py_filename):
    """ Convert a Python source file to a marshalled code object and the name
    of the module.
    """

    mf = modulefinder.ModuleFinder()

    mf.load_file(py_filename)

    # Find the module corresponding to the Python file.
    for name, mod in mf.modules.items():
        if mod.__code__.co_filename == py_file:
            return marshal.dumps(mod.__code__, MARSHAL_VERSION), name

    return None, None
