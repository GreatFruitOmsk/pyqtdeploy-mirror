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


import os

from ... import AbstractPackage, PackageOption


class SIPPackage(AbstractPackage):
    """ The SIP package. """

    # The package-specific options.
    options = [
        PackageOption('source', str, required=True,
                help="The archive containing the SIP source code."),
    ]

    def build(self, sysroot):
        """ Build SIP for the target. """

        sysroot.progress("Building SIP")

        archive = sysroot.find_file(self.source)
        self._build_code_generator(sysroot, archive)
        self._build_module(sysroot, archive)

    def _build_code_generator(self, sysroot, archive):
        """ Build the code generator for the host. """

        sysroot.unpack_archive(archive)

        sysroot.run(sysroot.host_python, 'configure.py', '--bindir',
                sysroot.host_bin_dir)

        os.chdir('sipgen')
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')
        os.chdir('..')

    def _build_module(self, sysroot, archive):
        """ Build the static module for the target. """

        sysroot.unpack_archive(archive)

        # Create a configuration file.
        cfg = '''py_inc_dir = {0}
py_pylib_dir = {1}
sip_module_dir = {2}
'''.format(sysroot.target_py_include_dir, sysroot.target_lib_dir,
                sysroot.target_sitepackages_dir)

        cfg_name = 'sip-' + sysroot.target_name + '.cfg'

        with open(cfg_name, 'wt') as cfg_file:
            cfg_file.write(cfg)

        # Configure, build and install.
        sysroot.run(sysroot.host_python, 'configure.py', '--static',
                '--sysroot', sysroot.sysroot_dir, '--no-pyi', '--no-tools',
                '--use-qmake', '--configuration', cfg_name)
        sysroot.run(sysroot.host_qmake)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')
