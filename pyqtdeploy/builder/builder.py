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

from PyQt5.QtCore import QDir, QFile, QFileInfo, QIODevice

from ..project import QrcDirectory, QrcFile
from ..user_exception import UserException
from ..version import PYQTDEPLOY_HEXVERSION


class Builder():
    """ The builder for a project. """

    # Map PyQt modules to the corresponding qmake QT or CONFIG values.  A
    # module that doesn't need any of these values can be omitted
    class _Qt5MetaData:
        def __init__(self, qt=None, config=None, needs_suffix=False):
            self.qt = qt
            self.config = config
            self.needs_suffix = needs_suffix

    class _Qt4MetaData(_Qt5MetaData):
        def __init__(self, qt=None, config=None, needs_suffix=True):
            super().__init__(qt=qt, config=config, needs_suffix=needs_suffix)

    _pyqt5_module_map = {
        'QAxContainer':         _Qt5MetaData(qt=['axcontainer']),
        'QtBluetooth':          _Qt5MetaData(qt=['bluetooth']),
        'QtCore':               _Qt5MetaData(qt=['-gui']),
        'QtDBus':               _Qt5MetaData(qt=['dbus', '-gui']),
        'QtDesigner':           _Qt5MetaData(qt=['designer']),
        'QtHelp':               _Qt5MetaData(qt=['help']),
        'QtMacExtras':          _Qt5MetaData(qt=['macextras']),
        'QtMultimedia':         _Qt5MetaData(qt=['multimedia']),
        'QtMultimediaWidgets':  _Qt5MetaData(
                                        qt=['multimediawidgets',
                                                'multimedia']),
        'QtNetwork':            _Qt5MetaData(qt=['network', '-gui']),
        'QtOpenGL':             _Qt5MetaData(qt=['opengl']),
        'QtPositioning':        _Qt5MetaData(qt=['positioning']),
        'QtPrintSupport':       _Qt5MetaData(qt=['printsupport']),
        'QtQml':                _Qt5MetaData(qt=['qml']),
        'QtQuick':              _Qt5MetaData(qt=['quick']),
        'QtSensors':            _Qt5MetaData(qt=['sensors']),
        'QtSerialPort':         _Qt5MetaData(qt=['serialport']),
        'QtSql':                _Qt5MetaData(qt=['sql', 'widgets']),
        'QtSvg':                _Qt5MetaData(qt=['svg']),
        'QtTest':               _Qt5MetaData(qt=['testlib', 'widgets']),
        'QtWebKit':             _Qt5MetaData(qt=['webkit', 'network']),
        'QtWebKitWidgets':      _Qt5MetaData(qt=['webkitwidgets']),
        'QtWidgets':            _Qt5MetaData(qt=['widgets']),
        'QtWinExtras':          _Qt5MetaData(qt=['winextras', 'widgets']),
        'QtX11Extras':          _Qt5MetaData(qt=['x11extras']),
        'QtXmlPatterns':        _Qt5MetaData(
                                        qt=['xmlpatterns', '-gui', 'network']),

        'QtChart':              _Qt5MetaData(config=['qtcommercialchart']),
        'QtDataVisualization':  _Qt5MetaData(qt=['datavisualization']),
        'Qsci':                 _Qt5MetaData(config=['qscintilla2']),
    }

    _pyqt4_module_map = {
        'QAxContainer':         _Qt4MetaData(config=['qaxcontainer']),
        'QtCore':               _Qt4MetaData(qt=['-gui']),
        'QtDBus':               _Qt4MetaData(qt=['dbus', '-gui']),
        'QtDeclarative':        _Qt4MetaData(qt=['declarative', 'network']),
        'QtDesigner':           _Qt4MetaData(config=['designer']),
        'QtHelp':               _Qt4MetaData(config=['help']),
        'QtMultimedia':         _Qt4MetaData(qt=['multimedia']),
        'QtNetwork':            _Qt4MetaData(qt=['network', '-gui']),
        'QtOpenGL':             _Qt4MetaData(qt=['opengl']),
        'QtScript':             _Qt4MetaData(qt=['script', '-gui']),
        'QtScriptTools':        _Qt4MetaData(qt=['scripttools', 'script']),
        'QtSql':                _Qt4MetaData(qt=['sql']),
        'QtSvg':                _Qt4MetaData(qt=['svg']),
        'QtTest':               _Qt4MetaData(qt=['testlib']),
        'QtWebKit':             _Qt4MetaData(qt=['webkit', 'network']),
        'QtXml':                _Qt4MetaData(qt=['xml', '-gui']),
        'QtXmlPatterns':        _Qt4MetaData(
                                        qt=['xmlpatterns', '-gui', 'network']),
        'phonon':               _Qt4MetaData(qt=['phonon']),

        'QtChart':              _Qt4MetaData(config=['qtcommercialchart'],
                                        needs_suffix=False),
        'Qsci':                 _Qt4MetaData(config=['qscintilla2'],
                                        needs_suffix=False),
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

        self._create_directory(build_dir)

        freeze = self._copy_lib_file('freeze.py')

        self._write_qmake(build_dir, freeze)

        resources_dir = os.path.join(build_dir, 'resources')
        self._create_directory(resources_dir)

        for resource in self.resources():
            if resource == '':
                package = project.application_package
                self._write_resource(resources_dir, resource, package, 
                        project.absolute_path(package.name), freeze)
            elif resource == 'stdlib':
                self._write_resource(resources_dir, resource,
                        project.stdlib_package,
                        os.path.join(project.python_target_stdlib_dir, ''),
                        freeze)
            else:
                # Add the PyQt package to a temporary copy of the site-packages
                # package.
                site_packages_package = project.site_packages_package.copy()
                pyqt_dir = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'

                if len(project.pyqt_modules) != 0:
                    pyqt_pkg_init = QrcFile('__init__.py')
                    pyqt_pkg_dir = QrcDirectory(pyqt_dir)
                    pyqt_pkg_dir.contents.append(pyqt_pkg_init)
                    site_packages_package.contents.append(pyqt_pkg_dir)

                    # Add uic if requested.
                    if 'uic' in project.pyqt_modules:
                        self._add_uic_dir(pyqt_pkg_dir,
                                os.path.join(
                                        self._project.python_target_stdlib_dir,
                                        'site-packages', pyqt_dir),
                                'uic', [])

                self._write_resource(resources_dir, resource,
                        site_packages_package,
                        os.path.join(project.python_target_stdlib_dir,
                                'site-packages', ''),
                        freeze)

        os.remove(freeze)

    def _add_uic_dir(self, package, pyqt_dir, dirname, dir_stack):
        """ Add a uic directory to a package. """

        dir_pkg = QrcDirectory(dirname)
        package.contents.append(dir_pkg)

        dirpath = [pyqt_dir] + dir_stack + [dirname]
        dirpath = os.path.join(*dirpath)

        for content in os.listdir(dirpath):
            if content in ('port_v2', '__pycache__'):
                continue

            content_path = os.path.join(dirpath, content)

            if os.path.isfile(content_path):
                dir_pkg.contents.append(QrcFile(content))
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

            metadata = self._get_metadata(pyqt_m)

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
            f.write('CONFIG += console\n')
            f.write('QT -= gui\n')

        if len(qmake_qt) != 0:
            f.write('QT += {0}\n'.format(' '.join(qmake_qt)))

        if len(qmake_config) != 0:
            f.write('CONFIG += {0}\n'.format(' '.join(qmake_config)))

        # Determine the extension modules and link against them.
        extensions = {}

        for extension_module in project.extension_modules:
            if extension_module.name != '':
                extensions[extension_module.name] = (
                        QDir.fromNativeSeparators(
                                project.absolute_path(extension_module.path)),
                        extension_module.name)

        if len(project.pyqt_modules) > 0:
            sitepackages = QDir.fromNativeSeparators(
                    project.absolute_path(
                            project.python_target_stdlib_dir)) + '/site-packages'
            pyqt_version = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'

            for pyqt in project.pyqt_modules:
                if pyqt != 'uic':
                    lib_name = pyqt
                    if self._get_metadata(pyqt).needs_suffix:
                        # Qt4's qmake thinks -lQtCore etc. always refer to the
                        # Qt libraries so PyQt4 creates static libraries with a
                        # suffix.
                        lib_name += '_s'

                    extensions[pyqt_version + '.' + pyqt] = (
                            sitepackages + '/' + pyqt_version,
                            lib_name)

            # Add the implicit sip module.
            extensions['sip'] = (sitepackages, 'sip')

        if len(extensions) > 0:
            f.write('\n')

            # Get the list of unique module directories.
            mod_dirs = []
            for mod_dir, _ in extensions.values():
                if mod_dir not in mod_dirs:
                    mod_dirs.append(mod_dir)

            mod_dir_flags = ['-L' + self._quote(md) for md in mod_dirs]
            mod_flags = ['-l' + l for _, l in extensions.values()]

            f.write(
                    'LIBS += {0} {1}\n'.format(' '.join(mod_dir_flags),
                            ' '.join(mod_flags)))

        # Configure the target Python interpreter.
        f.write('\n')

        if project.python_target_include_dir != '':
            inc_dir = QDir.fromNativeSeparators(
                    project.absolute_path(project.python_target_include_dir))
            f.write('INCLUDEPATH += {0}\n'.format(self._quote(inc_dir)))

        if project.python_target_library != '':
            lib_dir = os.path.dirname(project.python_target_library)
            lib_dir = QDir.fromNativeSeparators(project.absolute_path(lib_dir))

            lib, _ = os.path.splitext(
                    os.path.basename(project.python_target_library))

            if lib.startswith('lib'):
                lib = lib[3:]

            f.write('LIBS += -L{0} -l{1}\n'.format(self._quote(lib_dir), lib))

        # Add the platform specific stuff.
        platforms_f = QFile(self._lib_filename('platforms.pro'))

        if not platforms_f.open(QIODevice.ReadOnly|QIODevice.Text):
            raise UserException(
                    "Unable to open file {0}.".format(platforms_f.fileName()),
                    platforms_f.errorString())

        platforms = platforms_f.readAll()
        platforms_f.close()

        f.write('\n')
        f.write(platforms.data().decode('latin1'))

        # Specify any resource files.
        resources = self.resources()

        if len(resources) != 0:
            f.write('\n')

            f.write('RESOURCES =')

            for resource in resources:
                if resource == '':
                    resource = 'pyqtdeploy'

                f.write(' \\\n    resources/{0}.qrc'.format(resource))

            f.write('\n')

        # Specify the source and header files.
        f.write('\n')

        f.write('SOURCES = main.c pyqtdeploy_main.c pyqtdeploy_module.cpp\n')
        self._write_main_c(build_dir, app_name, extensions.keys())
        self._copy_lib_file('pyqtdeploy_main.c', build_dir)
        self._copy_lib_file('pyqtdeploy_module.cpp', build_dir)

        f.write('HEADERS = frozen_bootstrap.h frozen_main.h pyqtdeploy_version.h\n')

        major, _ = project.python_target_version
        if major is None:
            raise UserException("Unable to determine target Python version")

        bootstrap = self._copy_lib_file(
                'bootstrap_py3.py' if major == 3 else 'bootstrap_py2.py')
        self._freeze(os.path.join(build_dir, 'frozen_bootstrap.h'), bootstrap,
                freeze, name='pyqtdeploy_bootstrap')
        os.remove(bootstrap)

        self._freeze(os.path.join(build_dir, 'frozen_main.h'),
                project.absolute_path(project.application_script), freeze,
                name='pyqtdeploy_main')

        version_f = self._create_file(build_dir, 'pyqtdeploy_version.h')
        version_f.write(
                '#define PYQTDEPLOY_HEXVERSION %s\n' % hex(
                        PYQTDEPLOY_HEXVERSION))
        version_f.close()

        # All done.
        f.close()

    def resources(self):
        """ Return the list of resources needed. """

        project = self._project

        resources = []

        for content in project.application_package.contents:
            if content.included:
                resources.append('')
                break

        resources.append('stdlib')

        if len(project.pyqt_modules) != 0:
            resources.append('site-packages')
        else:
            for content in project.site_packages_package.contents:
                if content.included:
                    resources.append('site-packages')
                    break

        return resources

    def _get_metadata(self, name):
        """ Get the metadata for a module. """

        if self._project.application_is_pyqt5:
            module_map = self._pyqt5_module_map
            default_metadata = self._Qt5MetaData()
        else:
            module_map = self._pyqt4_module_map
            default_metadata = self._Qt4MetaData()

        return module_map.get(name, default_metadata)

    @staticmethod
    def _quote(name):
        """ Return the quoted version of a name if quoting is required. """

        if ' ' in name:
            name = '"' + name + '"'

        return name

    def _write_resource(self, resources_dir, resource, package, src, freeze):
        """ Create a .qrc file for a resource and the corresponding contents.
        """

        # The main application resource does not go in a sub-directory.
        if resource == '':
            qrc_file = 'pyqtdeploy.qrc'
            dst_root_dir = resources_dir
        else:
            qrc_file = resource + '.qrc'
            dst_root_dir = os.path.join(resources_dir, resource)
            self._create_directory(dst_root_dir)

        f = self._create_file(resources_dir, qrc_file)

        f.write('''<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource>
''')

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
            if dir_tail == '.':
                dir_stack = []

            dst_dir = os.path.join(dst_root_dir, dir_tail)
            self._create_directory(dst_dir)

        prefix = os.path.basename(dst_root_dir)
        if prefix != 'resources':
            prefix = [prefix]
        else:
            prefix = []

        for content in contents:
            if not content.included:
                continue

            if isinstance(content, QrcDirectory):
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

                file_path = list(prefix)

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

            f.write('#if PY_MAJOR_VERSION >= 3\n')
            cls._write_inittab(f, extension_names, inittab, py3=True)
            f.write('#else\n')
            cls._write_inittab(f, extension_names, inittab, py3=False)
            f.write('#endif\n\n')
        else:
            inittab = 'NULL'

        f.write('#if PY_MAJOR_VERSION >= 3\n')
        cls._write_main_call(f, app_name, inittab, py3=True)
        f.write('#else\n')
        cls._write_main_call(f, app_name, inittab, py3=False)
        f.write('#endif\n}\n')

        f.close()

    @staticmethod
    def _write_inittab(f, extension_names, inittab, py3):
        """ Write the Python version specific extension module inittab. """

        if py3:
            init_type = 'PyObject *'
            init_prefix = 'PyInit_'
        else:
            init_type = 'void '
            init_prefix = 'init'

        for ext in extension_names:
            base_ext = ext.split('.')[-1]

            f.write('    extern %s%s%s(void);\n' % (init_type, init_prefix,
                    base_ext))

        f.write('''
    static struct _inittab %s[] = {
''' % inittab)

        for ext in extension_names:
            base_ext = ext.split('.')[-1]

            f.write('        {"%s", %s%s},\n' % (ext, init_prefix, base_ext))

        f.write('''        {NULL, NULL}
    };
''')

    @staticmethod
    def _write_main_call(f, app_name, inittab, py3):
        """ Write the Python version specific call to pyqtdeploy_main(). """

        if py3:
            name_type = 'wchar_t'
            name_prefix = 'L'
        else:
            name_type = 'char'
            name_prefix = ''

        f.write('''    extern int pyqtdeploy_main(int argc, char **argv, %s *py_main,
            struct _inittab *extension_modules);

    return pyqtdeploy_main(argc, argv, %s"%s", %s);
''' % (name_type, name_prefix, app_name, inittab))

    def _freeze(self, output, py_filename, freeze, name=None, as_data=False):
        """ Freeze a Python source file to a C header file or a data file. """

        args = [self._project.python_host_interpreter, freeze]
        
        if name is not None:
            args.append('--name')
            args.append(name)

        args.append('--as-data' if as_data else '--as-c')
        args.append(output)
        args.append(py_filename)

        self._log("Running '{0}'".format(' '.join(args)))

        try:
            subprocess.check_output(args, stderr=subprocess.STDOUT,
                    universal_newlines=True)
        except subprocess.CalledProcessError as e:
            self._log(e.output)
            raise UserException("Unable to freeze {0}.".format(py_filename),
                    e.output)

    @staticmethod
    def _lib_filename(filename):
        """ Get name of a file in the 'lib' directory that can be used by
        QFile.
        """

        lib_dir = QFileInfo(__file__).dir()
        lib_dir.cd('lib')

        return lib_dir.filePath(filename)

    @classmethod
    def _copy_lib_file(cls, filename, dirname=None):
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
        s_filename = cls._lib_filename(filename)

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
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            raise UserException(
                    "Unable to create the '{0}' directory.".format(dir_name),
                    str(e))

    def _log(self, message):
        """ Log a message if requested. """

        if self._verbose:
            print(message)
