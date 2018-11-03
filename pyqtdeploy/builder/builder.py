# Copyright (c) 2018, Riverbank Computing Limited
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
import glob
import os
import shlex
import shutil
import subprocess

from PyQt5.QtCore import (QByteArray, QCoreApplication, QDir, QFile,
        QFileDevice, QFileInfo, QProcess, QTemporaryDir, QTextCodec)

from ..file_utilities import (create_file, get_embedded_dir,
        get_embedded_file_for_version, parse_version, read_embedded_file)
from ..metadata import (external_libraries_metadata, get_python_metadata,
        get_targeted_value, pyqt4_metadata, pyqt5_metadata)
from ..project import QrcDirectory
from ..platforms import Architecture, Platform
from ..user_exception import UserException
from ..version import PYQTDEPLOY_HEXVERSION
from ..windows import get_py_install_path


class Builder:
    """ The builder for a project. """

    def __init__(self, project, target_arch_name, message_handler):
        """ Initialise the builder for a project. """

        self._project = project
        self._message_handler = message_handler

        self._host = Architecture.architecture()
        self._target = Architecture.architecture(target_arch_name)

    def build(self, opt, nr_resources, clean, sysroot, build_dir, include_dir, interpreter, python_library, source_dir, standard_library_dir):
        """ Build the project in a given directory.  Raise a UserException if
        there is an error.
        """

        project = self._project

        py_major, py_minor, py_patch = project.python_target_version
        py_version = (py_major << 16) + (py_minor << 8) + py_patch

        # Set $SYSROOT.  An explicit sysroot will override any existing value.
        if sysroot:
            os.environ['SYSROOT'] = os.path.abspath(sysroot)
        elif 'SYSROOT' not in os.environ:
            # Provide a default.
            os.environ['SYSROOT'] = os.path.abspath(
                    'sysroot-' + self._target.name)

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

            if module.target and not self._target.is_targeted(module.target):
                continue

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
            elif self._host.platform.name == 'win':
                interpreter = get_py_install_path(
                        project.python_target_version, self._target) + 'python'
            else:
                interpreter = 'python{0}.{1}'.format(py_major, py_minor)

        # On Windows the interpreter name is simply 'python'.  So in order to
        # make the .pdy file more portable we strip any trailing version
        # number.
        if self._host.platform.name == 'win':
            for i in range(len(interpreter) - 1, -1, -1):
                if interpreter[i] not in '.0123456789':
                    interpreter = interpreter[:i + 1]
                    break

        interpreter = QDir.toNativeSeparators(interpreter)

        # Make sure the interpreter being used is the one we are targetting.
        self._check_interpreter_version(interpreter, py_version)

        if python_library is None:
            python_library = project.path_from_user(
                    project.python_target_library)

        if standard_library_dir is None:
            standard_library_dir = project.path_from_user(
                    project.python_target_stdlib_dir)

        # Set the name of the build directory.
        if not build_dir:
            build_dir = 'build-' + self._target.name

        self._build_dir = os.path.abspath(build_dir)

        # Remove any build directory if required.
        if clean:
            native_build_dir = QDir.toNativeSeparators(self._build_dir)
            self._message_handler.progress_message(
                    "Cleaning {0}".format(native_build_dir))
            shutil.rmtree(native_build_dir, ignore_errors=True)

        # Now start the build.
        self._create_directory(self._build_dir)

        # Create the job file and writer.
        job_filename = QDir.toNativeSeparators(temp_dir.path() + '/jobs.csv')
        job_file = open(job_filename, 'w', newline='')
        job_writer = csv.writer(job_file)

        # Freeze the bootstrap.  Note that from Python v3.5 the modified part
        # is in _bootstrap_external.py and _bootstrap.py is unchanged from the
        # original source.  We continue to use a local copy of _bootstrap.py
        # as it still needs to be frozen and we don't want to depend on an
        # external source.
        self._freeze_bootstrap('bootstrap', py_version, self._build_dir,
                temp_dir, job_writer)

        if py_version >= 0x030500:
            self._freeze_bootstrap('bootstrap_external', py_version,
                    self._build_dir, temp_dir, job_writer)

        # Freeze any main application script.
        if project.application_script != '':
            self._freeze(job_writer, self._build_dir + '/frozen_main.h',
                    project.path_from_user(project.application_script),
                    'pyqtdeploy_main', as_c=True)

        # Create the pyqtdeploy module version file.
        version_f = self._create_file(
                self._build_dir + '/pyqtdeploy_version.h')
        version_f.write(
                '#define PYQTDEPLOY_HEXVERSION %s\n' % hex(
                        PYQTDEPLOY_HEXVERSION))
        version_f.close()

        # Determine if there is a private sip module.
        sip_lib_path = '{0}/site-packages/{1}/{2}'.format(
                standard_library_dir, self._get_pyqt_package_name(),
                'sip.lib' if self._target.platform.name == 'win' else 'libsip.a')
        private_sip = QFile.exists(sip_lib_path)

        # Generate the application resource.
        resource_names = self._generate_resource(
                self._build_dir + '/resources', required_py,
                standard_library_dir, private_sip, job_writer, nr_resources)

        # Write the .pro file.
        self._write_qmake(py_version, required_ext, required_libraries,
                include_dir, python_library, standard_library_dir, private_sip,
                source_dir, job_writer, opt, resource_names)

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

    def _generate_resource(self, resources_dir, required_py, standard_library_dir, private_sip, job_writer, nr_resources):
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
        if any([m for m in project.pyqt_modules if private_sip or m != 'sip']):
            pyqt_subdir = self._get_pyqt_package_name()
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
            module = required_py[name]
            suffix = '/__init__.py' if module.modules is not None else '.py'

            # Resolve any patterns.
            if '*' in name:
                pattern = os.path.join(standard_library_dir,
                        name.replace('.', os.sep) + suffix)
                modules = glob.glob(pattern)

                if len(modules) != 1:
                    raise UserException(
                            "'{0}' must match exactly one module".format(name))

                name_path = modules[0][len(standard_library_dir) + 1:-len(suffix)].replace(os.sep, '/')
            else:
                name_path = name.replace('.', '/')

            if module.modules is not None:
                self._create_directory(resources_dir + '/' + name_path)

            in_file = name_path + suffix
            out_file = in_file + 'o'

            self._freeze(job_writer, resources_dir + '/' + out_file,
                    standard_library_dir + '/' + in_file, in_file)

            resource_contents.append(out_file)

    # The map of non-C/C++ source extensions to qmake variable.
    _source_extensions = (
        ('.asm',    'MASMSOURCES'),
        ('.h',      'HEADERS'),
        ('.java',   'JAVASOURCES'),
        ('.l',      'LEXSOURCES'),
        ('.pyx',    'CYTHONSOURCES'),
        ('.y',      'YACCSOURCES')
    )

    def _write_qmake(self, py_version, required_ext, required_libraries, include_dir, python_library, standard_library_dir, private_sip, source_dir, job_writer, opt, resource_names):
        """ Create the .pro file for qmake. """

        project = self._project
        target_platform = self._target.platform.name

        f = self._create_file(self._build_dir + '/' +
                project.get_executable_basename() + '.pro')

        f.write('# Generated for {0} and Python v{1}.{2}.{3}.\n\n'.format(
                self._target.name, (py_version >> 16),
                (py_version >> 8) & 0xff, py_version & 0xff))

        f.write('TEMPLATE = app\n')
        f.write('\n')

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

            if self._target.is_targeted(metadata.targets):
                qmake_qt4.update(metadata.qt4)
                qmake_config4.update(metadata.config4)

                qmake_qt5.update(metadata.qt5)
                qmake_config5.update(metadata.config5)

        # Extract QT and CONFIG values that not version-specific.
        qmake_qt45 = qmake_qt4 & qmake_qt5
        qmake_qt4 -= qmake_qt45
        qmake_qt5 -= qmake_qt45

        qmake_config45 = qmake_config4 & qmake_config5
        qmake_config4 -= qmake_config45
        qmake_config5 -= qmake_config45

        # Generate QT.
        self._write_qt_config(f, 'QT', None, qmake_qt45)
        self._write_qt_config(f, 'QT', 4, qmake_qt4)
        self._write_qt_config(f, 'QT', 5, qmake_qt5)

        if not needs_gui:
            f.write('QT -= gui\n')

        # Generate CONFIG.
        config = ['warn_off']

        if target_platform == 'win':
            if project.application_is_console or not needs_gui:
                config.append('console')

        if needs_cpp11:
            config.append('c++11')

        f.write('CONFIG += {0}\n'.format(' '.join(config)))

        if target_platform == 'macos':
            if not project.application_is_bundle:
                f.write('CONFIG -= app_bundle\n')

        self._write_qt_config(f, 'CONFIG', None, qmake_config45)
        self._write_qt_config(f, 'CONFIG', 4, qmake_config4)
        self._write_qt_config(f, 'CONFIG', 5, qmake_config5)

        # Modules can share sources so we need to make sure we don't include
        # them more than once.  We might as well handle the other things in the
        # same way.
        used_qt = set()
        used_config = set()
        used_sources = set()
        used_defines = set()
        used_includepath = set()
        used_libs = set()
        used_inittab = set()
        used_dlls = set()

        # Handle any static PyQt modules.
        site_packages = standard_library_dir + '/site-packages'
        pyqt_package = self._get_pyqt_package_name()

        for module in self._get_all_pyqt_modules():
            # The uic module is pure Python.
            if module == 'uic':
                continue

            metadata = self._get_pyqt_module_metadata(module)

            if not self._target.is_targeted(metadata.targets):
                continue

            # The sip module is always needed (implicitly or explicitly) if we
            # have got this far.  We handle it separately when it is in a
            # different directory.
            if module == 'sip' and not private_sip:
                used_inittab.add(module)
                used_libs.add('-L' + site_packages)
            else:
                used_inittab.add(pyqt_package + '.' + module)
                used_libs.add('-L' + site_packages + '/' + pyqt_package)

            lib_name = '-l' + module
            if metadata.needs_suffix:
                # Qt4's qmake thinks -lQtCore etc. always refer to the Qt
                # libraries so PyQt4 creates static libraries with a suffix.
                lib_name += '_s'

            used_libs.add(lib_name)

        # Handle any other extension modules.
        for other_em in project.other_extension_modules:
            # If the name is scoped then the targets are the outer scopes for
            # the remaining values.
            value = self._get_scoped_value(other_em.name)
            if value is None:
                continue

            used_inittab.add(value)

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
            used_includepath.add(include_dir)

        if python_library != '':
            fi = QFileInfo(python_library)

            py_lib_dir = fi.absolutePath()
            lib = fi.completeBaseName()

            # This is smart enough to translate the Python library as a UNIX .a
            # file to what Windows needs.
            if lib.startswith('lib'):
                lib = lib[3:]

            if '.' in lib and target_platform == 'win':
                lib = lib.replace('.', '')

            used_libs.add('-l' + lib)
            used_libs.add('-L' + py_lib_dir)
        else:
            py_lib_dir = None

        # Handle any standard library extension modules.
        if target_platform not in project.python_use_platform:
            self._add_stdlib_extension_modules(project, target_platform,
                    source_dir, required_ext, used_inittab, used_sources,
                    used_includepath, used_defines, used_libs, used_dlls)

        # Handle any required external libraries.
        android_extra_libs = []

        external_libs = project.external_libraries.get(target_platform, ())

        for required_lib in required_libraries:
            # Skip any external libraries that are not for the current target.
            required_lib = self._get_scoped_value(required_lib)
            if required_lib is None:
                continue

            defines = includepath = libs = ''

            for xlib in external_libs:
                if xlib.name == required_lib:
                    defines = xlib.defines
                    includepath = xlib.includepath
                    libs = xlib.libs
                    break
            else:
                # Use the defaults.
                for xlib in external_libraries_metadata:
                    if xlib.name == required_lib:
                        if target_platform not in project.python_use_platform:
                            defines = xlib.defines
                            includepath = xlib.includepath
                            libs = xlib.get_libs(target_platform)

                        break

            # Check the library is not disabled for this target.
            enabled = False

            if defines != '':
                self._add_compound_scoped_values(used_defines, defines, False)
                enabled = True

            if includepath != '':
                self._add_compound_scoped_values(used_includepath, includepath,
                        True)
                enabled = True

            if libs != '':
                self._add_compound_scoped_values(used_libs, libs, False)
                enabled = True

            if enabled and target_platform == 'android':
                self._add_android_extra_libs(libs, android_extra_libs)

        # Specify any project-specific configuration.
        if used_qt:
            f.write('\n')
            self._write_used_values(f, used_qt, 'QT')

        if used_config:
            f.write('\n')
            self._write_used_values(f, used_config, 'CONFIG')

        # Python v3.6.0 requires C99 at least.  Note that specifying 'c++11' in
        # 'CONFIG' doesn't affect 'CFLAGS'.
        if py_version >= 0x030600 and target_platform != 'win':
            f.write('\n')
            f.write('QMAKE_CFLAGS += -std=c99\n')

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
        self._write_main(py_version, used_inittab, used_defines)
        self._copy_lib_file('pyqtdeploy_start.cpp', self._build_dir)
        self._copy_lib_file('pdytools_module.cpp', self._build_dir)

        f.write('\n')
        f.write('HEADERS = {0}\n'.format(' '.join(headers)))

        # Specify the libraries.
        if used_libs:
            f.write('\n')
            self._write_used_values(f, used_libs, 'LIBS')

        # Add the library files to be added to an Android APK.
        if android_extra_libs and target_platform == 'android':
            f.write('\n')
            f.write('ANDROID_EXTRA_LIBS += %s\n' % ' '.join(android_extra_libs))

        # If we are using the platform Python on Windows then copy in the
        # required DLLs if they can be found.
        if 'win' in project.python_use_platform and used_dlls and py_lib_dir is not None:
            self._copy_windows_dlls(py_version, py_lib_dir, used_dlls, f)

        # Add the project independent post-configuration stuff.
        self._write_embedded_lib_file('post_configuration.pro', f)

        # Add any application specific stuff.
        qmake_configuration = project.qmake_configuration.strip()

        if qmake_configuration != '':
            f.write('\n' + qmake_configuration + '\n')

        # All done.
        f.close()

    def _add_stdlib_extension_modules(self, project, target_platform, source_dir, required_ext, used_inittab, used_sources, used_includepath, used_defines, used_libs, used_dlls):
        """ Add the building of any standard library extension modules. """

        for name, module in required_ext.items():
            if not self._target.is_targeted(module.target):
                continue

            # See if the extension module should be disabled for a platform
            # because there are no external libraries to link against.
            skip_module = False

            for xlib in project.external_libraries.get(target_platform, ()):
                if xlib.name == module.xlib:
                    if xlib.defines == '' and xlib.includepath == '' and xlib.libs == '':
                        skip_module = True

                    break

            if skip_module:
                continue

            used_inittab.add(name)

            for source in module.source:
                source = self._get_scoped_value(source)
                if source is not None:
                    source = self._python_source_file(source_dir, source)
                    used_sources.add(source)

                    used_includepath.add(source_dir + '/Modules')

            if module.defines is not None:
                for define in module.defines:
                    define = self._get_scoped_value(define)
                    if define is not None:
                        used_defines.add(define)

            if module.includepath is not None:
                for includepath in module.includepath:
                    includepath = self._get_scoped_value(includepath)
                    if includepath is not None:
                        includepath = self._python_source_file(source_dir,
                                includepath)
                        used_includepath.add(includepath)

            if module.libs is not None:
                for lib in module.libs:
                    lib = self._get_scoped_value(lib)
                    if lib is not None:
                        used_libs.add(lib)

            if module.pyd is not None and target_platform == 'win':
                used_dlls.add(module)

        if target_platform == 'win':
            used_includepath.add(source_dir + '/PC')

    def _get_pyqt_package_name(self):
        """ Return the name of the PyQt package. """

        return 'PyQt5' if self._project.application_is_pyqt5 else 'PyQt4'

    @classmethod
    def _write_qt_config(cls, f, name, qt_major, values):
        """ Write the values of QT or CONFIG which may be Qt version specific.
        """

        if values:
            if qt_major is None:
                indent = ''
            else:
                indent = '    '

                if qt_major == 5:
                    f.write('greaterThan(QT_MAJOR_VERSION, 4) {\n')
                else:
                    f.write('lessThan(QT_MAJOR_VERSION, 5) {\n')

            f.write('%s%s += %s\n' % (indent, name, ' '.join(values)))

            if indent:
                f.write('}\n')

    @classmethod
    def _write_used_values(cls, f, used_values, name):
        """ Write a set of used values to a .pro file. """

        # Sort them for reproduceable output.
        for value in sorted(used_values):
            qmake_var = name

            if qmake_var == 'SOURCES':
                for ext, var in cls._source_extensions:
                    if value.endswith(ext):
                        qmake_var = var
                        break

            elif qmake_var == 'LIBS':
                # A (strictly unnecessary) bit of pretty printing.
                if value.startswith('"-framework') and value.endswith('"'):
                    value = value[1:-1]

            f.write('{0} += {1}\n'.format(qmake_var, value))

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

        for name in dlls:
            f.write('''
PDY_DLL = %s/DLLs%d.%d/%s
exists($$PDY_DLL) {
    CONFIG(debug, debug|release) {
        QMAKE_POST_LINK += $(COPY_FILE) $$shell_path($$PDY_DLL) $$shell_path($$OUT_PWD/debug) &
    } else {
        QMAKE_POST_LINK += $(COPY_FILE) $$shell_path($$PDY_DLL) $$shell_path($$OUT_PWD/release) &
    }
}
''' % (py_lib_dir, py_major, py_minor, name))

    def _write_embedded_lib_file(self, file_name, f):
        """ Write an embedded file from the lib directory. """

        contents = read_embedded_file(self._get_lib_file_name(file_name))

        f.write('\n')
        f.write(contents.data().decode('latin1'))

    @staticmethod
    def _python_source_file(py_source_dir, rel_path):
        """ Return the absolute name of a file in the Python source tree
        relative to the Modules directory.
        """

        file_path = py_source_dir + '/Modules/' + rel_path

        return QFileInfo(file_path).absoluteFilePath()

    def _add_compound_scoped_values(self, used_values, raw, isfilename):
        """ Parse a string of space separated possible scoped values and add
        them to a set of used values.  The values are optionally treated as
        filenames where they are converted to absolute filenames with UNIX
        separators and have environment variables expanded.
        """

        project = self._project

        for scoped_value in self._split_quotes(raw):
            value = self._get_scoped_value(scoped_value)
            if value is None:
                continue

            # Convert potential filenames.
            if isfilename:
                value = project.path_from_user(value)
            elif value.startswith('-L'):
                value = '-L' + project.path_from_user(value[2:])

            used_values.add(value)

    def _add_android_extra_libs(self, libs, android_extra_libs):
        """ Add the shared library files for Android. """

        project = self._project

        lib_dir = ''
        lib_so = []

        for scoped_value in self._split_quotes(libs):
            # We support the use of scoped values (to be consistent) but it
            # actually makes no sense in this context.
            value = self._get_scoped_value(scoped_value)
            if value is None:
                continue

            if value.startswith('-L'):
                lib_dir = project.path_from_user(value[2:])
            elif value.startswith('-l'):
                lib_so.append('lib' + value[2:] + '.so')

        if lib_dir != '':
            for lib in lib_so:
                android_extra_libs.append(lib_dir + '/' + lib)

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

    def _get_scoped_value(self, scoped_value):
        """ Return the value from a (possibly) scoped value or None if the
        value isn't valid for the target.
        """

        return get_targeted_value(scoped_value, self._target)

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

    def _write_main(self, py_version, inittab, defines):
        """ Create the application specific pyqtdeploy_main.cpp file. """

        project = self._project

        f = self._create_file(self._build_dir + '/pyqtdeploy_main.cpp')

        # Compilation fails when using GCC 5 when both Py_BUILD_CORE and
        # HAVE_STD_ATOMIC are defined.  Py_BUILD_CORE gets defined when certain
        # Python modukes are used.  We simply make sure HAVE_STD_ATOMIC is not
        # defined.
        if 'Py_BUILD_CORE' in defines:
            f.write('''// Py_BUILD_CORE/HAVE_STD_ATOMIC conflict workaround.
#include <pyconfig.h>
#undef HAVE_STD_ATOMIC

''')

        f.write('''#include <Python.h>
#include <QtGlobal>


''')

        if len(inittab) > 0:
            c_inittab = 'extension_modules'

            self._write_inittab(f, inittab, c_inittab, py_version)
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

        if self._target.platform.name == 'win' and py_version >= 0x030000:
            f.write('''

#include <windows.h>

extern int pyqtdeploy_start(int argc, wchar_t **w_argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);

int main(int argc, char **)
{
    LPWSTR *w_argv = CommandLineToArgvW(GetCommandLineW(), &argc);

    return pyqtdeploy_start(argc, w_argv, %s, "%s", %s, %s);
}
''' % (c_inittab, main_module, entry_point, path_dirs))
        else:
            f.write('''

extern int pyqtdeploy_start(int argc, char **argv,
        struct _inittab *extension_modules, const char *main_module,
        const char *entry_point, const char **path_dirs);

int main(int argc, char **argv)
{
    return pyqtdeploy_start(argc, argv, %s, "%s", %s, %s);
}
''' % (c_inittab, main_module, entry_point, path_dirs))

        f.close()

    @classmethod
    def _write_inittab(cls, f, inittab, c_inittab, py_version):
        """ Write the Python version specific extension module inittab. """

        if py_version >= 0x030000:
            init_type = 'PyObject *'
            init_prefix = 'PyInit_'
        else:
            init_type = 'void '
            init_prefix = 'init'

        # We want reproduceable output.
        sorted_inittab = sorted(inittab)

        for name in sorted_inittab:
            base_name = name.split('.')[-1]

            f.write('extern "C" %s%s%s(void);\n' % (init_type, init_prefix,
                    base_name))

        f.write('''
static struct _inittab %s[] = {
''' % c_inittab)

        for name in sorted_inittab:
            base_name = name.split('.')[-1]

            f.write('    {"%s", %s%s},\n' % (name, init_prefix, base_name))

        f.write('''    {NULL, NULL}
};
''')

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

        argv = [interpreter]

        if opt == 2:
            argv.append('-OO')
        elif opt == 1:
            argv.append('-O')

        argv.append(freeze)
        argv.append(job_filename)

        self.run(argv, "Unable to freeze files")

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
        finished = process.waitForFinished()

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
    def _check_interpreter_version(interpreter, py_version):
        """ Check that the interpreter version matches the target version. """

        argv = [interpreter, '-c', 'import sys; print(sys.version)']

        try:
            stdout = subprocess.check_output(argv, universal_newlines=True,
                    stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            try:
                detail = e.stderr
            except AttributeError:
                detail = e.output

            raise UserException("Unable to run '{0}'".format(interpreter),
                    detail=detail)

        interpreter_version = stdout.strip().split()[0]

        # We ignore the micro version.
        if parse_version(interpreter_version) >> 8 != py_version >> 8:
            raise UserException(
                    "The host interpreter version '{0}' does not match the "
                    "target version".format(interpreter_version))
