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
import sys
import tempfile

from PyQt5.QtCore import QDir, QFile

from ..file_utilities import (create_file, get_embedded_dir,
        get_embedded_file_for_version, read_embedded_file)
from ..metadata import (external_libraries_metadata, get_python_metadata,
        pyqt4_metadata, pyqt5_metadata)
from ..project import QrcDirectory
from ..user_exception import UserException
from ..version import PYQTDEPLOY_HEXVERSION


class Builder():
    """ The builder for a project. """

    def __init__(self, project, message_handler):
        """ Initialise the builder for a project. """

        super().__init__()

        self._project = project
        self._message_handler = message_handler

    def build(self, opt, build_dir=None, clean=False, console=False):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        # Get the names of the required Python modules, extension modules and
        # libraries.
        metadata = get_python_metadata(project.python_target_version)
        required_modules, required_libraries = project.get_stdlib_requirements(
                include_hidden=True)

        required_py = {}
        required_ext = {}
        for name in required_modules.keys():
            module = metadata[name]

            if module.source is None:
                required_py[name] = module
            elif not module.core:
                required_ext[name] = module

        # Initialise and check we have the information we need.
        if len(required_py) != 0 or len(required_ext) != 0:
            if project.python_source_dir == '':
                raise UserException(
                        "The name of the Python source directory has not been "
                        "specified")

        if project.get_executable_basename() == '':
            raise UserException("The name of the application has not been "
                    "specified and cannot be inferred")

        if project.application_script == '':
            if project.application_entry_point == '':
                raise UserException("Either the application script name or "
                        "the entry point must be specified")
            elif len(project.application_entry_point.split(':')) != 2:
                raise UserException("An entry point must be a module name and "
                        "a callable separated by a colon.")
        elif project.application_entry_point != '':
            raise UserException("Either the application script name or the "
                    "entry point must be specified but not both")

        # Get the name of the build directory.
        if build_dir is None:
            build_dir = project.build_dir
            if build_dir == '':
                build_dir = '.'

            build_dir = project.absolute_path(build_dir)

        # Remove any build directory if required.
        if clean:
            self._message_handler.progress_message(
                    "Cleaning {0}".format(build_dir))
            shutil.rmtree(build_dir, ignore_errors=True)

        # Now start the build.
        self._create_directory(build_dir)

        # The odd naming of the Python source files is to prevent them from
        # being frozen if we deploy ourself.
        freeze = self._copy_lib_file(self._get_lib_file_name('freeze.python'),
                dst_file_name='freeze.py')

        self._write_qmake(build_dir, required_ext, required_libraries, console,
                freeze, opt)

        # Freeze the bootstrap.
        py_major, py_minor = project.python_target_version
        py_version = (py_major << 16) + (py_minor << 8)

        bootstrap_src = get_embedded_file_for_version(py_version, __file__,
                'lib', 'bootstrap')
        bootstrap = self._copy_lib_file(bootstrap_src,
                dst_file_name='bootstrap.py')
        self._freeze(os.path.join(build_dir, 'frozen_bootstrap.h'), bootstrap,
                freeze, opt, name='pyqtdeploy_bootstrap')
        os.remove(bootstrap)

        # Freeze any main application script.
        if project.application_script != '':
            self._freeze(os.path.join(build_dir, 'frozen_main.h'),
                    project.absolute_path(project.application_script), freeze,
                    opt, name='pyqtdeploy_main')

        # Create the pyqtdeploy module version file.
        version_f = self._create_file(build_dir, 'pyqtdeploy_version.h')
        version_f.write(
                '#define PYQTDEPLOY_HEXVERSION %s\n' % hex(
                        PYQTDEPLOY_HEXVERSION))
        version_f.close()

        # Generate the application resource.
        self._generate_resource(os.path.join(build_dir, 'resources'),
                required_py, freeze, opt)

        os.remove(freeze)

    def _generate_resource(self, resources_dir, required_py, freeze, opt):
        """ Generate the application resource. """

        project = self._project

        self._create_directory(resources_dir)
        resource_contents = []

        # Handle any application package.
        if project.application_package.name != '':
            package_src_dir, package_name = self._package_details(
                    project.application_package)

            self._write_package(resource_contents, resources_dir, package_name,
                    project.application_package, package_src_dir, freeze, opt)

        # Handle the Python standard library.
        self._write_stdlib(resource_contents, resources_dir, required_py,
                freeze, opt)

        # Handle any additional packages.
        for package in project.packages:
            package_src_dir, package_name = self._package_details(package)

            self._write_package(resource_contents, resources_dir, package_name,
                    package, package_src_dir, freeze, opt)

        # Handle the PyQt package.
        if len(project.pyqt_modules) != 0:
            pyqt_subdir = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'
            pyqt_dst_dir = os.path.join(resources_dir, pyqt_subdir)
            pyqt_src_dir = os.path.join(sitepackages_src_dir, pyqt_subdir)

            self._create_directory(pyqt_dst_dir)

            self._freeze(os.path.join(pyqt_dst_dir, '__init__.pyo'),
                    os.path.join(pyqt_src_dir, '__init__.py'), freeze, opt)

            resource_contents.append(pyqt_subdir + '/__init__.pyo')

            # Handle the PyQt.uic package.
            if 'uic' in project.pyqt_modules:
                uic_src_dir = os.path.join(pyqt_src_dir, 'uic')

                skip_dirs = ['__pycache__']
                if project.python_target_version[0] == 3:
                    skip_dirs.append('port_v2')
                else:
                    skip_dirs.append('port_v3')

                def copy_freeze(src, dst):
                    for skip in skip_dirs:
                        if skip in src:
                            break
                    else:
                        if dst.endswith('.py'):
                            dst += 'o'
                            self._freeze(dst, src, freeze, opt)
                            rel_dst = dst[len(resources_dir) + 1:]
                            resource_contents.append(rel_dst.replace('\\', '/'))

                shutil.copytree(os.path.join(pyqt_src_dir, 'uic'),
                        os.path.join(pyqt_dst_dir, 'uic'),
                        copy_function=copy_freeze)

        # Write the .qrc file.
        f = self._create_file(resources_dir, 'pyqtdeploy.qrc')

        f.write('''<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource>
''')

        for content in resource_contents:
            f.write('        <file>{0}</file>\n'.format(content))

        f.write('''    </qresource>
</RCC>
''')

        f.close()

    def _write_stdlib_py(self, resource_contents, resources_dir, required_py, freeze, opt):
        """ Write the required parts of the Python standard library that are
        implemented in Python.
        """

        project = self._project

        stdlib_src_dir = project.absolute_path(
                project.python_target_stdlib_dir)

        # By sorting the names we ensure parents are handled before children.
        for name in sorted(required_py.keys()):
            name_path = os.path.join(*name.split('.'))
            name_qrc = name.replace('.', '/')

            if required_py[name].modules is None:
                in_file = name_path + '.py'
                out_file = name_path + '.pyo'
                qrc_file = name_qrc + '.pyo'
            else:
                in_file = os.path.join(name_path, '__init__.py')
                out_file = os.path.join(name_path, '__init__.pyo')
                qrc_file = name_qrc + '/__init__.pyo'
                self._create_directory(os.path.join(resources_dir, name_path))

            self._freeze(os.path.join(resources_dir, out_file),
                    os.path.join(stdlib_src_dir, in_file), freeze, opt)

            resource_contents.append(qrc_file)

    def _package_details(self, package):
        """ Return the absolute source directory of a package and its name. """

        package_src_dir = self._project.absolute_path(package.name)
        package_name, _ = os.path.splitext(os.path.basename(package_src_dir))

        return package_src_dir, package_name

    def _write_qmake(self, build_dir, required_ext, required_libraries, console, freeze, opt):
        """ Create the .pro file for qmake. """

        project = self._project

        f = self._create_file(build_dir,
                project.get_executable_basename() + '.pro')

        f.write('TEMPLATE = app\n')
        f.write('\n')

        # Configure the CONFIG and QT values.
        needs_gui = False
        qmake_qt4 = set()
        qmake_config4 = set()
        qmake_qt5 = set()
        qmake_config5 = set()

        for pyqt_m in project.pyqt_modules:
            metadata = self._get_pyqt_module_metadata(pyqt_m)

            if metadata.gui:
                needs_gui = True

            qmake_qt4.update(metadata.qt4)
            qmake_config4.update(metadata.config4)
            qmake_qt5.update(metadata.qt5)
            qmake_config5.update(metadata.config5)

        both_qt = qmake_qt4 & qmake_qt5
        qmake_qt4 -= both_qt
        qmake_qt5 -= both_qt

        both_config = qmake_qt4 & qmake_qt5
        qmake_config4 -= both_config
        qmake_config5 -= both_config

        both_config.add('release')
        both_config.add('warn_on')

        if not needs_gui or console:
            both_config.add('console')

        f.write('CONFIG += {0}\n'.format(' '.join(both_config)))

        if not needs_gui:
            f.write('QT -= gui\n')

        if both_qt:
            f.write('QT += {0}\n'.format(' '.join(both_qt)))

        if qmake_config4 or qmake_qt4:
            f.write('\n')
            f.write('lessThan(QT_MAJOR_VERSION, 5) {\n')

            if qmake_config4:
                f.write('    CONFIG += {0}\n'.format(' '.join(qmake_config4)))

            if qmake_qt4:
                f.write('    QT += {0}\n'.format(' '.join(qmake_qt4)))

            f.write('}\n')

        if qmake_config5 or qmake_qt5:
            f.write('\n')
            f.write('greaterThan(QT_MAJOR_VERSION, 4) {\n')

            if qmake_config5:
                f.write('    CONFIG += {0}\n'.format(' '.join(qmake_config5)))

            if qmake_qt5:
                f.write('    QT += {0}\n'.format(' '.join(qmake_qt5)))

            f.write('}\n')

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
                    if self._get_pyqt_module_metadata(pyqt).needs_suffix:
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
        platforms = read_embedded_file(
                self._get_lib_file_name('platforms.pro'))

        f.write('\n')
        f.write(platforms.data().decode('latin1'))

        # Specify the resource file.
        f.write('\n')
        f.write('RESOURCES = resources/pyqtdeploy.qrc\n')

        # Specify the source and header files.
        f.write('\n')

        # Add any standard library modules to the inittab list.
        extension_module_names = {name: None for name in extensions.keys()}
        for name, module in required_ext.items():
            extension_module_names[name] = module.windows

        f.write('SOURCES = main.c pyqtdeploy_start.cpp pdytools_module.cpp\n')
        self._write_main_c(build_dir, extension_module_names)
        self._copy_lib_file('pyqtdeploy_start.cpp', build_dir)
        self._copy_lib_file('pdytools_module.cpp', build_dir)

        headers = 'HEADERS = pyqtdeploy_version.h frozen_bootstrap.h'
        if project.application_script != '':
            f.write('DEFINES += PYQTDEPLOY_FROZEN_MAIN\n')
            headers += ' frozen_main.h'

        f.write(headers)
        f.write('\n')

        # Handle any standard library extension modules.
        if len(required_ext) != 0:
            source_dir = project.absolute_path(project.python_source_dir)

            f.write('\nINCLUDEPATH += {0}/Modules\n'.format(source_dir))

            # Modules can share sources so we need to make sure we don't
            # include them more than once.
            used_sources = []

            for name, module in required_ext.items():
                f.write('\n')

                if module.windows is not None:
                    prefix = '    '

                    if module.windows:
                        f.write('win32 {\n')
                    else:
                        f.write('!win32 {\n')
                else:
                    prefix = ''

                if module.defines != '':
                    f.write(
                            '{0}DEFINES += {1}\n'.format(
                                    prefix, module.defines))

                if module.subdir != '':
                    f.write(
                            '{0}INCLUDEPATH += {1}/Modules/{2}\n'.format(
                                    prefix, source_dir, module.subdir))

                module_sources = []
                for src in module.sources:
                    if src not in used_sources:
                        module_sources.append(src)
                        used_sources.append(src)

                if module_sources:
                    f.write(
                            '{0}SOURCES += {1}\n'.format(
                                    prefix,
                                    ' '.join(['{0}/Modules/{1}'.format(source_dir, src) for src in module_sources])))

                if module.windows is not None:
                    f.write('}\n')

        # Handle the required external libraries.
        for required_lib in required_libraries:
            required_lib = external_libraries_metadata[required_lib]

            for xlib in project.external_libraries:
                if xlib.name == required_lib:
                    defines = xlib.defines
                    includepath = xlib.includepath
                    libs = xlib.libs
                    break
            else:
                defines = ''
                includepath = ''
                libs = required_lib.libs

            f.write('\n')

            if defines != '':
                f.write('DEFINES += {0}\n'.format(defines))

            if includepath != '':
                f.write('INCLUDEPATH += {0}\n'.format(includepath))

            if libs != '':
                f.write('LIBS += {0}\n'.format(libs))

        # All done.
        f.close()

    def _get_py_module_metadata(self, name):
        """ Get the meta-data for a Python module. """

        return get_python_metadata(self._project.python_target_version).get(name)

    def _get_pyqt_module_metadata(self, module_name):
        """ Get the meta-data for a PyQt module. """

        if self._project.application_is_pyqt5:
            metadata = pyqt5_metadata
        else:
            metadata = pyqt4_metadata

        return metadata[module_name]

    def _get_all_pyqt_modules(self):
        """ Return the list of all PyQt modules including dependencies. """

        all_modules = []

        for module_name in self._project.pyqt_modules:
            self._get_pyqt_module_dependencies(module_name, all_modules)

            if module_name not in all_modules:
                all_modules.append(module_name)

        return all_modules

    def _get_pyqt_module_dependencies(self, module_name, all_modules):
        """ Update a list of dependencies for a PyQt module. """

        for dep in self._get_pyqt_module_metadata(module_name).deps:
            if dep not in all_modules:
                all_modules.append(dep)

            # Handle sub-dependencies.
            self._get_pyqt_module_dependencies(dep, all_modules)

    @staticmethod
    def _quote(name):
        """ Return the quoted version of a name if quoting is required. """

        if ' ' in name:
            name = '"' + name + '"'

        return name

    def _write_package(self, resource_contents, resources_dir, resource, package, src_dir, freeze, opt):
        """ Write the contents of a single package and return the list of files
        written relative to the resources directory.
        """

        if resource == '':
            dst_dir = resources_dir
            dir_stack = []
        else:
            dst_dir = os.path.join(resources_dir, resource)
            dir_stack = [resource]

        self._write_package_contents(package.contents, dst_dir, src_dir,
                dir_stack, freeze, opt, resource_contents)

    def _write_package_contents(self, contents, dst_dir, src_dir, dir_stack, freeze, opt, resource_contents):
        """ Write the contents of a single package directory. """

        self._create_directory(dst_dir)

        for content in contents:
            if not content.included:
                continue

            if isinstance(content, QrcDirectory):
                dir_stack.append(content.name)

                self._write_package_contents(content.contents,
                        os.path.join(dst_dir, content.name),
                        os.path.join(src_dir, content.name), dir_stack, freeze,
                        opt, resource_contents)

                dir_stack.pop()
            else:
                freeze_file = True
                src_file = content.name
                src_path = os.path.join(src_dir, src_file)

                if src_file.endswith('.py'):
                    dst_file = src_file[:-3] + '.pyo'
                elif src_file.endswith('.pyw'):
                    dst_file = src_file[:-4] + '.pyo'
                else:
                    # Just copy the file.
                    dst_file = src_file
                    freeze_file = False

                dst_path = os.path.join(dst_dir, dst_file)

                if freeze_file:
                    self._freeze(dst_path, src_path, freeze, opt)
                else:
                    shutil.copyfile(src_path, dst_path)

                file_path = list(dir_stack)
                file_path.append(dst_file)
                resource_contents.append('/'.join(file_path))

    def _write_main_c(self, build_dir, extension_names):
        """ Create the application specific main.c file. """

        project = self._project

        f = self._create_file(build_dir, 'main.c')

        f.write('''#include <Python.h>

''')

        if len(extension_names) > 0:
            inittab = 'extension_modules'

            f.write('#if PY_MAJOR_VERSION >= 3\n')
            self._write_inittab(f, extension_names, inittab, py3=True)
            f.write('#else\n')
            self._write_inittab(f, extension_names, inittab, py3=False)
            f.write('#endif\n\n')
        else:
            inittab = 'NULL'

        sys_path = project.sys_path

        if sys_path != '':
            f.write('static const char *path_dirs[] = {\n')

            # Extract the (possibly quoted) individual directories.
            start = -1
            quote = ''

            for i, ch in enumerate(sys_path):
                dir_name = None

                if ch == quote:
                    dir_name = sys_path[start:i]
                    start = -1
                    quote = ''
                elif ch in ('"\''):
                    start = i + 1
                    quote = ch
                elif quote == '' and ch == ' ':
                    if start != -1:
                        dir_name = sys_path[start:i]
                        start = -1
                else:
                    if start == -1:
                        start = i

                if dir_name is not None:
                    f.write('    "{0}",\n'.format(dir_name))

            if start != -1:
                f.write('    "{0}",\n'.format(sys_path[start:]))

            f.write('''    NULL
};

''')

        if project.application_script != '':
            main_module = '__main__'
            entry_point = 'NULL'
        else:
            main_module, entry_point = project.application_entry_point.split(
                    ':')
            entry_point = '"' + entry_point + '"'

        path_dirs = 'path_dirs' if sys_path != '' else 'NULL'

        f.write('''extern int pyqtdeploy_start(int argc, char **argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);
''')

        f.write('''
int main(int argc, char **argv)
{
    return pyqtdeploy_start(argc, argv, %s, "%s", %s, %s);
}
''' % (inittab, main_module, entry_point, path_dirs))

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

        for ext, windows in extension_names.items():
            base_ext = ext.split('.')[-1]

            if windows is not None:
                if windows:
                    f.write('#if defined(WIN32) || defined(WIN64)\n')
                else:
                    f.write('#if !defined(WIN32) && !defined(WIN64)\n')

            f.write('extern %s%s%s(void);\n' % (init_type, init_prefix,
                    base_ext))

            if windows is not None:
                f.write('#endif\n')

        f.write('''
static struct _inittab %s[] = {
''' % inittab)

        for ext, windows in extension_names.items():
            base_ext = ext.split('.')[-1]

            if windows is not None:
                if windows:
                    f.write('#if defined(WIN32) || defined(WIN64)\n')
                else:
                    f.write('#if !defined(WIN32) && !defined(WIN64)\n')

            f.write('    {"%s", %s%s},\n' % (ext, init_prefix, base_ext))

            if windows is not None:
                f.write('#endif\n')

        f.write('''    {NULL, NULL}
};
''')

    def _freeze(self, out_file, in_file, freeze, opt, name=None):
        """ Freeze a Python source file to a C header file or a data file. """

        argv = [os.path.expandvars(self._project.python_host_interpreter)]

        if opt == 2:
            argv.append('-OO')
        elif opt == 1:
            argv.append('-O')

        argv.append(freeze)
        
        if name is not None:
            argv.append('--as-c')
            argv.append('--name')
            argv.append(name)
        else:
            argv.append('--as-data')

        argv.append(out_file)
        argv.append(in_file)

        self._message_handler.progress_message("Freezing {0}".format(in_file))

        self.run(argv, "Unable to freeze {0}".format(in_file))

    def run(self, argv, error_message, in_build_dir=False):
        """ Execute a command and capture the output. """

        if in_build_dir:
            saved_cwd = os.getcwd()
            build_dir = self._project.absolute_path(self._project.build_dir)
            os.chdir(build_dir)
            self._message_handler.verbose_message(
                    "{0} is now the current directory".format(build_dir))
        else:
            saved_cwd = None

        self._message_handler.verbose_message(
                "Running '{0}'".format(' '.join(argv)))

        try:
            subprocess.check_output(argv, stderr=subprocess.STDOUT,
                    universal_newlines=True)
        except subprocess.CalledProcessError as e:
            raise UserException(error_message, e.output)
        except FileNotFoundError:
            raise UserException("{0} does not seem to exist".format(argv[0]))
        finally:
            if saved_cwd is not None:
                os.chdir(saved_cwd)
                self._message_handler.verbose_message(
                        "{0} is now the current directory".format(saved_cwd))

    @staticmethod
    def _get_lib_file_name(file_name):
        """ Get name of a file in the 'lib' sub-directory. """

        return get_embedded_dir(__file__, 'lib').absoluteFilePath(file_name)

    @classmethod
    def _copy_lib_file(cls, file_name, dir_name=None, dst_file_name=None):
        """ Copy a library file to a directory and return the full pathname of
        the copy.  If the directory wasn't specified then copy it to a
        temporary directory.
        """

        # Note that we use the Qt file operations to support the possibility
        # that pyqtdeploy itself has been deployed as a single executable.

        if dir_name is None:
            dir_name = tempfile.gettempdir()

        if dst_file_name is None:
            dst_file_name = file_name
            s_file_name = cls._get_lib_file_name(file_name)
        else:
            s_file_name = file_name

        d_file_name = os.path.join(dir_name, dst_file_name)

        # Make sure the destination doesn't exist.
        QFile.remove(d_file_name)

        if not QFile.copy(s_file_name, QDir.fromNativeSeparators(d_file_name)):
            raise UserException("Unable to copy file {0}".format(file_name))

        return d_file_name

    @staticmethod
    def _create_file(build_dir, filename):
        """ Create a text file in the build directory. """

        return create_file(os.path.join(build_dir, filename))

    def _create_directory(self, dir_name):
        """ Create a directory which may already exist. """

        self._message_handler.verbose_message(
                "Creating directory {0}".format(dir_name))

        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            raise UserException(
                    "Unable to create the '{0}' directory".format(dir_name),
                    str(e))
