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


import os
import sys

from ... import ComponentBase, ComponentOption


class Qt5Component(ComponentBase):
    """ The Qt5 component. """

    # The component options.
    options = [
        ComponentOption('configure_options', type=list,
                help="The additional options to be passed to 'configure' when building from source."),
        ComponentOption('disabled_features', type=list,
                help="The features that are disabled when building from source."),
        ComponentOption('qt_dir',
                help="The pathname of the directory containing an existing Qt5 installation to use. If it is not specified then the installation will be built from source."),
        ComponentOption('ssl',
                values=['openssl-linked', 'openssl-runtime',
                        'securetransport'],
                help="Enable SSL support."),
        ComponentOption('skip', type=list,
                help="The Qt modules to skip when building from source."),
        ComponentOption('source',
                help="The archive containing the Qt5 source code if an existing installation is not to be used."),
        ComponentOption('static_msvc_runtime', type=bool,
                help="Set if the MSVC runtime should be statically linked."),
    ]

    def build(self, sysroot):
        """ Build Qt5 for the target. """

        if self.qt_dir:
            sysroot.progress("Installing an existing Qt5")
        else:
            sysroot.progress("Building Qt5 from source")

            # We don't support cross-compiling Qt.
            if sysroot.host_platform_name != sysroot.target_platform_name:
                sysroot.error(
                        "cross compiling Qt is not supported - use the 'qt_dir' option to specify an existing Qt5 installation")

            self._build_from_source(sysroot)

        # Create a symbolic link to qmake in a standard place in sysroot so
        # that it can be referred to in cross-target build scripts.
        sysroot.make_symlink(sysroot.host_qmake,
                os.path.join(sysroot.host_bin_dir, sysroot.host_exe('qmake')))

        # Do the same for androiddeployqt if it exists.
        androiddeployqt = sysroot.host_exe('androiddeployqt')
        androiddeployqt_path = os.path.join(self._target_qt_dir, 'bin',
                androiddeployqt)

        if os.path.isfile(androiddeployqt_path):
            sysroot.make_symlink(androiddeployqt_path,
                    os.path.join(sysroot.host_bin_dir, androiddeployqt))

    def _build_from_source(self, sysroot):
        """ Build Qt5 from source. """

        archive = sysroot.find_file(self.source)
        archive_dir = sysroot.unpack_archive(archive)

        if sys.platform == 'win32':
            configure = 'configure.bat'

            dx_setenv = os.path.expandvars(
                    '%DXSDK_DIR%\\Utilities\\bin\\dx_setenv.cmd')

            if os.path.exists(dx_setenv):
                sysroot.run(dx_setenv)

            original_path = os.environ['PATH']
            new_path = [original_path]

            new_path.insert(0, os.path.abspath('gnuwin32\\bin'))

            # Look in the registry for a Python v2.7 installation.
            py_27 = sysroot.get_python_install_path(0x020700)
            new_path.insert(0, py_27)

            os.environ['PATH'] = ';'.join(new_path)
        else:
            configure = './configure'
            original_path = None

        license = '-opensource' if '-opensource-' in archive_dir else '-commercial'

        args = [configure, '-prefix', self._target_qt_dir, license,
                '-confirm-license', '-static', '-release', '-nomake',
                'examples', '-nomake', 'tools',
                '-I', sysroot.target_include_dir,
                '-L', sysroot.target_lib_dir]

        if sys.platform == 'win32' and self.static_msvc_runtime:
            args.append('-static-runtime')

        if self.ssl:
            args.append('-ssl')

            if self.ssl == 'securetransport':
                args.append('-securetransport')

            elif self.ssl == 'openssl-linked':
                args.append('-openssl-linked')

                if sys.platform == 'win32':
                    # Get the OpenSSL version number.
                    openssl = sysroot.find_component('openssl')
                    openssl_archive = sysroot.find_file(openssl.source)
                    openssl_version_nr = sysroot.extract_version_nr(
                            openssl_archive)

                    if openssl_version_nr >= 0x010100:
                        openssl_libs = '-llibssl -llibcrypto'
                    else:
                        openssl_libs = '-lssleay32 -llibeay32'

                    args.append('OPENSSL_LIBS=' + openssl_libs + ' -lGdi32')

            elif self.ssl == 'openssl-runtime':
                args.append('-openssl-runtime')

        else:
            args.append('-no-ssl')

        if self.configure_options:
            args.extend(self.configure_options)

        if self.disabled_features:
            for feature in self.disabled_features:
                args.append('-no-feature-' + feature)

        if self.skip:
            for module in self.skip:
                args.append('-skip')
                args.append(module)

        if sys.platform == 'win32':
            # These cause compilation failures (although maybe only with static
            # builds).
            args.append('-skip')
            args.append('qtimageformats')
        elif sys.platform == 'linux':
            args.append('-qt-xcb')

        sysroot.run(*args)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

        if original_path is not None:
            os.environ['PATH'] = original_path

    def configure(self, sysroot):
        """ Complete the configuration of the component. """

        # Determine the qmake location as it may be needed by other components.
        if self.qt_dir:
            if self.source:
                sysroot.error(
                        "the 'qt_dir' and 'source' options cannot both be specified")

            self._target_qt_dir = sysroot.find_file(self.qt_dir)

            if not os.path.isdir(self._target_qt_dir):
                sysroot.error("'{0}' could not be found".format(qt_dir))
        else:
            if not self.source:
                sysroot.error(
                        "either the 'qt_dir' or 'source' option must be specified")

            self._target_qt_dir = os.path.join(sysroot.sysroot_dir, 'qt')

        sysroot.host_qmake = os.path.join(self._target_qt_dir, 'bin', 'qmake')
