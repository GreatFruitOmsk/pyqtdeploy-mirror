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
    ]

    def build(self, sysroot):
        """ Build zlib for the target. """

        sysroot.progress("Building zlib")

        # TODO: Consider adding support.  If not then move the zlib.json test
        # out of the common directory.
        if sysroot.target_platform_name == 'android':
            sysroot.error(
                    "building zlib for {0} is not supported".format(
                            sysroot.target_platform_name))

        archive = sysroot.find_file(self.source)
        sysroot.unpack_archive(archive)

        if sysroot.target_platform_name == 'win':
            sysroot.run(sysroot.host_make, '-f', 'win32\\Makefile.msc',
                    'zlib.lib')
            sysroot.copy_file('zconf.h', sysroot.target_include_dir)
            sysroot.copy_file('zlib.h', sysroot.target_include_dir)
            sysroot.copy_file('zlib.lib', sysroot.target_lib_dir)
        else:
            if sysroot.target_platform_name == 'ios':
                os.environ['CFLAGS'] = '-O3 -arch arm64 -isysroot ' + sysroot.apple_sdk

            sysroot.run('./configure', '--static',
                    '--prefix=' + sysroot.sysroot_dir)
            sysroot.run(sysroot.host_make)
            sysroot.run(sysroot.host_make, 'install')

            if sysroot.target_platform_name == 'ios':
                del os.environ['CFLAGS']
