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


import glob
import sys

from ... import AbstractPackage, PackageOption


class OpenSSLPackage(AbstractPackage):
    """ The OpenSSL package. """

    # The package-specific options.
    options = [
        PackageOption('python_source', str,
                help="The archive of the Python source code containing patches to build OpenSSL on macOS."),
        PackageOption('source', str, required=True,
                help="The archive containing the OpenSSL source code."),
    ]

    def build(self, sysroot):
        """ Build OpenSSL for the target. """

        sysroot.progress("Building OpenSSL")

		# Unpack the source.
        archive = sysroot.find_file(self.source)
        sysroot.unpack_archive(archive)

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

        if sys.platform == 'darwin' and sysroot.native:
            self._build_macos(sysroot, common_options)
        elif sys.platform == 'win32' and sysroot.native:
            self._build_win(sysroot, common_options)
        else:
            sysroot.error(
                    "building OpenSSL for {0} is not yet supported".format(
                            sysroot.target_arch_name))

    def _build_macos(self, sysroot, common_options):
        """ Build OpenSSL for osx-64. """

        # Check pre-requisites.
        sysroot.find_exe('patch')
        sysroot.find_exe('perl')

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

        sysroot.apple_set_deployment_target()
        sysroot.run(*args)
        sysroot.run(sysroot.host_make, 'depend', 'OSX_SDK=' + sdk)
        sysroot.run(sysroot.host_make, 'all', 'OSX_SDK=' + sdk)
        sysroot.run(sysroot.host_make, 'install_sw', 'OSX_SDK=' + sdk)

    def _build_win(self, sysroot, common_options):
        """ Build OpenSSL for win-*. """

        # Check pre-requisites.
        sysroot.find_exe('perl')

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
