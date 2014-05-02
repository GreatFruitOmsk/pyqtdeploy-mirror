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

from ..metadata import pyqt4_metadata, pyqt5_metadata
from ..project import QrcDirectory, QrcFile
from ..user_exception import UserException
from ..version import PYQTDEPLOY_HEXVERSION


class Builder():
    """ The builder for a project. """

    def __init__(self, project):
        """ Initialise the builder for a project. """

        super().__init__()

        self._project = project

        self.quiet = False
        self.verbose = False

    def build(self, build_dir=None, clean=False, console=False):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        if build_dir is None:
            build_dir = project.build_dir
            if build_dir == '':
                build_dir = '.'

            build_dir = project.absolute_path(build_dir)

        if clean:
            self._progress("Cleaning {0}.".format(build_dir))
            shutil.rmtree(build_dir, ignore_errors=True)

        self._create_directory(build_dir)

        freeze = self._copy_lib_file('freeze.py')

        self._write_qmake(build_dir, console, freeze)

        resources_dir = os.path.join(build_dir, 'resources')
        self._create_directory(resources_dir)
        stdlib_dir = project.absolute_path(project.python_target_stdlib_dir)

        for resource in self.resources():
            if resource == '':
                package = project.application_package
                self._write_resource(resources_dir, resource, package, 
                        project.absolute_path(package.name), freeze)
            elif resource == 'stdlib':
                self._write_resource(resources_dir, resource,
                        project.stdlib_package, os.path.join(stdlib_dir, ''),
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
                                os.path.join(stdlib_dir, 'site-packages',
                                        pyqt_dir),
                                'uic', [])

                self._write_resource(resources_dir, resource,
                        site_packages_package,
                        os.path.join(stdlib_dir, 'site-packages', ''), freeze)

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

    def _write_qmake(self, build_dir, console, freeze):
        """ Create the .pro file for qmake. """

        project = self._project

        app_name = project.application_basename()

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

            metadata = self._get_module_metadata(pyqt_m)

            for qt in metadata.qt:
                if qt == '-gui':
                    needs_gui = False
                elif qt not in qmake_qt:
                    qmake_qt.append(qt)

            for config in metadata.config:
                if config not in qmake_config:
                    qmake_config.append(config)

            if needs_gui:
                no_gui = False

        if no_gui or console:
            f.write('CONFIG += console\n')

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
                extensions[extension_module.name] = (
                        QDir.fromNativeSeparators(
                                project.absolute_path(extension_module.path)),
                        extension_module.name)

        if len(project.pyqt_modules) > 0:
            sitepackages = QDir.fromNativeSeparators(
                    os.path.join(
                            project.absolute_path(
                                    project.python_target_stdlib_dir),
                            'site-packages'))

            pyqt_version = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'

            for pyqt in self._get_all_pyqt_modules():
                if pyqt != 'uic':
                    lib_name = pyqt
                    if self._get_module_metadata(pyqt).needs_suffix:
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
            lib_path = project.absolute_path(project.python_target_library)
            lib_dir = QDir.fromNativeSeparators(os.path.dirname(lib_path))
            lib, _ = os.path.splitext(os.path.basename(lib_path))

            if lib.startswith('lib'):
                lib = lib[3:]

            f.write('LIBS += -L{0} -l{1}\n'.format(self._quote(lib_dir), lib))

        # Add the platform specific stuff.
        platforms_f = QFile(self._lib_filename('platforms.pro'))

        if not platforms_f.open(QIODevice.ReadOnly|QIODevice.Text):
            self._error(
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
            self._error("Unable to determine target Python version")

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

    def _get_module_metadata(self, module_name):
        """ Get the metadata for a module. """

        if self._project.application_is_pyqt5:
            metadata = pyqt5_metadata
        else:
            metadata = pyqt4_metadata

        return metadata[module_name]

    def _get_all_pyqt_modules(self):
        """ Return the list of all PyQt modules including dependencies. """

        all_modules = []

        for module_name in self._project.pyqt_modules:
            self._get_module_dependencies(module_name, all_modules)

            if module_name not in all_modules:
                all_modules.append(module_name)

        return all_modules

    def _get_module_dependencies(self, module_name, all_modules):
        """ Update a list of dependencies for a module. """

        for dep in self._get_module_metadata(module_name).deps:
            if dep not in all_modules:
                all_modules.append(dep)

            # Handle sub-dependencies.
            self._get_module_dependencies(dep, all_modules)

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

        argv = [os.path.expandvars(self._project.python_host_interpreter),
            freeze]
        
        if name is not None:
            argv.append('--name')
            argv.append(name)

        argv.append('--as-data' if as_data else '--as-c')
        argv.append(output)
        argv.append(py_filename)

        self._progress("Freezing {0}".format(py_filename))

        self.run(argv, "Unable to freeze {0}.".format(py_filename))

    def run(self, argv, error_message, in_build_dir=False):
        """ Execute a command and capture the output. """

        if in_build_dir:
            saved_cwd = os.getcwd()
            build_dir = self._project.absolute_path(self._project.build_dir)
            os.chdir(build_dir)
            self._verbose(
                    "{0} is now the current directory.".format(build_dir))
        else:
            saved_cwd = None

        self._verbose("Running '{0}'".format(' '.join(argv)))

        try:
            subprocess.check_output(argv, stderr=subprocess.STDOUT,
                    universal_newlines=True)
        except subprocess.CalledProcessError as e:
            self._error(error_message, e.output)
        finally:
            if saved_cwd is not None:
                os.chdir(saved_cwd)
                self._verbose(
                        "{0} is now the current directory.".format(saved_cwd))

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
            self._error("Unable to copy file {0}.".format(filename))

        return d_filename

    @staticmethod
    def _create_file(build_dir, filename):
        """ Create a text file in the build directory. """

        pathname = os.path.join(build_dir, filename)

        try:
            return open(pathname, 'wt')
        except Exception as e:
            self._error("Unable to create file {0}.".format(pathname), str(e))

    def _create_directory(self, dir_name):
        """ Create a directory which may already exist. """

        self._verbose("Creating directory {0}.".format(dir_name))

        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            self._error(
                    "Unable to create the '{0}' directory.".format(dir_name),
                    str(e))

    def _progress(self, text):
        """ Display a progress message if requested. """

        if not self.quiet:
            self.information(text)

    def _verbose(self, text):
        """ Display a verbose progress message if requested. """

        if self.verbose:
            self.information(text)

    def _error(self, text, detail=''):
        """ Handle an error.  This will raise an exception and not return. """

        self.error(text)

        if detail != '':
            self.error(detail)

        raise UserException(text, detail)

    def information(self, text):
        """ Handle a user information message (which will not have a trailing
        newline).  This default implementation just sends it to stdout.
        """

        print(text)

    def error(self, text):
        """ Handle a user error message (which will not have a trailing
        newline).  This default implementation just sends it to stderr.
        """

        print(text, file=sys.stderr)
