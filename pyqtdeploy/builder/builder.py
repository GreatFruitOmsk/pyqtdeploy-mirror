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
import shlex
import shutil
import subprocess
import sys

from PyQt5.QtCore import QDir, QFile, QFileInfo, QTemporaryDir

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

    def build(self, opt, build_dir=None, clean=False):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        # Create a temporary directory which will be removed automatically when
        # this function's objects are garbage collected.
        temp_dir = QTemporaryDir()
        if not temp_dir.isValid():
            raise UserException(
                    "There was an error creating a temporary directory")

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

            build_dir = project.path_from_user(build_dir)

        # Remove any build directory if required.
        if clean:
            native_build_dir = QDir.toNativeSeparators(build_dir)
            self._message_handler.progress_message(
                    "Cleaning {0}".format(native_build_dir))
            shutil.rmtree(native_build_dir, ignore_errors=True)

        # Now start the build.
        self._create_directory(build_dir)

        # The odd naming of the Python source files is to prevent them from
        # being frozen if we deploy ourself.
        freeze = self._copy_lib_file(self._get_lib_file_name('freeze.python'),
                temp_dir.path(), dst_file_name='freeze.py')

        self._write_qmake(build_dir, required_ext, required_libraries, freeze,
                opt)

        # Freeze the bootstrap.
        py_major, py_minor = project.python_target_version
        py_version = (py_major << 16) + (py_minor << 8)

        bootstrap_src = get_embedded_file_for_version(py_version, __file__,
                'lib', 'bootstrap')
        bootstrap = self._copy_lib_file(bootstrap_src, temp_dir.path(),
                dst_file_name='bootstrap.py')
        self._freeze(build_dir + '/frozen_bootstrap.h', bootstrap,
                freeze, opt, name='pyqtdeploy_bootstrap')
        QFile.remove(bootstrap)

        # Freeze any main application script.
        if project.application_script != '':
            self._freeze(build_dir + '/frozen_main.h',
                    project.path_from_user(project.application_script), freeze,
                    opt, name='pyqtdeploy_main')

        # Create the pyqtdeploy module version file.
        version_f = self._create_file(build_dir + '/pyqtdeploy_version.h')
        version_f.write(
                '#define PYQTDEPLOY_HEXVERSION %s\n' % hex(
                        PYQTDEPLOY_HEXVERSION))
        version_f.close()

        # Generate the application resource.
        self._generate_resource(build_dir + '/resources', required_py, freeze,
                opt)

        QFile.remove(freeze)

    def _generate_resource(self, resources_dir, required_py, freeze, opt):
        """ Generate the application resource. """

        project = self._project

        self._create_directory(resources_dir)
        resource_contents = []

        # Handle any application package.
        if project.application_package.name != '':
            fi = QFileInfo(project.path_from_user(
                    project.application_package.name))

            package_src_dir = fi.canonicalFilePath()
            package_name = fi.completeBaseName()

            self._write_package(resource_contents, resources_dir, package_name,
                    project.application_package, package_src_dir, freeze, opt)

        # Handle the Python standard library.
        self._write_stdlib_py(resource_contents, resources_dir, required_py,
                freeze, opt)

        # Handle any additional packages.
        for package in project.other_packages:
            self._write_package(resource_contents, resources_dir, '', package,
                    project.path_from_user(package.name), freeze, opt)

        # Handle the PyQt package.
        if len(project.pyqt_modules) != 0:
            pyqt_subdir = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'
            pyqt_dst_dir = resources_dir + '/' +  pyqt_subdir
            pyqt_src_dir = project.path_from_user(project.python_target_stdlib_dir) + '/site-packages/' + pyqt_subdir

            self._create_directory(pyqt_dst_dir)

            self._freeze(pyqt_dst_dir + '/__init__.pyo',
                    pyqt_src_dir + '/__init__.py', freeze, opt)

            resource_contents.append(pyqt_subdir + '/__init__.pyo')

            # Handle the PyQt.uic package.
            if 'uic' in project.pyqt_modules:
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

                            src = QDir.fromNativeSeparators(src)
                            dst = QDir.fromNativeSeparators(dst)

                            self._freeze(dst, src, freeze, opt)

                            rel_dst = dst[len(resources_dir) + 1:]
                            resource_contents.append(rel_dst)

                shutil.copytree(QDir.toNativeSeparators(pyqt_src_dir + '/uic'),
                        QDir.toNativeSeparators(pyqt_dst_dir + '/uic'),
                        copy_function=copy_freeze)

        # Write the .qrc file.
        f = self._create_file(resources_dir + '/pyqtdeploy.qrc')

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

        stdlib_src_dir = project.path_from_user(
                project.python_target_stdlib_dir)

        # By sorting the names we ensure parents are handled before children.
        for name in sorted(required_py.keys()):
            name_path = name.replace('.', '/')

            if required_py[name].modules is None:
                in_file = name_path + '.py'
                out_file = name_path + '.pyo'
            else:
                in_file = name_path + '/__init__.py'
                out_file = name_path + '/__init__.pyo'
                self._create_directory(resources_dir + '/' + name_path)

            self._freeze(resources_dir + '/' + out_file,
                    stdlib_src_dir + '/' + in_file, freeze, opt)

            resource_contents.append(out_file)

    def _write_qmake(self, build_dir, required_ext, required_libraries, freeze, opt):
        """ Create the .pro file for qmake. """

        project = self._project

        f = self._create_file(build_dir + '/' +
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
        both_config.add('warn_off')

        if not needs_gui or project.application_is_console:
            both_config.add('console')

        f.write('CONFIG += {0}\n'.format(' '.join(both_config)))

        if not project.application_is_bundle:
            f.write('CONFIG -= app_bundle\n')

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

        # Modules can share sources so we need to make sure we don't include
        # them more than once.  We might as well handle the other things in the
        # same way.
        used_sources = {}
        used_defines = {}
        used_includepath = {}
        used_libs = {}
        used_inittab = {}

        # Handle any static PyQt modules.
        if len(project.pyqt_modules) > 0:
            site_packages = project.path_from_user(
                    project.python_target_stdlib_dir) + '/site-packages'
            pyqt_version = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'

            l_libs = []
            for pyqt in self._get_all_pyqt_modules():
                if pyqt != 'uic':
                    self._add_value_for_scope(used_inittab,
                            pyqt_version + '.' + pyqt)

                    lib_name = pyqt
                    if self._get_pyqt_module_metadata(pyqt).needs_suffix:
                        # Qt4's qmake thinks -lQtCore etc. always refer to the
                        # Qt libraries so PyQt4 creates static libraries with a
                        # suffix.
                        lib_name += '_s'

                    l_libs.append('-l' + lib_name)

            # Add the LIBS value for the PyQt modules to the global scope.
            self._add_value_for_scope(used_libs,
                    '-L{0}/{1} {2}'.format(site_packages, pyqt_version,
                            ' '.join(l_libs)))

            # Add the implicit sip module.
            self._add_value_for_scope(used_inittab, 'sip')
            self._add_value_for_scope(used_libs,
                    '-L{0} -lsip'.format(site_packages))

        # Handle any other extension modules.
        for other_em in project.other_extension_modules:
            scoped_values = self._parse_scoped_values(other_em.libs)

            for scope, values in scoped_values.items():
                self._add_value_for_scope(used_inittab, other_em.name, scope)
                self._add_value_set_for_scope(used_libs, values, scope)

        # Configure the target Python interpreter.
        if project.python_target_include_dir != '':
            self._add_value_for_scope(used_includepath,
                    project.path_from_user(project.python_target_include_dir))

        if project.python_target_library != '':
            fi = QFileInfo(project.path_from_user(
                    project.python_target_library))

            lib_dir = fi.absolutePath()
            lib = fi.completeBaseName()

            # This is smart enough to translate the Python library as a UNIX .a
            # file to what Windows needs.
            if lib.startswith('lib'):
                lib = lib[3:]

            if '.' in lib:
                self._add_value_for_scope(used_libs,
                        '-L{0} -l{1}\n'.format(
                                lib_dir, lib.replace('.', '')),
                        'win32')
                self._add_value_for_scope(used_libs,
                        '-L{0} -l{1}\n'.format(lib_dir, lib), '!win32')
            else:
                self._add_value_for_scope(used_libs,
                        '-L{0} -l{1}\n'.format(lib_dir, lib))

        # Handle any standard library extension modules.
        if len(required_ext) != 0:
            source_dir = project.path_from_user(project.python_source_dir)

            self._add_value_for_scope(used_includepath,
                    source_dir + '/Modules')

            for name, module in required_ext.items():
                self._add_value_for_scope(used_inittab, name, module.scope);

                for source in module.source:
                    source = self._python_source_file(source_dir, source)
                    self._add_scoped_value(used_sources, source,
                            default_scope=module.scope)

                if module.defines is not None:
                    for define in module.defines:
                        self._add_scoped_value(used_defines, define,
                                default_scope=module.scope)

                if module.includepath is not None:
                    for includepath in module.includepath:
                        includepath = self._python_source_file(source_dir,
                                includepath)
                        self._add_scoped_value(used_includepath, includepath,
                                default_scope=module.scope)

                if module.libs is not None:
                    for lib in module.libs:
                        self._add_scoped_value(used_libs, lib,
                                default_scope=module.scope)

        # Handle any required external libraries.
        for required_lib in required_libraries:
            for xlib in project.external_libraries:
                if xlib.name == required_lib:
                    if xlib.defines != '':
                        self._add_parsed_scoped_values(used_defines,
                                xlib.defines, False)

                    if xlib.includepath != '':
                        self._add_parsed_scoped_values(used_includepath,
                                xlib.includepath, True)

                    if xlib.libs != '':
                        self._add_parsed_scoped_values(used_libs, xlib.libs,
                                False)

                    break
            else:
                for xlib in external_libraries_metadata:
                    if xlib.name == required_lib:
                        for lib in xlib.libs.split():
                            self._add_value_for_scope(used_libs, lib)

                        break

        # Specify the resource file.
        f.write('\n')
        f.write('RESOURCES = resources/pyqtdeploy.qrc\n')

        # Specify the source and header files.
        f.write('\n')

        f.write('SOURCES = pyqtdeploy_main.cpp pyqtdeploy_start.cpp pdytools_module.cpp\n')
        self._write_main(build_dir, used_inittab)
        self._copy_lib_file('pyqtdeploy_start.cpp', build_dir)
        self._copy_lib_file('pdytools_module.cpp', build_dir)

        headers = 'HEADERS = pyqtdeploy_version.h frozen_bootstrap.h'
        if project.application_script != '':
            f.write('DEFINES += PYQTDEPLOY_FROZEN_MAIN\n')
            headers += ' frozen_main.h'

        f.write(headers)
        f.write('\n')

        # Get the set of all scopes used.
        used_scopes = set(used_sources.keys())
        used_scopes.update(used_defines.keys())
        used_scopes.update(used_includepath.keys())
        used_scopes.update(used_libs.keys())

        # Write out grouped by scope.
        for scope in used_scopes:
            f.write('\n')

            if scope != '':
                prefix = '    '
                f.write('%s {\n' % scope)
            else:
                prefix = ''

            for defines in used_defines.get(scope, ()):
                f.write('{0}DEFINES += {1}\n'.format(prefix, defines))

            for includepath in used_includepath.get(scope, ()):
                f.write('{0}INCLUDEPATH += {1}\n'.format(prefix, includepath))

            for lib in used_libs.get(scope, ()):
                f.write('{0}LIBS += {1}\n'.format(prefix, lib))

            for source in used_sources.get(scope, ()):
                f.write('{0}SOURCES += {1}\n'.format(prefix, source))

            if scope != '':
                f.write('}\n')

        # Add the platform specific stuff.
        platforms = read_embedded_file(
                self._get_lib_file_name('platforms.pro'))

        f.write('\n')
        f.write(platforms.data().decode('latin1'))

        # All done.
        f.close()

    @staticmethod
    def _python_source_file(py_source_dir, rel_path):
        """ Return the canonical name of a file in the Python source tree
        relative to the Modules directory.
        """

        return QFileInfo(py_source_dir + '/Modules/' + rel_path).canonicalFilePath()

    def _add_parsed_scoped_values(self, used_values, raw, isfilename):
        """ Parse a string of space separated possible scoped values and add
        them to a dict of used values indexed by scope.  The values are
        optionally treated as filenames where they are converted to absolute
        filenames with UNIX separators and have environment variables expanded.
        """

        for scope, value_set in self._parse_scoped_values(raw, isfilename):
            self._add_value_set_for_scope(used_values, value_set, scope)

    def _parse_scoped_values(self, raw, isfilename):
        """ Parse a string of space separated possible scoped values and return
        a dict, keyed by scope, of the values for each scope.
        """

        scoped_value_sets = {}

        for scoped_value in shlex.split(raw):
            self._add_scoped_value(scoped_value_sets, scoped_value,
                    isfilename=isfilename)

        return scoped_value_sets

    def _add_scoped_value(self, used_values, scoped_value, isfilename=False, default_scope=''):
        """ Add an optionally scoped value to a dict of used values indexed by
        scope.
        """

        # Isolate the scope and value.
        parts = scoped_value.split('#', maxsplit=1)
        if len(parts) == 2:
            scope, value = parts
        else:
            scope = default_scope
            value = parts[0]

        # Convert potential filenames.
        if isfilename:
            value = self.project.path_from_user(value)
        elif value.startswith('-L'):
            value = '-L' + self.project.path_from_user(value[2:])

        self._add_value_for_scope(used_values, value, scope)

    @staticmethod
    def _add_value_for_scope(used_values, value, scope=''):
        """ Add a value to the set of used values for a scope. """

        used_values.setdefault(scope, set()).add(value)

    @staticmethod
    def _add_value_set_for_scope(used_values, values, scope=''):
        """ Add a set of values to the set of used values for a scope. """

        used_values.setdefault(scope, set()).update(values)

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

    def _write_package(self, resource_contents, resources_dir, resource, package, src_dir, freeze, opt):
        """ Write the contents of a single package and return the list of files
        written relative to the resources directory.
        """

        if resource == '':
            dst_dir = resources_dir
            dir_stack = []
        else:
            dst_dir = resources_dir + '/' + resource
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
                        dst_dir + '/' + content.name,
                        src_dir + '/' + content.name, dir_stack, freeze, opt,
                        resource_contents)

                dir_stack.pop()
            else:
                freeze_file = True
                src_file = content.name
                src_path = src_dir + '/' + src_file

                if src_file.endswith('.py'):
                    dst_file = src_file[:-3] + '.pyo'
                elif src_file.endswith('.pyw'):
                    dst_file = src_file[:-4] + '.pyo'
                else:
                    # Just copy the file.
                    dst_file = src_file
                    freeze_file = False

                dst_path = dst_dir + '/' + dst_file

                if freeze_file:
                    self._freeze(dst_path, src_path, freeze, opt)
                else:
                    src_path = QDir.toNativeSeparators(src_path)
                    dst_path = QDir.toNativeSeparators(dst_path)

                    try:
                        shutil.copyfile(src_path, dst_path)
                    except FileNotFoundError:
                        raise UserException(
                                "{0} does not seem to exist".format(src_path))

                file_path = list(dir_stack)
                file_path.append(dst_file)
                resource_contents.append('/'.join(file_path))

    def _write_main(self, build_dir, inittab):
        """ Create the application specific pyqtdeploy_main.cpp file. """

        project = self._project

        f = self._create_file(build_dir + '/pyqtdeploy_main.cpp')

        f.write('''#include <Python.h>
#include <QtGlobal>

''')

        if len(inittab) > 0:
            c_inittab = 'extension_modules'

            f.write('#if PY_MAJOR_VERSION >= 3\n')
            self._write_inittab(f, inittab, c_inittab, py3=True)
            f.write('#else\n')
            self._write_inittab(f, inittab, c_inittab, py3=False)
            f.write('#endif\n\n')
        else:
            c_inittab = 'NULL'

        sys_path = project.sys_path

        if sys_path != '':
            f.write('static const char *path_dirs[] = {\n')

            for dir_name in shlex.split(sys_path):
                f.write('    "{0}",\n'.format(dir_name.replace('"','\\"')))

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
''' % (c_inittab, main_module, entry_point, path_dirs))

        f.close()

    @classmethod
    def _write_inittab(cls, f, inittab, c_inittab, py3):
        """ Write the Python version specific extension module inittab. """

        if py3:
            init_type = 'PyObject *'
            init_prefix = 'PyInit_'
        else:
            init_type = 'void '
            init_prefix = 'init'

        for scope, names in inittab.items():
            if scope != '':
                cls._write_scope_guard(f, scope)

            for name in names:
                base_name = name.split('.')[-1]

                f.write('extern "C" %s%s%s(void);\n' % (init_type, init_prefix,
                        base_name))

            if scope != '':
                f.write('#endif\n')

        f.write('''
