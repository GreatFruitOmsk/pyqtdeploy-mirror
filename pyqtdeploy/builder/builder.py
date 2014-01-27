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
import subprocess
import tempfile

from PyQt5.QtCore import QDir, QFile, QFileInfo

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

        try:
            os.makedirs(build_dir, exist_ok=True)
        except Exception as e:
            raise UserException("Unable to create the build directory.",
                    str(e))

        freeze = self._copy_lib_file('freeze.py')
        self._write_qmake(build_dir, freeze)
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

        # Specify the source and header files.
        f.write('\n')

        f.write('SOURCES = main.c pyqtdeploy_main.c mfsimport.cpp\n')
        self._write_main_c(build_dir, app_name)
        self._copy_lib_file('pyqtdeploy_main.c', build_dir)
        self._copy_lib_file('mfsimport.cpp', build_dir)

        f.write('HEADERS = frozen_bootstrap.h frozen_main.h\n')

        bootstrap = self._copy_lib_file('__bootstrap__.py')
        self._freeze(os.path.join(build_dir, 'frozen_bootstrap.h'), bootstrap,
                freeze)
        os.remove(bootstrap)

        self._freeze(os.path.join(build_dir, 'frozen_main.h'),
                self._file_from_project(project.application_script), freeze,
                main=True)

        # All done.
        f.close()

    @classmethod
    def _write_main_c(cls, build_dir, app_name):
        """ Create the application specific main.c file. """

        f = cls._create_file(build_dir, 'main.c')

        f.write('''#include <wchar.h>

int main(int argc, char **argv)
{
    extern int pyqtdeploy_main(int argc, char **argv, wchar_t *py_main);

    return pyqtdeploy_main(argc, argv, L"%s");
}
''' % app_name)

        f.close()

    def _freeze(self, h_filename, py_filename, freeze, main=False):
        """ Freeze a Python source file to a C header file. """

        args = [self._project.python_host_interpreter, freeze]
        
        if main:
            args.append('--main')
            
        args.extend(['--as-c', h_filename, py_filename])

        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise UserException("Unable to freeze {0}.".format(py_filename),
                    e.output)

    def _file_from_project(self, filename):
        """ Return the full pathname of a file.  A relative name is resolved
        against the directory containing the project file.
        """

        if os.path.isabs(filename):
            return filename

        prj_dir = os.path.dirname(self._project.filename)
        filename = os.path.join(prj_dir, filename)

        return os.path.abspath(filename)

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
