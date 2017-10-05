# Copyright (c) 2017, Riverbank Computing Limited
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


import csv
import os
import shlex
import shutil
import sys

from PyQt5.QtCore import (QByteArray, QCoreApplication, QDir, QFile,
        QFileDevice, QFileInfo, QProcess, QTemporaryDir, QTextCodec)

from ..file_utilities import (create_file, get_embedded_dir,
        get_embedded_file_for_version, read_embedded_file)
from ..hosts import Host
from ..metadata import (external_libraries_metadata, get_python_metadata,
        pyqt4_metadata, pyqt5_metadata)
from ..project import QrcDirectory
from ..targets import TargetArch, TargetPlatform
from ..user_exception import UserException
from ..version import PYQTDEPLOY_HEXVERSION
from ..windows import get_python_install_path


# The list of all target platform names.
TARGET_PLATFORM_NAMES = [p.name for p in TargetPlatform.get_platforms()]


class Builder():
    """ The builder for a project. """

    def __init__(self, project, timeout, message_handler):
        """ Initialise the builder for a project. """

        super().__init__()

        self._project = project
        self._timeout = timeout * 1000 if timeout > 0 else -1
        self._message_handler = message_handler

        self._host = Host.factory()

    def build(self, opt, nr_resources, clean=True, build_dir=None, include_dir=None, interpreter=None, python_library=None, source_dir=None, standard_library_dir=None):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        py_major, py_minor, py_patch = project.python_target_version

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
        if len(required_ext) != 0:
            if source_dir is None:
                if project.python_source_dir == '':
                    raise UserException(
                            "The name of the Python source directory has not "
                            "been specified")

                source_dir = project.path_from_user(project.python_source_dir)

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

        # Get other directories from the project that may be overridden.
        if include_dir is None:
            include_dir = project.path_from_user(
                    project.python_target_include_dir)

        if interpreter is None:
            if project.python_host_interpreter != '':
                # Note that we assume a relative filename is on PATH rather
                # than being relative to the project file.
                interpreter = project.expandvars(
                        project.python_host_interpreter)
            elif sys.platform == 'win32':
                # TODO: This doesn't handle 32-bit Python v3.5 and later.
                interpreter = get_python_install_path(
                        '{0}.{1}'.format(py_major, py_minor)) + 'python'
            else:
                interpreter = 'python{0}.{1}'.format(py_major, py_minor)

        if python_library is None:
            python_library = project.path_from_user(
                    project.python_target_library)

        if standard_library_dir is None:
            standard_library_dir = project.path_from_user(
                    project.python_target_stdlib_dir)

        # Set the name of the build directory.
        if build_dir is None:
            build_dir = project.build_dir
            if build_dir == '':
                build_dir = '.'

            build_dir = project.path_from_user(build_dir)

        self._build_dir = build_dir

        # Remove any build directory if required.
        if clean:
            native_build_dir = QDir.toNativeSeparators(build_dir)
            self._message_handler.progress_message(
                    "Cleaning {0}".format(native_build_dir))
            shutil.rmtree(native_build_dir, ignore_errors=True)

        # Now start the build.
        self._create_directory(build_dir)

        # Create the job file and writer.
        job_filename = QDir.toNativeSeparators(temp_dir.path() + '/jobs.csv')
        job_file = open(job_filename, 'w', newline='')
        job_writer = csv.writer(job_file)

        # Freeze the bootstrap.  Note that from Python v3.5 the modified part
        # is in _bootstrap_external.py and _bootstrap.py is unchanged from the
        # original source.  We continue to use a local copy of _bootstrap.py
        # as it still needs to be frozen and we don't want to depend on an
        # external source.
        py_version = (py_major << 16) + (py_minor << 8) + py_patch

        self._freeze_bootstrap('bootstrap', py_version, build_dir, temp_dir,
                job_writer)

        if py_version >= 0x030500:
            self._freeze_bootstrap('bootstrap_external', py_version, build_dir,
                    temp_dir, job_writer)

        # Freeze any main application script.
        if project.application_script != '':
            self._freeze(job_writer, build_dir + '/frozen_main.h',
                    project.path_from_user(project.application_script),
                    'pyqtdeploy_main', as_c=True)

        # Create the pyqtdeploy module version file.
        version_f = self._create_file(build_dir + '/pyqtdeploy_version.h')
        version_f.write(
                '#define PYQTDEPLOY_HEXVERSION %s\n' % hex(
                        PYQTDEPLOY_HEXVERSION))
        version_f.close()

        # Generate the application resource.
        resource_names = self._generate_resource(build_dir + '/resources',
                required_py, standard_library_dir, job_writer, nr_resources)

        # Write the .pro file.
        self._write_qmake(py_version, required_ext, required_libraries,
                include_dir, python_library, standard_library_dir, job_writer,
                opt, resource_names)

        # Run the freeze jobs.
        job_file.close()

        # The odd naming of Python source files is to prevent them from being
        # frozen if we deploy ourself.
        freeze = self._copy_lib_file(self._get_lib_file_name('freeze.python'),
                temp_dir.path(), dst_file_name='freeze.py')

        self._run_freeze(freeze, interpreter, job_filename, opt)

    def _freeze_bootstrap(self, name, py_version, build_dir, temp_dir, job_writer):
        """ Freeze a version dependent bootstrap script. """

        bootstrap_src = get_embedded_file_for_version(py_version, __file__,
                'lib', name)
        bootstrap = self._copy_lib_file(bootstrap_src, temp_dir.path(),
                dst_file_name=name + '.py')
        self._freeze(job_writer, build_dir + '/frozen_' + name + '.h',
                bootstrap, 'pyqtdeploy_' + name, as_c=True)

    def _generate_resource(self, resources_dir, required_py, standard_library_dir, job_writer, nr_resources):
        """ Generate the application resource. """

        project = self._project

        self._create_directory(resources_dir)
        resource_contents = []

        # Handle any application package.
        if project.application_package.name is not None:
            fi = QFileInfo(project.path_from_user(
                    project.application_package.name))

            package_src_dir = fi.canonicalFilePath()

            package_name = project.application_package.name
            if package_name != '':
                package_name = fi.completeBaseName()

            self._write_package(resource_contents, resources_dir, package_name,
                    project.application_package, package_src_dir, job_writer)

        # Handle the Python standard library.
        self._write_stdlib_py(resource_contents, resources_dir, required_py,
                standard_library_dir, job_writer)

        # Handle any additional packages.
        for package in project.other_packages:
            self._write_package(resource_contents, resources_dir, '', package,
                    project.path_from_user(package.name), job_writer)

        # Handle the PyQt package.
        if len(project.pyqt_modules) != 0:
            pyqt_subdir = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'
            pyqt_dst_dir = resources_dir + '/' +  pyqt_subdir
            pyqt_src_dir = standard_library_dir + '/site-packages/' + pyqt_subdir

            self._create_directory(pyqt_dst_dir)

            self._freeze(job_writer, pyqt_dst_dir + '/__init__.pyo',
                    pyqt_src_dir + '/__init__.py',
                    pyqt_subdir + '/__init__.py')

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
                            src = QDir.fromNativeSeparators(src)
                            dst = QDir.fromNativeSeparators(dst)
                            rel_dst = dst[len(resources_dir) + 1:] + 'o'

                            self._freeze(job_writer, dst + 'o', src, rel_dst)

                            resource_contents.append(rel_dst)

                shutil.copytree(QDir.toNativeSeparators(pyqt_src_dir + '/uic'),
                        QDir.toNativeSeparators(pyqt_dst_dir + '/uic'),
                        copy_function=copy_freeze)

        # Write the .qrc files.
        if nr_resources == 1:
            resource_names = [self._write_resource(resources_dir,
                    resource_contents)]
        else:
            resource_names = []

            nr_files = len(resource_contents)

            if nr_resources > nr_files:
                nr_resources = nr_files

            per_resource = (nr_files + nr_resources - 1) // nr_resources
            start = 0

            for r in range(nr_resources):
                end = start + per_resource
                if end > nr_files:
                    end = nr_files

                resource_names.append(
                        self._write_resource(resources_dir,
                                resource_contents[start:end], r))
                start += per_resource

        return resource_names

    def _write_resource(self, resources_dir, resource_contents, nr=-1):
        """ Write a single resource file and return its basename. """

        suffix = '' if nr < 0 else str(nr)
        basename = 'pyqtdeploy{0}.qrc'.format(suffix)

        f = self._create_file(resources_dir + '/' + basename)

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

        return basename

    def _write_stdlib_py(self, resource_contents, resources_dir, required_py, standard_library_dir, job_writer):
        """ Write the required parts of the Python standard library that are
        implemented in Python.
        """

        project = self._project

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

            self._freeze(job_writer, resources_dir + '/' + out_file,
                    standard_library_dir + '/' + in_file, in_file)

            resource_contents.append(out_file)

    # The map of non-C/C++ source extensions to qmake variable.
    _source_extensions = {
        '.asm':     'MASMSOURCES',
        '.h':       'HEADERS',
        '.java':    'JAVASOURCES',
        '.l':       'LEXSOURCES',
        '.pyx':     'CYTHONSOURCES',
        '.y':       'YACCSOURCES',
    }

    def _write_qmake(self, py_version, required_ext, required_libraries, include_dir, python_library, standard_library_dir, job_writer, opt, resource_names):
        """ Create the .pro file for qmake. """

        project = self._project

        f = self._create_file(self._build_dir + '/' +
                project.get_executable_basename() + '.pro')

        f.write('TEMPLATE = app\n')

        # Configure the CONFIG and QT values that are project dependent.
        needs_cpp11 = False
        needs_gui = False
        qmake_qt4 = set()
        qmake_config4 = set()
        qmake_qt5 = set()
        qmake_config5 = set()

        for pyqt_m in project.pyqt_modules:
            metadata = self._get_pyqt_module_metadata(pyqt_m)

            if metadata.cpp11:
                needs_cpp11 = True

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

        both_config.add('warn_off')

        if project.application_is_console or not needs_gui:
            both_config.add('console')

        if needs_cpp11:
            both_config.add('c++11')

        f.write('\n')
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
        used_qt = {}
        used_config = {}
        used_sources = {}
        used_defines = {}
        used_includepath = {}
        used_libs = {}
        used_inittab = {}
        used_dlls = {}

        if 'SYSROOT' in os.environ:
            self._add_value_for_targets(used_includepath,
                    os.path.expandvars('$SYSROOT/include'))
            self._add_value_for_targets(used_libs,
                    os.path.expandvars('-L$SYSROOT/lib'))

        # Handle any static PyQt modules.
        if len(project.pyqt_modules) > 0:
            site_packages = standard_library_dir + '/site-packages'
            pyqt_version = 'PyQt5' if project.application_is_pyqt5 else 'PyQt4'

            l_libs = []
            for pyqt in self._get_all_pyqt_modules():
                # The sip module is always needed (implicitly or explicitly) if
                # we have got this far.  We handle it separately as it is in a
                # different directory.
                if pyqt == 'sip':
                    continue

                # The uic module is pure Python.
                if pyqt == 'uic':
                    continue

                self._add_value_for_targets(used_inittab,
                        pyqt_version + '.' + pyqt)

                lib_name = pyqt
                if self._get_pyqt_module_metadata(pyqt).needs_suffix:
                    # Qt4's qmake thinks -lQtCore etc. always refer to the Qt
                    # libraries so PyQt4 creates static libraries with a
                    # suffix.
                    lib_name += '_s'

                l_libs.append('-l' + lib_name)

            # Add the LIBS value for any PyQt modules to all targets.
            if len(l_libs) > 0:
                self._add_value_for_targets(used_libs,
                        '-L' + site_packages + '/' + pyqt_version)

                for l_lib in l_libs:
                    self._add_value_for_targets(used_libs, l_lib)

            # Add the sip module.
            self._add_value_for_targets(used_inittab, 'sip')
            self._add_value_for_targets(used_libs, '-L' + site_packages)
            self._add_value_for_targets(used_libs, '-lsip')

        # Handle any other extension modules.
        for other_em in project.other_extension_modules:
            # If the name is scoped then the targets are the outer scopes for
            # the remaining values.
            targets, value = self._get_targets_and_value(other_em.name)
            self._add_value_for_targets(used_inittab, value, targets)

            if other_em.qt != '':
                self._add_compound_scoped_values(used_qt, other_em.qt, False)

            if other_em.config != '':
                self._add_compound_scoped_values(used_config, other_em.config,
                        False)

            if other_em.sources != '':
                self._add_compound_scoped_values(used_sources,
                        other_em.sources, True)

            if other_em.defines != '':
                self._add_compound_scoped_values(used_defines,
                        other_em.defines, False)

            if other_em.includepath != '':
                self._add_compound_scoped_values(used_includepath,
                        other_em.includepath, True)

            if other_em.libs != '':
                self._add_compound_scoped_values(used_libs, other_em.libs,
                        False)

        # Configure the target Python interpreter.
        if include_dir != '':
            self._add_value_for_targets(used_includepath, include_dir)

        if python_library != '':
            fi = QFileInfo(python_library)

            py_lib_dir = fi.absolutePath()
            lib = fi.completeBaseName()

            # This is smart enough to translate the Python library as a UNIX .a
            # file to what Windows needs.
            if lib.startswith('lib'):
                lib = lib[3:]

            if '.' in lib:
                self._add_value_for_targets(used_libs,
                        '-l' + lib.replace('.', ''),
                        self._resolve_target_expression('win'))
                self._add_value_for_targets(used_libs, '-l' + lib,
                        self._resolve_target_expression('!win'))
            else:
                self._add_value_for_targets(used_libs, '-l' + lib)

            self._add_value_for_targets(used_libs, '-L' + py_lib_dir)
        else:
            py_lib_dir = None

        # Handle any standard library extension modules.
        if len(required_ext) != 0:
            source_dir = project.path_from_user(project.python_source_dir)
            source_targets = set()

            for name, module in required_ext.items():
                # Get the list of all applicable targets.
                module_targets = self._stdlib_extmod_targets(module.target)

                if len(module_targets) == 0:
                    # The module is specific to a platform for which we are
                    # using the python.org Python libraries so ignore it
                    # completely.
                    continue

                self._add_value_for_targets(used_inittab, name, module_targets)

                for source in module.source:
                    targets, source = self._get_targets_and_value(source,
                            module_targets)
                    source = self._python_source_file(source_dir, source)
                    self._add_value_for_targets(used_sources, source, targets)

                    source_targets.update(targets)

                if module.defines is not None:
                    for define in module.defines:
                        targets, define = self._get_targets_and_value(define,
                                module_targets)
                        self._add_value_for_targets(used_defines, define,
                                targets)

                if module.includepath is not None:
                    for includepath in module.includepath:
                        targets, includepath = self._get_targets_and_value(
                                includepath, module_targets)
                        includepath = self._python_source_file(source_dir,
                                includepath)
                        self._add_value_for_targets(used_includepath,
                                includepath, targets)

                if module.libs is not None:
                    for lib in module.libs:
                        targets, lib = self._get_targets_and_value(lib,
                                module_targets)
                        self._add_value_for_targets(used_libs, lib, targets)

                if module.pyd is not None:
                    self._add_value_for_targets(used_dlls, module, ['win'])

            self._add_value_for_targets(used_includepath,
                    source_dir + '/Modules', source_targets)

            if 'win' not in project.python_use_platform:
                self._add_value_for_targets(used_includepath,
                        source_dir + '/PC', ['win'])

        # Handle any required external libraries platform by platform.
        for platform in TargetPlatform.get_platforms():
            external_libs = project.external_libraries.get(platform.name, [])

            for required_lib in required_libraries:
                for xlib in external_libs:
                    if xlib.name == required_lib:
                        # Check the library is not disabled for this platform.
                        if xlib.libs != '':
                            if xlib.defines != '':
                                self._add_compound_scoped_values(used_defines,
                                        xlib.defines, False, platform.name)

                            if xlib.includepath != '':
                                self._add_compound_scoped_values(
                                        used_includepath, xlib.includepath,
                                        True, platform.name)

                            self._add_compound_scoped_values(used_libs,
                                    xlib.libs, False, platform.name)

                    break
                else:
                    # Use the defaults.
                    for xlib in external_libraries_metadata:
                        if xlib.name == required_lib:
                            targets = self._stdlib_extmod_targets()

                            if len(targets) != 0:
                                for lib in xlib.libs.split():
                                    self._add_value_for_targets(used_libs, lib,
                                            targets)

                            break

        # Specify any project-specific configuration.
        if used_qt:
            f.write('\n')
            self._write_used_values(f, used_qt, 'QT')

        if used_config:
            f.write('\n')
            self._write_used_values(f, used_config, 'CONFIG')

        # Specify the resource files.
        f.write('\n')
        f.write('RESOURCES = \\\n')
        f.write(' \\\n'.join(['    resources/{0}'.format(n) for n in resource_names]))
        f.write('\n')

        # Specify the defines.
        defines = []
        headers = ['pyqtdeploy_version.h', 'frozen_bootstrap.h']

        if py_version >= 0x030500:
            headers.append('frozen_bootstrap_external.h')

        if project.application_script != '':
            defines.append('PYQTDEPLOY_FROZEN_MAIN')
            headers.append('frozen_main.h')

        if opt:
            defines.append('PYQTDEPLOY_OPTIMIZED')

        if defines or used_defines:
            f.write('\n')

            if defines:
                f.write('DEFINES += {0}\n'.format(' '.join(defines)))

            self._write_used_values(f, used_defines, 'DEFINES')

        # Specify the include paths.
        if used_includepath:
            f.write('\n')
            self._write_used_values(f, used_includepath, 'INCLUDEPATH')

        # Specify the source files and header files.
        f.write('\n')
        f.write('SOURCES = pyqtdeploy_main.cpp pyqtdeploy_start.cpp pdytools_module.cpp\n')
        self._write_used_values(f, used_sources, 'SOURCES')
        self._write_main(self._optimised(used_inittab))
        self._copy_lib_file('pyqtdeploy_start.cpp', self._build_dir)
        self._copy_lib_file('pdytools_module.cpp', self._build_dir)

        f.write('\n')
        f.write('HEADERS = {0}\n'.format(' '.join(headers)))

        # Specify the libraries.
        if used_libs:
            f.write('\n')
            self._write_used_values(f, used_libs, 'LIBS')

        # If we are using the platform Python on Windows then copy in the
        # required DLLs if they can be found.
        if 'win' in project.python_use_platform and used_dlls and py_lib_dir is not None:
            self._copy_windows_dlls(py_version, py_lib_dir, used_dlls['win'],
                    f)

        # Add the project independent post-configuration stuff.
        self._write_embedded_lib_file('post_configuration.pro', f)

        # Add any application specific stuff.
        qmake_configuration = project.qmake_configuration.strip()

        if qmake_configuration != '':
            f.write('\n' + qmake_configuration + '\n')

        # All done.
        f.close()

    @classmethod
    def _write_used_values(cls, f, used_values, name):
        """ Write a set of used values to a .pro file. """

        for targets, values in cls._optimised(used_values):
            if targets:
                indent = '    '

                if targets[0][0] == '!':
                    f.write('!%s {\n' % cls._qmake_scope_for_target(
                            targets[0][1:]))
                else:
                    f.write('%s {\n' % ':'.join(
                            [cls._qmake_scope_for_target(t)
                                    for t in targets]))
            else:
                indent = ''

            for value in values:
                qmake_var = name

                if qmake_var == 'SOURCES':
                    for ext, var in cls._source_extensions.items():
                        if value.endswith(ext):
                            qmake_var = var
                            break

                elif qmake_var == 'LIBS':
                    # A (strictly unnecessary) bit of pretty printing.
                    if value.startswith('"-framework') and value.endswith('"'):
                        value = value[1:-1]

                f.write('{0}{1} += {2}\n'.format(indent, qmake_var, value))

            if targets:
                f.write('}\n')

    def _copy_windows_dlls(self, py_version, py_lib_dir, modules, f):
        """ Generate additional qmake commands to install additional Windows
        DLLs so that the application will be able to run.
        """

        py_major = py_version >> 16
        py_minor = (py_version >> 8) & 0xff

        dlls = ['python{0}{1}.dll'.format(py_major, py_minor)]

        if py_version >= 0x030500:
            dlls.append('vcruntime140.dll')

        for module in modules:
            dlls.append(module.pyd)

            if module.dlls is not None:
                dlls.extend(module.dlls)

        f.write('\nwin32 {')

        for name in dlls:
            f.write('\n')
            f.write('    PDY_DLL = %s/DLLs%d.%d/%s\n' % (py_lib_dir, py_major, py_minor, name))
            f.write('    exists($$PDY_DLL) {\n')
            f.write('        CONFIG(debug, debug|release) {\n')
            f.write('            QMAKE_POST_LINK += $(COPY_FILE) $$shell_path($$PDY_DLL) $$shell_path($$OUT_PWD/debug) &\n')
            f.write('        } else {\n')
            f.write('            QMAKE_POST_LINK += $(COPY_FILE) $$shell_path($$PDY_DLL) $$shell_path($$OUT_PWD/release) &\n')
            f.write('        }\n')
            f.write('    }\n')

        f.write('}\n')

    def _write_embedded_lib_file(self, file_name, f):
        """ Write an embedded file from the lib directory. """

        contents = read_embedded_file(self._get_lib_file_name(file_name))

        f.write('\n')
        f.write(contents.data().decode('latin1'))

    def _stdlib_extmod_targets(self, module_target=None):
        """ Return the list of targets for any extension module included in the
        standard library or, optionally, for one particular module.
        """

        # Get the list of all applicable targets.
        if module_target:
            targets = self._resolve_target_expression(module_target)
        else:
            targets = list(TARGET_PLATFORM_NAMES)

        # Remove those targets for which we are using the python.org Python
        # libraries.
        for plat_name in self._project.python_use_platform:
            try:
                targets.remove(plat_name)
            except ValueError:
                pass

        return targets

    @staticmethod
    def _python_source_file(py_source_dir, rel_path):
        """ Return the absolute name of a file in the Python source tree
        relative to the Modules directory.
        """

        file_path = py_source_dir + '/Modules/' + rel_path

        return QFileInfo(file_path).absoluteFilePath()

    def _add_compound_scoped_values(self, used_values, raw, isfilename, target=None):
        """ Parse a string of space separated possible scoped values and add
        them to a dict of used values indexed by target.  The values are
        optionally treated as filenames where they are converted to absolute
        filenames with UNIX separators and have environment variables expanded.
        """

        project = self._project

        targets = TARGET_PLATFORM_NAMES if target is None else [target]

        scoped_value_sets = {}

        for scoped_value in self._split_quotes(raw):
            value_targets, value = self._get_targets_and_value(scoped_value,
                    targets)

            # Convert potential filenames.
            if isfilename:
                value = project.path_from_user(value)
            elif value.startswith('-L'):
                value = '-L' + project.path_from_user(value[2:])

            self._add_value_for_targets(scoped_value_sets, value,
                    value_targets)

        for target, values in scoped_value_sets.items():
            used_values.setdefault(target, set()).update(values)

    @staticmethod
    def _split_quotes(s):
        """ A generator for a splitting a string allowing for quoted spaces.
        """

        s = s.lstrip()

        while s != '':
            quote_stack = []
            i = 0

            for ch in s:
                if ch in '\'"':
                    if len(quote_stack) == 0 or quote_stack[-1] != ch:
                        quote_stack.append(ch)
                    else:
                        quote_stack.pop()
                elif ch == ' ':
                    if len(quote_stack) == 0:
                        break

                i += 1

            yield s[:i]

            s = s[i:].lstrip()

    @classmethod
    def _get_targets_and_value(cls, scoped_value, targets=None):
        """ Return the 2-tuple of targets and value from a (possibly) scoped
        value.  If the returning list of targets is empty then the value is not
        valid.
        """

        if targets is None:
            targets = TARGET_PLATFORM_NAMES

        parts = scoped_value.split('#', maxsplit=1)
        if len(parts) == 2:
            target_scope, value = parts
            target_scopes = cls._resolve_target_expression(target_scope)

            # The final targets is the intersection of the current targets and
            # those defined by the scope while taking architectures into
            # account.
            final_targets = []
            for target in target_scopes:
                if target in targets:
                    final_targets.append(target)
                elif TargetPlatform.find_platform(target) is None:
                    arch = TargetArch.find_arch(target)
                    if arch is None:
                        raise UserException(
                                "'{0}' is not the name of a target architecture or platform".format(target))

                    if arch.platform.name in targets:
                        final_targets.append(arch.name)

            targets = final_targets
        else:
            # The value is unscoped.
            value = scoped_value

        return targets, value

    @staticmethod
    def _add_value_for_targets(used_values, value, targets=None):
        """ Add a value to the set of used values for a set of targets. """

        # Get the list of relevant targets.
        if targets is None:
            targets = TARGET_PLATFORM_NAMES

        # Add the value for each relevant target.
        for target in targets:
            used_values.setdefault(target, set()).add(value)

    @staticmethod
    def _resolve_target_expression(target):
        """ Convert a target expression to a list of targets. """

        if target[0] == '!':
            # Note that this assumes that the target is a platform rather than
            # an architecture.  If this is incorrect then it is a bug in the
            # metadata somewhere.
            targets = list(TARGET_PLATFORM_NAMES)
            targets.remove(target[1:])
        else:
            targets = [target]

        return targets

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

    def _write_package(self, resource_contents, resources_dir, resource, package, src_dir, job_writer):
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
                dir_stack, job_writer, resource_contents)

    def _write_package_contents(self, contents, dst_dir, src_dir, dir_stack, job_writer, resource_contents):
        """ Write the contents of a single package directory. """

        self._create_directory(dst_dir)

        for content in contents:
            if not content.included:
                continue

            if isinstance(content, QrcDirectory):
                dir_stack.append(content.name)

                self._write_package_contents(content.contents,
                        dst_dir + '/' + content.name,
                        src_dir + '/' + content.name, dir_stack, job_writer,
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

                file_path = list(dir_stack)
                file_path.append(dst_file)
                file_path = '/'.join(file_path)

                if freeze_file:
                    self._freeze(job_writer, dst_path, src_path,
                            file_path[:-1])
                else:
                    src_path = QDir.toNativeSeparators(src_path)
                    dst_path = QDir.toNativeSeparators(dst_path)

                    try:
                        shutil.copyfile(src_path, dst_path)
                    except FileNotFoundError:
                        raise UserException(
                                "{0} does not seem to exist".format(src_path))

                resource_contents.append(file_path)

    def _write_main(self, inittab):
        """ Create the application specific pyqtdeploy_main.cpp file. """

        project = self._project

        f = self._create_file(self._build_dir + '/pyqtdeploy_main.cpp')

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

        f.write('''
#if defined(Q_OS_WIN) && PY_MAJOR_VERSION >= 3
#include <windows.h>

extern int pyqtdeploy_start(int argc, wchar_t **w_argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);

int main(int argc, char **)
{
    LPWSTR *w_argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    return pyqtdeploy_start(argc, w_argv, %s, "%s", %s, %s);
}
#else
extern int pyqtdeploy_start(int argc, char **argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);

int main(int argc, char **argv)
{
    return pyqtdeploy_start(argc, argv, %s, "%s", %s, %s);
}
#endif
''' % (c_inittab, main_module, entry_point, path_dirs,
       c_inittab, main_module, entry_point, path_dirs))

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

        for targets, names in inittab:
            if targets:
                cls._write_cpp_guard(f, targets)

            for name in names:
                base_name = name.split('.')[-1]

                f.write('extern "C" %s%s%s(void);\n' % (init_type, init_prefix,
                        base_name))

            if targets:
                f.write('#endif\n')

        f.write('''
static struct _inittab %s[] = {
''' % c_inittab)

        for targets, names in inittab:
            if targets:
                cls._write_cpp_guard(f, targets)

            for name in names:
                base_name = name.split('.')[-1]

                f.write('    {"%s", %s%s},\n' % (name, init_prefix, base_name))

            if targets:
                f.write('#endif\n')

        f.write('''    {NULL, NULL}
};
''')

    @classmethod
    def _write_cpp_guard(cls, f, targets):
        """ Write the C pre-processor guard for some targets. """

        f.write('#if ')

        if targets[0][0] == '!':
            f.write('!defined({0})'.format(cls._cpp_for_target(targets[0][1:])))
        else:
            f.write(' || '.join(['defined({0})'.format(cls._cpp_for_target(t)) for t in targets]))

        f.write('\n')

    @staticmethod
    def _optimised(used_targets):
        """ Return an optimised (to reduce the amount of generated code) list
        of a 2-tuple of targets and values.
        """

        # Generate a reverse dict.
        by_value = {}
        for target, values in used_targets.items():
            for value in values:
                by_value.setdefault(value, set()).add(target)

        # Reverse again and merge the targets.
        optimised = {}
        for value, targets in by_value.items():
            # Convert the targets to a list in predictable order.
            targets = sorted(targets)

            # Ignore unless all targets are platform names.
            for target in targets:
                if '-' in target:
                    break
            else:
                nr_targets = len(targets)
                nr_platforms = len(TARGET_PLATFORM_NAMES)

                if nr_targets == nr_platforms:
                    # The value is unscoped.
                    targets = []
                elif nr_targets == nr_platforms - 1:
                    # Find the missing target.
                    missing = list(TARGET_PLATFORM_NAMES)
                    for target in targets:
                        missing.remove(target)

                    targets = ['!' + missing[0]]

            optimised.setdefault(tuple(targets), set()).add(value)

        # Convert to a data structure that will generate code in a predictable
        # order with unscoped values first.
        pretty = []
        for targets in sorted(optimised.keys()):
            pretty.append((targets, sorted(optimised[targets])))

        return pretty

    @staticmethod
    def _freeze(job_writer, out_file, in_file, name, as_c=False):
        """ Freeze a Python source file to a C header file or a data file. """

        out_file = QDir.toNativeSeparators(out_file)
        in_file = QDir.toNativeSeparators(in_file)

        if as_c:
            conversion = 'C'
        else:
            name = ':/' + name
            conversion = 'data'

        job_writer.writerow([out_file, in_file, name, conversion])

    def _run_freeze(self, freeze, interpreter, job_filename, opt):
        """ Run the accumlated freeze jobs. """

        # On Windows the interpreter name is simply 'python'.  So in order to
        # make the .pdy file more portable we strip any trailing version
        # number.
        if sys.platform == 'win32':
            for i in range(len(interpreter) - 1, -1, -1):
                if interpreter[i] not in '.0123456789':
                    interpreter = interpreter[:i + 1]
                    break

        argv = [QDir.toNativeSeparators(interpreter)]

        if opt == 2:
            argv.append('-OO')
        elif opt == 1:
            argv.append('-O')

        argv.append(freeze)
        argv.append(job_filename)

        self.run(argv, "Unable to freeze files")

    def run_qmake(self, qmake):
        """ Run qmake. """

        if qmake is None:
            qmake = os.path.expandvars(self._project.qmake)

        if qmake == '':
            raise UserException(
                    "qmake cannot be run because its name has not been set")

        self.run([qmake], "qmake failed", in_build_dir=True)

    def run_make(self):
        """ Run make. """

        make = self._host.make

        self.run([make], "{0} failed".format(make), in_build_dir=True)

    def run(self, argv, error_message, in_build_dir=False):
        """ Execute a command and capture the output. """

        if in_build_dir:
            saved_cwd = os.getcwd()
            native_build_dir = QDir.toNativeSeparators(self._build_dir)
            os.chdir(native_build_dir)
            self._message_handler.verbose_message(
                    "{0} is now the current directory".format(
                            native_build_dir))
        else:
            saved_cwd = None

        self._message_handler.verbose_message(
                "Running '{0}'".format(' '.join(argv)))

        QCoreApplication.processEvents()

        process = QProcess()

        process.readyReadStandardOutput.connect(
                lambda: self._message_handler.progress_message(
                        QTextCodec.codecForLocale().toUnicode(
                                process.readAllStandardOutput()).strip()))

        stderr_output = QByteArray()
        process.readyReadStandardError.connect(
                lambda: stderr_output.append(process.readAllStandardError()))

        process.start(argv[0], argv[1:])
        finished = process.waitForFinished(self._timeout)

        if saved_cwd is not None:
            os.chdir(saved_cwd)
            self._message_handler.verbose_message(
                    "{0} is now the current directory".format(saved_cwd))

        if not finished:
            raise UserException(error_message, process.errorString())

        if process.exitStatus() != QProcess.NormalExit or process.exitCode() != 0:
            raise UserException(error_message,
                    QTextCodec.codecForLocale().toUnicode(stderr_output).strip())

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

        # The file will be read-only if it was embedded.
        QFile.setPermissions(d_file_name,
                QFileDevice.ReadOwner|QFileDevice.WriteOwner)

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

    @staticmethod
    def _cpp_for_target(target):
        """ Return the C pre-processor guard for an architecture or platform.
        """

        if '-' in target:
            return TargetArch.find_arch(target).platform.cpp

        return TargetPlatform.find_platform(target).cpp

    @staticmethod
    def _qmake_scope_for_target(target):
        """ Return the C pre-processor guard for an architecture or platform.
        """

        if '-' in target:
            return TargetArch.find_arch(target).qmake_scope

        return TargetPlatform.find_platform(target).qmake_scope
