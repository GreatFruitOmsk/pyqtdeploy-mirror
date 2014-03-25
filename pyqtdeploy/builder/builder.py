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


import os
import shutil
import subprocess
import tempfile

from PyQt5.QtCore import QDir, QFile, QFileInfo

from ..project import MfsDirectory, MfsFile
from ..user_exception import UserException


class Builder():
    """ The builder for a project. """

    # Map PyQt modules to the corresponding qmake QT or CONFIG values.
    class QtMetaData:
        def __init__(self, qt=None, config=None):
            self.qt = qt
            self.config = config

    _pyqt_module_map = {
        'QAxContainer':         QtMetaData(qt=['axcontainer']),
        'QtBluetooth':          QtMetaData(qt=['bluetooth']),
        'QtCore':               QtMetaData(qt=['-gui']),
        'QtDBus':               QtMetaData(qt=['dbus', '-gui']),
        'QtDesigner':           QtMetaData(qt=['designer']),
        'QtGui':                QtMetaData(),
        'QtHelp':               QtMetaData(qt=['help']),
        'QtMacExtras':          QtMetaData(qt=['macextras']),
        'QtMultimedia':         QtMetaData(qt=['multimedia']),
        'QtMultimediaWidgets':  QtMetaData(
                                        qt=['multimediawidgets',
                                                'multimedia']),
        'QtNetwork':            QtMetaData(qt=['network', '-gui']),
        'QtOpenGL':             QtMetaData(qt=['opengl']),
        'QtPositioning':        QtMetaData(qt=['positioning']),
        'QtPrintSupport':       QtMetaData(qt=['printsupport']),
        'QtQml':                QtMetaData(qt=['qml']),
        'QtQuick':              QtMetaData(qt=['quick']),
        'QtSensors':            QtMetaData(qt=['sensors']),
        'QtSerialPort':         QtMetaData(qt=['serialport']),
        'QtSql':                QtMetaData(qt=['sql', 'widgets']),
        'QtSvg':                QtMetaData(qt=['svg']),
        'QtTest':               QtMetaData(qt=['testlib', 'widgets']),
        'QtWebKit':             QtMetaData(qt=['webKit', 'network']),
        'QtWebKitWidgets':      QtMetaData(qt=['webkitwidgets']),
        'QtWidgets':            QtMetaData(qt=['widgets']),
        'QtWinExtras':          QtMetaData(qt=['winextras', 'widgets']),
        'QtX11Extras':          QtMetaData(qt=['x11extras']),
        'QtXmlPatterns':        QtMetaData(
                                        qt=['xmlpatterns', '-gui', 'network']),

        'QtChart':              QtMetaData(config=['qtcommercialchart']),
        'QtDataVisualization':  QtMetaData(qt=['datavisualization']),
        'Qsci':                 QtMetaData(config=['qscintilla2']),
    }

    def __init__(self, project, verbose=False):
        """ Initialise the builder for a project. """

        super().__init__()

        self._project = project
        self._verbose = verbose

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

        for resource in self.resources():
            if resource == 'application':
                package = project.application_package
                self._write_resource(build_dir, resource, package, 
                        project.absolute_path(package.name), freeze)
            elif resource == 'stdlib':
                self._write_resource(build_dir, resource,
                        project.stdlib_package,
                        os.path.join(project.python_target_stdlib_dir, ''),
                        freeze)
            else:
                # Add the PyQt package to a temporary copy of the site-packages
                # package.
                site_packages_package = project.site_packages_package.copy()

                if len(project.pyqt_modules) != 0:
                    pyqt_pkg_init = MfsFile('__init__.py')
                    pyqt_pkg_dir = MfsDirectory('PyQt5')
                    pyqt_pkg_dir.contents.append(pyqt_pkg_init)
                    site_packages_package.contents.append(pyqt_pkg_dir)

                    # Add uic if requested.
                    if 'uic' in project.pyqt_modules:
                        self._add_uic_dir(pyqt_pkg_dir,
                                os.path.join(
                                        self._project.python_target_stdlib_dir,
                                        'site-packages', 'PyQt5'),
                                'uic', [])

                self._write_resource(build_dir, resource,
                        site_packages_package,
                        os.path.join(project.python_target_stdlib_dir,
                                'site-packages', ''),
                        freeze)

        os.remove(freeze)

    def _add_uic_dir(self, package, pyqt_dir, dirname, dir_stack):
        """ Add a uic directory to a package. """

        dir_pkg = MfsDirectory(dirname)
        package.contents.append(dir_pkg)

        dirpath = [pyqt_dir] + dir_stack + [dirname]
        dirpath = os.path.join(*dirpath)

        for content in os.listdir(dirpath):
            if content in ('port_v2', '__pycache__'):
                continue

            content_path = os.path.join(dirpath, content)

            if os.path.isfile(content_path):
                dir_pkg.contents.append(MfsFile(content))
            elif os.path.isdir(content_path):
                dir_stack.append(dirname)
                self._add_uic_dir(dir_pkg, pyqt_dir, content, dir_stack)
                dir_stack.pop()

    def _write_qmake(self, build_dir, freeze):
        """ Create the .pro file for qmake. """

        project = self._project

        app_name = os.path.basename(project.application_script)
        app_name, _ = os.path.splitext(app_name)

        f = self._create_file(build_dir, app_name + '.pro')

        f.write('TEMPLATE = app\n')
        f.write('CONFIG += release warn_on\n')

        # Configure the QT value.
        f.write('\n')

        no_gui = True
        qmake_qt = []
        qmake_config = []

        for pyqt_m in project.pyqt_modules:
            needs_gui = True

            try:
                metadata = self._pyqt_module_map[pyqt_m]
            except KeyError:
                pass

            if metadata.qt is not None:
                for qt in metadata.qt:
                    if qt == '-gui':
                        needs_gui = False
                    elif qt not in qmake_qt:
                        qmake_qt.append(qt)

            if metadata.config is not None:
                for config in metadata.config:
                    if config not in qmake_config:
                        qmake_config.append(config)

            if needs_gui:
                no_gui = False

        if no_gui:
            f.write('QT -= gui\n')

        if len(qmake_qt) != 0:
            f.write('QT += {0}\n'.format(' '.join(qmake_qt)))

        if len(qmake_config) != 0:
            f.write('CONFIG += {0}\n'.format(' '.join(qmake_config)))

        # Determine the extension modules and link against them.
        extensions = {}

        for extension_module in project.extension_modules:
            if extension_module.name != '':
                extensions[extension_module.name] = extension_module.path

        if len(project.pyqt_modules) > 0:
            sitepackages = project.absolute_path(
                    project.python_target_stdlib_dir) + '/site-packages'

            for pyqt in project.pyqt_modules:
                if pyqt != 'uic':
                    extensions['PyQt5.' + pyqt] = sitepackages + '/PyQt5'

            # Add the implicit sip module.
            extensions['sip'] = sitepackages

        if len(extensions) > 0:
            f.write('\n')

            # Get the list of unique module directories.
            mod_dirs = []
            for mod_dir in extensions.values():
                if mod_dir not in mod_dirs:
                    mod_dirs.append(mod_dir)

            mod_dir_flags = ['-L' + md for md in mod_dirs]
            mod_flags = ['-l' + m.split('.')[-1] for m in extensions.keys()]

            f.write(
                    'LIBS += {0} {1}\n'.format(' '.join(mod_dir_flags),
                            ' '.join(mod_flags)))

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

        # Specify any resource files.
        resources = self.resources()

        if len(resources) != 0:
            f.write('\n')

            f.write('RESOURCES =')

            for resource in resources:
                f.write(' \\\n    {0}.qrc'.format(resource))

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
'''.format(', '.join(["':/{0}'".format(resource) for resource in resources])))
        bootstrap_f.close()

        self._freeze(os.path.join(build_dir, 'frozen_bootstrap.h'),
                os.path.join(build_dir, '__bootstrap__.py'), freeze)

        self._freeze(os.path.join(build_dir, 'frozen_main.h'),
                project.absolute_path(project.application_script), freeze,
                main=True)

        # All done.
        f.close()

    def resources(self):
        """ Return the list of resources needed. """

        project = self._project

        resources = []

        if project.application_package.name != '':
            resources.append('application')

        resources.append('stdlib')

        if len(project.pyqt_modules) != 0:
            resources.append('site-packages')
        else:
            for content in project.site_packages_package.contents:
                if content.included:
                    resources.append('site-packages')
                    break

        return resources

    def _write_resource(self, build_dir, resource, package, src, freeze):
        """ Create a .qrc file for a resource and the corresponding contents.
        """

        f = self._create_file(build_dir, resource + '.qrc')

        f.write('''<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource>
