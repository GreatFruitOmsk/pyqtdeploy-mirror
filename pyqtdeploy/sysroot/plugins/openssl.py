# Copyright (c) 2019, Riverbank Computing Limited
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
        ComponentOption('no_asm', type=bool,
                help="Disable the use of assembly language speedups."),
        ComponentOption('python_source',
                help="The archive of the Python source code containing patches to build OpenSSL on macOS for Python v3.6.4 and earlier."),
        ComponentOption('source', required=True,
                help="The archive containing the OpenSSL source code."),
    ]

    def build(self, sysroot):
        """ Build OpenSSL for the target. """

		# Unpack the source.
        archive = sysroot.find_file(self.source)
        sysroot.unpack_archive(archive)

        # Get the version number.
        version_nr = sysroot.extract_version_nr(archive)

        # Set common options.
        common_options = ['--prefix=' + sysroot.sysroot_dir, 'no-engine']

        if self.no_asm:
            common_options.append('no-asm')

        if version_nr >= 0x010100:
            self._build_1_1(sysroot, common_options)
        else:
            self._build_1_0(sysroot, common_options)

    def configure(self, sysroot):
        """ Complete the configuration of the component. """

        host = sysroot.host_platform_name
        target = sysroot.target_platform_name
        version_nr = sysroot.verify_source(self.source)

        if version_nr >= 0x010101:
            sysroot.error("building OpenSSL v1.1.1 is not supported")

        if target == host:
            supported = (target in ('macos', 'win'))
        else:
            supported = (target == 'android')

        if not supported:
            sysroot.error(
                    "building OpenSSL for {0} on {1} is not supported".format(
                            target, host))

        # See if we will need to patch the Python source code.
        if target == 'macos' and (version_nr & 0xffff00) == 0x010000 and self.python_source:
            sysroot.find_exe('patch')

        sysroot.find_exe('perl')

        # Check NASM is available if it is required.
        if sys.platform == 'win' and not self.no_asm:
            sysroot.find_exe('nasm')

    def _build_1_1(self, sysroot, common_options):
        """ Build OpenSSL v1.1 for supported platforms. """

        if sysroot.target_platform_name == sysroot.host_platform_name:
            # We are building natively.

            if sysroot.target_arch_name == 'macos-64':
                args = ['./config', 'no-shared']
                args.extend(common_options)

                sysroot.run(*args)
                sysroot.run(sysroot.host_make)
                sysroot.run(sysroot.host_make, 'install')

            elif sysroot.target_platform_name == 'win':
                self._build_1_1_win(sysroot, common_options)
        else:
            # We are cross-compiling.

            if sysroot.target_platform_name == 'android':
                self._build_1_1_android(sysroot, common_options)

    def _build_1_1_android(self, sysroot, common_options):
        """ Build OpenSSL v1.1 for Android on either Linux or MacOS hosts. """

        # Configure the environment.
        using_clang = (sysroot.android_ndk_version >= (16, 0, 0))

        original_path = sysroot.add_to_path(sysroot.android_toolchain_bin)

        configure_args = ['perl', 'Configure']

        if using_clang:
            os.environ['CC'] = sysroot.android_toolchain_cc
            os.environ['AR'] = sysroot.android_toolchain_prefix + 'ar'
            os.environ['RANLIB'] = sysroot.android_toolchain_prefix + 'ranlib'
        else:
            configure_args.append('--cross-compile-prefix=' + sysroot.android_toolchain_prefix)

            os.environ['CROSS_SYSROOT'] = os.path.join(
                    sysroot.android_ndk_sysroot)

        configure_args.extend(common_options)
        configure_args.append('android')

        sysroot.run(*configure_args)

        # Fix the Makefile so that it creates .so files without version
        # numbers for qmake to be able to handle.
        with open('Makefile') as f:
            mf = f.read()

        mf = mf.replace('.$(SHLIB_MAJOR).$(SHLIB_MINOR)', '')

        if using_clang:
            mf = mf.replace('-mandroid', '')
            mf = mf.replace('--sysroot=$(CROSS_SYSROOT)', '')

        with open('Makefile', 'w') as f:
            f.write(mf)

        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

        for lib in ('libcrypto', 'libssl'):
            # Remove the static library that was also built.
            os.remove(os.path.join(sysroot.target_lib_dir, lib + '.a'))

        if using_clang:
            del os.environ['CC']
            del os.environ['AR']
            del os.environ['RANLIB']
        else:
            del os.environ['CROSS_SYSROOT']

        os.environ['PATH'] = original_path

    def _build_1_1_win(self, sysroot, common_options):
        """ Build OpenSSL v1.1 for Windows. """

        # Set the architecture-specific values.
        if sysroot.target_arch_name.endswith('-64'):
            target = 'VC-WIN64A'
        else:
            target = 'VC-WIN32'

        args = ['perl', 'Configure', target, 'no-shared',
                '--openssldir=' + sysroot.sysroot_dir + '\\ssl']
        args.extend(common_options)

        sysroot.run(*args)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

    def _build_1_0(self, sysroot, common_options):
        """ Build OpenSSL v1.0 for supported platforms. """

        # Add the common options that Python used prior to v3.7.
        common_options.extend([
            'no-krb5',
            'no-idea',
            'no-mdc2',
            'no-rc5',
            'no-zlib',
            'enable-tlsext',
            'no-ssl2',
            'no-ssl3',
            'no-ssl3-method',
        ])

        if sysroot.target_platform_name == sysroot.host_platform_name:
            # We are building natively.

            if sysroot.target_arch_name == 'macos-64':
                self._build_1_0_macos(sysroot, common_options)

            elif sysroot.target_platform_name == 'win':
                self._build_1_0_win(sysroot, common_options)
        else:
            # We are cross-compiling.

            if sysroot.target_platform_name == 'android':
                self._build_1_0_android(sysroot, common_options)

    def _build_1_0_android(self, sysroot, common_options):
        """ Build OpenSSL v1.0 for Android on either Linux or MacOS hosts. """

        # Configure the environment.
        using_clang = (sysroot.android_ndk_version >= (16, 0, 0))

        original_path = sysroot.add_to_path(sysroot.android_toolchain_bin)
        os.environ['MACHINE'] = 'arm7'
        os.environ['RELEASE'] = '2.6.37'
        os.environ['SYSTEM'] = 'android'
        os.environ['ARCH'] = 'arm'
        os.environ['ANDROID_DEV'] = os.path.join(sysroot.android_ndk_sysroot,
                'usr')

        if using_clang:
            os.environ['CC'] = sysroot.android_toolchain_cc
            os.environ['AR'] = sysroot.android_toolchain_prefix + 'ar'
            os.environ['RANLIB'] = sysroot.android_toolchain_prefix + 'ranlib'
        else:
            os.environ['CROSS_COMPILE'] = sysroot.android_toolchain_prefix

        # Configure, build and install.
        args = ['perl', 'Configure', 'shared']
        args.extend(common_options)
        args.append('android')

        sysroot.run(*args)

        # Patch the Makefile for clang.
        if using_clang:
            with open('Makefile') as f:
                mf = f.read()

            mf = mf.replace('-mandroid', '')

            with open('Makefile', 'w') as f:
                f.write(mf)

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

        if using_clang:
            del os.environ['CC']
            del os.environ['AR']
            del os.environ['RANLIB']
        else:
            del os.environ['CROSS_COMPILE']

        del os.environ['MACHINE']
        del os.environ['RELEASE']
        del os.environ['SYSTEM']
        del os.environ['ARCH']
        del os.environ['ANDROID_DEV']
        os.environ['PATH'] = original_path

    def _build_1_0_macos(self, sysroot, common_options):
        """ Build OpenSSL v1.0 for 64 bit macOS. """

        # Find and apply any Python patch.
        if self.python_source:
            python_archive = sysroot.find_file(self.python_source)
            python_dir = sysroot.unpack_archive(python_archive, chdir=False)

            patches = glob.glob(python_dir + '/Mac/BuildScript/openssl*.patch')

            if len(patches) > 1:
                sysroot.error(
                        "found multiple OpenSSL patches in the Python source tree")

            if len(patches) == 1:
                sysroot.run('patch', '-p1', '-i', patches[0])

        # Configure, build and install.
        sdk_env = 'OSX_SDK=' + sysroot.apple_sdk

        args = ['perl', 'Configure',
                'darwin64-x86_64-cc', 'enable-ec_nistp_64_gcc_128']
        args.extend(common_options)

        sysroot.run(*args)
        sysroot.run(sysroot.host_make, 'depend', sdk_env)
        sysroot.run(sysroot.host_make, 'all', sdk_env)
        sysroot.run(sysroot.host_make, 'install_sw', sdk_env)

    def _build_1_0_win(self, sysroot, common_options):
        """ Build OpenSSL v1.0 for Windows. """

        # Set the architecture-specific values.
        if sysroot.target_arch_name.endswith('-64'):
            target = 'VC-WIN64A'
            post_config = 'ms\\do_win64a.bat'
        else:
            target = 'VC-WIN32'
            post_config = 'ms\\do_ms.bat' if self.no_asm else 'ms\\do_nasm.bat'

        # 'no-engine' seems to be broken on Windows.  It (correctly) doesn't
        # install the header file but tries to build the engines anyway.
        common_options.remove('no-engine')

        # Configure, build and install.
        args = ['perl', 'Configure', target]
        args.extend(common_options)

        sysroot.run(*args)
        sysroot.run(post_config)
        sysroot.run(sysroot.host_make, '-f', 'ms\\nt.mak')
        sysroot.run(sysroot.host_make, '-f', 'ms\\nt.mak', 'install')