static struct _inittab %s[] = {
''' % c_inittab)

        for scope, names in inittab.items():
            if scope != '':
                cls._write_scope_guard(f, scope)

            for name in names:
                base_name = name.split('.')[-1]

                f.write('    {"%s", %s%s},\n' % (name, init_prefix, base_name))

            if scope != '':
                f.write('#endif\n')

        f.write('''    {NULL, NULL}
};
''')

    # The map of scopes to pre-processor symbols.
    _guards = {
        'macx':     'Q_OS_MAC',
        'win32':    'Q_OS_WIN',
    }

    @classmethod
    def _write_scope_guard(cls, f, scope):
        """ Write the C pre-processor guard for a scope. """

        if scope[0] == '!':
            inv = '!'
            scope = scope[1:]
        else:
            inv = ''

        f.write('#if {0}defined({1})\n'.format(inv, cls._guards[scope]))

    def _freeze(self, out_file, in_file, freeze, opt, name=None):
        """ Freeze a Python source file to a C header file or a data file. """

        # Note that we assume a relative filename is on PATH rather than being
        # relative to the project file.
        interp = os.path.expandvars(self._project.python_host_interpreter)

        # On Windows the interpreter name is simply 'python'.  So in order to
        # make the .pdy file more portable we strip any trailing version
        # number.
        if sys.platform == 'win32':
            for i in range(len(interp) - 1, -1, -1):
                if interp[i] not in '.0123456789':
                    interp = interp[:i + 1]
                    break

        argv = [QDir.toNativeSeparators(interp)]

        if opt == 2:
            argv.append('-OO')
        elif opt == 1:
            argv.append('-O')

        argv.append(freeze)
        
        if name is not None:
            argv.append('--name')
            argv.append(name)
            argv.append('--as-c')
        else:
            argv.append('--as-data')

        out_file = QDir.toNativeSeparators(out_file)
        in_file = QDir.toNativeSeparators(in_file)

        argv.append(out_file)
        argv.append(in_file)

        self._message_handler.progress_message("Freezing {0}".format(in_file))

        self.run(argv, "Unable to freeze {0}".format(in_file))

    def run(self, argv, error_message, in_build_dir=False):
        """ Execute a command and capture the output. """

        if in_build_dir:
            project = self._project

            saved_cwd = os.getcwd()
            build_dir = project.path_from_user(project.build_dir)
            build_dir = QDir.toNativeSeparators(build_dir)
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
    def _copy_lib_file(cls, file_name, dir_name, dst_file_name=None):
        """ Copy a library file to a directory and return the full pathname of
        the copy.
        """

        # Note that we use the Qt file operations to support the possibility
        # that pyqtdeploy itself has been deployed as a single executable.

        if dst_file_name is None:
            dst_file_name = file_name
            s_file_name = cls._get_lib_file_name(file_name)
        else:
            s_file_name = file_name

        d_file_name = dir_name + '/' +  dst_file_name

        # Make sure the destination doesn't exist.
        QFile.remove(d_file_name)

        if not QFile.copy(s_file_name, d_file_name):
            raise UserException("Unable to copy file {0}".format(file_name))

        return d_file_name

    @staticmethod
    def _create_file(file_name):
        """ Create a text file in the build directory. """

        return create_file(QDir.toNativeSeparators(file_name))

    def _create_directory(self, dir_name):
        """ Create a directory which may already exist. """

        dir_name = QDir.toNativeSeparators(dir_name)

        self._message_handler.verbose_message(
                "Creating directory {0}".format(dir_name))

        try:
            os.makedirs(dir_name, exist_ok=True)
        except Exception as e:
            raise UserException(
                    "Unable to create the '{0}' directory".format(dir_name),
                    str(e))