''')

        dst_root_dir = os.path.join(build_dir, resource)
        self._create_directory(dst_root_dir)

        src_root_dir, src_root = os.path.split(src)

        self._write_package_contents(package.contents, dst_root_dir,
                src_root_dir, [src_root], freeze, f)

        f.write('''    </qresource>
</RCC>
''')

        f.close()

    def _write_package_contents(self, contents, dst_root_dir, src_root_dir, dir_stack, freeze, f):
        """ Write the contents of a single package directory. """

        dir_tail = os.path.join(*dir_stack)

        if dir_tail == '':
            dir_stack = []
            dst_dir = dst_root_dir
        else:
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
                freeze_file = True
                src_file = content.name
                src_path = os.path.join(src_root_dir, dir_tail, src_file)

                if src_file.endswith('.py'):
                    dst_file = src_file[:-3] + '.pyf'
                elif src_file.endswith('.pyw'):
                    dst_file = src_file[:-4] + '.pyf'
                else:
                    # Just copy the file.
                    dst_file = src_file
                    freeze_file = False

                dst_path = os.path.join(dst_dir, dst_file)

                file_path = [prefix]

                if dir_tail != '':
                    file_path.extend(dir_stack)

                file_path.append(dst_file)

                f.write(
                        '        <file>{0}</file>\n'.format(
                                '/'.join(file_path)))

                if freeze_file:
                    self._freeze(dst_path, src_path, freeze, as_data=True)
                else:
                    shutil.copyfile(src_path, dst_path)

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
                base_ext = ext.split('.')[-1]

                f.write('    extern PyObject *PyInit_%s(void);\n' % base_ext)

            f.write('''
    static struct _inittab %s[] = {
''' % inittab)

            for ext in extension_names:
                base_ext = ext.split('.')[-1]

                f.write('        {"%s", PyInit_%s},\n' % (ext, base_ext))

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

        self._log("Freezing {0}".format(py_filename))

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

    def _log(self, message):
        """ Log a message if requested. """

        if self._verbose:
            print(message)
