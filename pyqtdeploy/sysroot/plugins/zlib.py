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

from ... import ComponentBase, ComponentOption


class zlibComponent(ComponentBase):
    """ The zlib component. """

    # The component options.
    options = [
        ComponentOption('source', required=True,
                help="The archive containing the zlib source code."),
        ComponentOption('static_msvc_runtime', type=bool,
                help="Set if the MSVC runtime should be statically linked."),
    ]

    def build(self, sysroot):
        """ Build zlib for the target. """

        sysroot.progress("Building zlib")

        archive = sysroot.find_file(self.source)
        sysroot.unpack_archive(archive)

        if sysroot.target_platform_name == 'win':
            make_args = [sysroot.host_make, '-f', 'win32\\Makefile.msc',
                    'zlib.lib']

            if self.static_msvc_runtime:
                make_args.append('LOC=-MT')

            sysroot.run(*make_args)

            sysroot.copy_file('zconf.h', sysroot.target_include_dir)
            sysroot.copy_file('zlib.h', sysroot.target_include_dir)
            sysroot.copy_file('zlib.lib', sysroot.target_lib_dir)

        elif sysroot.target_platform_name == 'android':
            # Configure the environment.
            original_path = sysroot.add_to_path(sysroot.android_toolchain_bin)
            os.environ['CROSS_PREFIX'] = sysroot.android_toolchain_prefix
            os.environ['CC'] = sysroot.android_toolchain_prefix + 'gcc'
            os.environ['CFLAGS'] = '-march=armv7-a -mfloat-abi=softfp -mfpu=vfp -fno-builtin-memmove -mthumb -Os --sysroot=' + sysroot.android_ndk_sysroot

            sysroot.run('./configure', '--static',
                    '--prefix=' + sysroot.sysroot_dir)
            sysroot.run(sysroot.host_make, 'AR=' + sysroot.android_toolchain_prefix + 'ar cqs')
            sysroot.run(sysroot.host_make, 'install')

            del os.environ['CROSS_PREFIX']
            del os.environ['CC']
            del os.environ['CFLAGS']
            os.environ['PATH'] = original_path

        else:
            if sysroot.target_platform_name == 'ios':
                # Note that this doesn't create a library that can be used with
                # an x86-based simulator.
                os.environ['CFLAGS'] = '-fembed-bitcode -O3 -arch arm64 -isysroot ' + sysroot.apple_sdk

            sysroot.run('./configure', '--static',
                    '--prefix=' + sysroot.sysroot_dir)
            sysroot.run(sysroot.host_make)
            sysroot.run(sysroot.host_make, 'install')

            if sysroot.target_platform_name == 'ios':
                del os.environ['CFLAGS']
