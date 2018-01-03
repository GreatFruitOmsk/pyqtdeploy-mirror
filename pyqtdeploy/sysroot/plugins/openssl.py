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


import glob
import os
import sys

from ... import ComponentBase, ComponentOption


class OpenSSLComponent(ComponentBase):
    """ The OpenSSL component. """

    # The component options.
    options = [
        ComponentOption('python_source',
                help="The archive of the Python source code containing patches to build OpenSSL on macOS."),
        ComponentOption('source', required=True,
                help="The archive containing the OpenSSL source code."),
    ]

    def build(self, sysroot):
        """ Build OpenSSL for the target. """

        sysroot.progress("Building OpenSSL")

		# Unpack the source.
        archive = sysroot.find_file(self.source)
        sysroot.unpack_archive(archive)

        # We require OpenSSL v1.0.* as Python does.
        major = minor = None
        name = os.path.basename(os.getcwd())
        name_parts = name.split('-')
        if len(name_parts) == 2:
            version_parts = name_parts[1].split('.')
            if len(version_parts) == 3:
                major, minor, _ = version_parts

        if major is None:
            sysroot.error(
                    "unable to extract OpenSSL version number from '{0}'".format(
                        name))

        if major != '1' or minor != '0':
            sysroot.error("OpenSSL v1.0.* is required")

        # TODO: Need to decide what to do about --openssldir.
        common_options = (
            'no-krb5',
            'no-idea',
            'no-mdc2',
            'no-rc5',
            'no-zlib',
            'enable-tlsext',
            'no-ssl2',
            'no-ssl3',
            'no-ssl3-method',
            '--prefix=' + sysroot.sysroot_dir,
        )

        # Check the common pre-requisites.
        sysroot.find_exe('perl')

        if sysroot.target_platform_name == sysroot.host_platform_name:
            # We are building natively.

            if sysroot.target_arch_name == 'macos-64':
                self._build_macos(sysroot, common_options)
                return

            if sysroot.target_platform_name == 'win':
                self._build_win(sysroot, common_options)
                return
        else:
            # We are cross-compiling.

            if sysroot.target_platform_name == 'android' and sysroot.host_platform_name in ('linux', 'macos'):
                self._build_android(sysroot, common_options)
                return

        # If we get this far then we can't do the requested build.
        sysroot.error(
                "building OpenSSL for '{0}' on '{1}' is not supported".format(
                        sysroot.target_arch_name, sysroot.host_platform_name))

    def _build_android(self, sysroot, common_options):
        """ Build OpenSSL for Android on either Linux or MacOS hosts. """

        # Configure the environment.
        android_host = 'darwin' if sysroot.host_platform_name == 'macos' else 'linux'
        android_host += '-x86_64'

        ndk_root = os.environ['ANDROID_NDK_ROOT']
        ndk_sysroot = os.path.join(ndk_root, 'platforms',
                'android-{}'.format(sysroot.android_api), 'arch-arm')
        toolchain_prefix = 'arm-linux-androideabi-'

        toolchain_version = os.environ.get('ANDROID_NDK_TOOLCHAIN_VERSION')
        if toolchain_version is None:
            sysroot.error(
                    "the ANDROID_NDK_TOOLCHAIN_VERSION environment variable must be set to an appropriate value (e.g. '4.9')")

        toolchain_bin = os.path.join(ndk_root, 'toolchains',
                toolchain_prefix + toolchain_version, 'prebuilt',
                android_host, 'bin')

        path = os.environ['PATH'].split(os.pathsep)
        if toolchain_bin not in path:
            path.insert(0, toolchain_bin)
            os.environ['PATH'] = os.pathsep.join(path)

        os.environ['MACHINE'] = 'arm7'
        os.environ['RELEASE'] = '2.6.37'
        os.environ['SYSTEM'] = 'android'
        os.environ['ARCH'] = 'arm'
        os.environ['CROSS_COMPILE'] = toolchain_prefix

        # Note that OpenSSL v1.1.0 and later uses CROSS_SYSROOT=ndk_sysroot
        # instead.
        os.environ['ANDROID_DEV'] = os.path.join(ndk_sysroot, 'usr')

        # Configure, build and install.
        args = ['perl', 'Configure', 'shared', 'android']
        args.extend(common_options)

        sysroot.run(*args)
        sysroot.run(sysroot.host_make, 'depend')
        sysroot.run(sysroot.host_make,
                'CALC_VERSIONS="SHLIB_COMPAT=; SHLIB_SOVER="', 'build_libs',
                'build_apps')
        sysroot.run(sysroot.host_make, 'install_sw')

        for lib in ('libcrypto', 'libssl'):
            # Remove the static library that was also built.
            os.remove(os.path.join(sysroot.target_lib_dir, lib + '.a'))

            # The unversioned .so was installed and then overwritten with a
            # symbolic link to the non-existing versioned .so, so install it
            # again.
            lib_so = lib + '.so'
            installed_lib_so = os.path.join(sysroot.target_lib_dir, lib_so)

            os.remove(installed_lib_so)
            sysroot.copy_file(lib_so, installed_lib_so)

    def _build_macos(self, sysroot, common_options):
        """ Build OpenSSL for 64 bit macOS. """

        # Check the additional pre-requisites.
        sysroot.find_exe('patch')

        # Find and apply the Python patch.
        if not self.python_source:
            sysroot.error("the 'python_source' option must be specified")

        python_archive = sysroot.find_file(self.python_source)
        python_dir = sysroot.unpack_archive(python_archive, chdir=False)

        patches = glob.glob(python_dir + '/Mac/BuildScript/openssl*.patch')

        if len(patches) < 1:
            sysroot.error(
                    "unable to find an OpenSSL patch in the Python source tree")

        if len(patches) > 1:
            sysroot.error(
                    "found multiple OpenSSL patches in the Python source tree")

        sysroot.run('patch', '-p1', '-i', patches[0])

        # Configure, build and install.
        sdk = sysroot.apple_sdk

        args = ['perl', 'Configure',
                'darwin64-x86_64-cc', 'enable-ec_nistp_64_gcc_128']
        args.extend(common_options)

        sysroot.run(*args)
        sysroot.run(sysroot.host_make, 'depend', 'OSX_SDK=' + sdk)
        sysroot.run(sysroot.host_make, 'all', 'OSX_SDK=' + sdk)
        sysroot.run(sysroot.host_make, 'install_sw', 'OSX_SDK=' + sdk)

    def _build_win(self, sysroot, common_options):
        """ Build OpenSSL for Windows. """

        # Set the architecture-specific values.
        if sysroot.target_arch_name.endswith('-64'):
            compiler = 'VC-WIN64A'
            post_config = 'ms\\do_win64a.bat'
        else:
            compiler = 'VC-WIN32'
            post_config = 'ms\\do_nasm.bat'

        # Configure, build and install.
        args = ['perl', 'Configure', compiler]
        args.extend(common_options)

        sysroot.run(*args)
        sysroot.run(post_config)
        sysroot.run(sysroot.host_make, '-f', 'ms\\nt.mak')
        sysroot.run(sysroot.host_make, '-f', 'ms\\nt.mak', 'install')
