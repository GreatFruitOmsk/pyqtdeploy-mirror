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


import os
import shutil
import subprocess
import tempfile

from PyQt5.QtCore import QDir, QFile, QFileInfo

from ..project import MfsDirectory
from ..user_exception import UserException


class Builder():
    """ The builder for a project. """

    # Map PyQt modules to the corresponding qmake QT values.
    pyqt_module_map = {
        'QAxContainer':         ('axcontainer', ),
        'QtBluetooth':          ('bluetooth', ),
        'QtCore':               ('-gui', ),
        'QtDBus':               ('dbus', '-gui'),
        'QtDesigner':           ('designer', ),
        'QtHelp':               ('help', ),
        'QtMacExtras':          ('macextras', ),
        'QtMultimedia':         ('multimedia', ),
        'QtMultimediaWidgets':  ('multimediawidgets', 'multimedia'),
        'QtNetwork':            ('network', '-gui'),
        'QtOpenGL':             ('opengl', ),
        'QtPositioning':        ('positioning', ),
        'QtPrintSupport':       ('printsupport', ),
        'QtQml':                ('qml', ),
        'QtQuick':              ('quick', ),
        'QtSensors':            ('sensors', ),
        'QtSerialPort':         ('serialport', ),
        'QtSql':                ('sql', 'widgets'),
        'QtSvg':                ('svg', ),
        'QtTest':               ('testlib', 'widgets'),
        'QtWebKit':             ('webKit', 'network'),
        'QtWebKitWidgets':      ('webkitwidgets', ),
        'QtWidgets':            ('widgets', ),
        'QtWinExtras':          ('winextras', 'widgets'),
        'QtX11Extras':          ('x11extras', ),
        'QtXmlPatterns':        ('xmlpatterns', '-gui', 'network')
    }

    def __init__(self, project):
        """ Initialise the builder for a project. """

        super().__init__()

        self._project = project

    def build(self, build_dir):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        try:
            os.makedirs(build_dir, exist_ok=True)
        except Exception as e:
            raise UserException("Unable to create the build directory.",
                    str(e))

        freeze = self._copy_lib_file('freeze.py')

        self._write_qmake(build_dir, freeze)

        if project.application_package.name != '':
            self._write_package(build_dir, project.application_package, freeze)

        os.remove(freeze)

    def _write_qmake(self, build_dir, freeze):
        """ Create the .pro file for qmake. """

        project = self._project

        app_name = os.path.basename(project.application_script)
        app_name, _ = os.path.splitext(app_name)

        f = self._create_file(build_dir, app_name + '.pro')

        f.write('TEMPLATE = app\n')

        # Configure the QT value.
        f.write('\n')

        no_gui = True
        qmake_qt = []

        if not project.qt_is_shared:
            # For static Qt builds we need to define all the modules used.
            for pyqt_m in project.pyqt_modules:
                needs_gui = True

                for qt in self.pyqt_module_map[pyqt_m]:
                    if qt == '-gui':
                        needs_gui = False
                    elif qt not in qmake_qt:
                        qmake_qt.append(qt)

                if needs_gui:
                    no_gui = False

        if no_gui:
            f.write('QT -= gui\n')

        if len(qmake_qt) != 0:
            f.write('QT += {0}\n'.format(' '.join(qmake_qt)))

        # Configure the target Python interpreter.
        f.write('\n')

        if project.python_target_include_dir != '':
            f.write(
                    'INCLUDEPATH += {0}\n'.format(
                            project.python_target_include_dir))

        if project.python_target_library != '':
            lib_dir = os.path.dirname(project.python_target_library)
            lib, _ = os.path.splitext(
                    os.path.basename(project.python_target_library))

            if lib.startswith('lib'):
                lib = lib[3:]

            f.write('LIBS += -L{0} -l{1}\n'.format(lib_dir, lib))

        # Determine the extension modules and link against them.
        # TODO - add any others.
        extensions = {}

        if len(project.pyqt_modules) > 0:
            sitepackages = project.absolute_path(
                    project.python_target_stdlib_dir) + '/site-packages'

            for pyqt in project.pyqt_modules:
                extensions[pyqt] = sitepackages + '/PyQt5'

            # Add the implicit sip module.
            extensions['sip'] = sitepackages

        if len(extensions) > 0:
            # Get the list of unique module directories.
            mod_dirs = []
            for mod_dir in extensions.values():
                if mod_dir not in mod_dirs:
                    mod_dirs.append(mod_dir)

            mod_dir_flags = ['-L' + md for md in mod_dirs]
            mod_flags = ['-l' + m for m in extensions.keys()]

            f.write(
                    'LIBS += {0} {1}\n'.format(' '.join(mod_dir_flags),
                            ' '.join(mod_flags)))

        # Specify any resource files.
        packages = []

        if project.application_package.name != '':
            packages.append(project.application_package)

        # TODO - add any other packages.

        if len(packages) != 0:
            f.write('\n')

            f.write('RESOURCES =')

            for package in packages:
                f.write(' \\\n    mfs_{0}.qrc'.format(package.sequence))

            f.write('\n')

        # Specify the source and header files.
        f.write('\n')

        f.write('SOURCES = main.c pyqtdeploy_main.c mfsimport.cpp\n')
        self._write_main_c(build_dir, app_name, extensions.keys())
        self._copy_lib_file('pyqtdeploy_main.c', build_dir)
        self._copy_lib_file('mfsimport.cpp', build_dir)

        f.write('HEADERS = frozen_bootstrap.h frozen_main.h\n')

        bootstrap_f = self._create_file(build_dir, '__bootstrap__.py')
        bootstrap_f.write('''import sys
import mfsimport

sys.path = [{0}]
sys.path_hooks = [mfsimport.mfsimporter]
'''.format(','.join(["':/mfs_{0}'".format(p.sequence) for p in packages])))
        bootstrap_f.close()

        self._freeze(os.path.join(build_dir, 'frozen_bootstrap.h'),
                os.path.join(build_dir, '__bootstrap__.py'), freeze)

        self._freeze(os.path.join(build_dir, 'frozen_main.h'),
                project.absolute_path(project.application_script), freeze,
                main=True)

        # All done.
        f.close()

    def _write_package(self, build_dir, package, freeze):
        """ Create a .qrc file for a package and the corresponding contents.
        """

        dst_root = 'mfs_{0}'.format(package.sequence)

        f = self._create_file(build_dir, dst_root + '.qrc')

        f.write('''<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource>
''')

        dst_root_dir = os.path.join(build_dir, dst_root)
        self._create_directory(dst_root_dir)

        src_root = os.path.basename(package.name)
        src_root_dir = os.path.dirname(
                self._project.absolute_path(package.name))

        self._write_package_contents(package.contents, dst_root_dir,
                src_root_dir, [src_root], freeze, f)

        f.write('''    </qresource>
</RCC>
''')

        f.close()

    def _write_package_contents(self, contents, dst_root_dir, src_root_dir, dir_stack, freeze, f):
        """ Write the contents of a single package directory. """

        dir_tail = os.path.join(*dir_stack)

        dst_dir = os.path.join(dst_root_dir, dir_tail)
        self._create_directory(dst_dir)

        prefix = os.path.basename(dst_root_dir)

        for content in contents:
            if not content.included:
                continue

            if isinstance(content, MfsDirectory):
                dir_stack.append(content.name)
                self._write_package_contents(content.contents, dst_root_dir,
                        src_root_dir, dir_stack, freeze, f)
                dir_stack.pop()
            else:
                src_file = content.name
                src_path = os.path.join(src_root_dir, dir_tail, src_file)

                if src_file.endswith('.py'):
                    dst_file = src_file[:-3]
                elif src_file.endswith('.pyw'):
                    dst_file = src_file[:-4]
                else:
                    # Just copy the file.
                    shutil.copyfile(src_path, os.path.join(dst_dir, src_file))
                    continue

                dst_file += '.pyf'
                dst_path = os.path.join(dst_dir, dst_file)

                f.write('        <file>{0}/{1}/{2}</file>\n'.format(prefix,
                        '/'.join(dir_stack), dst_file))

                self._freeze(dst_path, src_path, freeze, as_data=True)

    @classmethod
    def _write_main_c(cls, build_dir, app_name, extension_names):
        """ Create the application specific main.c file. """

        f = cls._create_file(build_dir, 'main.c')

        f.write('''#include <wchar.h>
#include <Python.h>

int main(int argc, char **argv)
{
''')

        if len(extension_names) > 0:
            inittab = 'extension_modules'

            for ext in extension_names:
                f.write('    extern PyObject *PyInit_%s(void);\n' % ext)

            f.write('''
    static struct _inittab %s[] = {
''' % inittab)

            for ext in extension_names:
                f.write('        {"%s", PyInit_%s},\n' % (ext, ext))

            f.write('''        {NULL, NULL}
    };

''')
        else:
            inittab = 'NULL'

        f.write('''    extern int pyqtdeploy_main(int argc, char **argv, wchar_t *py_main,
            struct _inittab *extension_modules);

    return pyqtdeploy_main(argc, argv, L"%s", %s);
}
''' % (app_name, inittab))

        f.close()

    def _freeze(self, output, py_filename, freeze, main=False, as_data=False):
        """ Freeze a Python source file to a C header file or a data file. """

        args = [self._project.python_host_interpreter, freeze]
        
        if main:
            args.append('--main')

        args.append('--as-data' if as_data else '--as-c')
        args.append(output)
        args.append(py_filename)

        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise UserException("Unable to freeze {0}.".format(py_filename),
                    e.output)

    @staticmethod
    def _copy_lib_file(filename, dirname=None):
        """ Copy a library file to a directory and return the full pathname of
        the copy.  If the directory wasn't specified then copy it to a
        temporary directory.
        """

        # Note that we use the Qt file operations to support the possibility
        # that pyqtdeploy itself has been deployed as a single executable.

        # The destination filename.
        if dirname is None:
            dirname = tempfile.gettempdir()

        d_filename = os.path.join(dirname, filename)

        # The source filename.
        s_dir = QFileInfo(__file__).dir()
        s_dir.cd('lib')
        s_filename = s_dir.filePath(filename)

        # Make sure the destination doesn't exist.
        QFile.remove(d_filename)

        if not QFile.copy(s_filename, QDir.fromNativeSeparators(d_filename)):
            raise UserException("Unable to copy file {0}.".format(filename))

        return d_filename

    @staticmethod
    def _create_file(build_dir, filename):
        """ Create a text file in the build directory. """

        pathname = os.path.join(build_dir, filename)

        try:
            return open(pathname, 'wt')
        except Exception as e:
            raise UserException("Unable to create file {0}.".format(pathname),
                    str(e))

    @staticmethod
    def _create_directory(dir_name):
        """ Create a directory which may already exist. """

        try:
            os.mkdir(dir_name)
        except FileExistsError:
            pass
