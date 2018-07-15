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


class SIPComponent(ComponentBase):
    """ The SIP component. """

    # The component options.
    options = [
        ComponentOption('module_name',
                help="The qualified name of the sip module."),
        ComponentOption('source', required=True,
                help="The archive containing the SIP source code."),
    ]

    def build(self, sysroot):
        """ Build SIP for the target. """

        sysroot.progress("Building SIP")

        archive = sysroot.find_file(self.source)
        version_nr = sysroot.extract_version_nr(archive)

        # v4.19.9-12 have too many problems so it's easier to blacklist them.
        if version_nr >= 0x041309 and version_nr <= 0x04130c:
            sysroot.error("Please use SIP v4.19.13 or later")

        build_generator = os.path.join(os.getcwd(), 'sip-generator')
        build_module = os.path.join(os.getcwd(), 'sip-module')

        os.mkdir(build_generator)
        os.chdir(build_generator)
        self._build_code_generator(sysroot, archive, version_nr)

        os.mkdir(build_module)
        os.chdir(build_module)
        self._build_module(sysroot, archive, version_nr)

    def _build_code_generator(self, sysroot, archive, version_nr):
        """ Build the code generator for the host. """

        sysroot.building_for_target = False

        sysroot.unpack_archive(archive)

        args = [sysroot.host_python, 'configure.py', '--bindir',
                sysroot.host_bin_dir]

        if version_nr >= 0x04130c:
            # From v4.19.12 sip.h is considered part of the tools.
            args.extend(['--incdir', sysroot.target_py_include_dir,
                    '--no-module'])

        sysroot.run(*args)
        os.chdir('sipgen')
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')

        sysroot.building_for_target = True

    def _build_module(self, sysroot, archive, version_nr):
        """ Build the static module for the target. """

        sysroot.unpack_archive(archive)

        # Create a configuration file.
        cfg = '''py_inc_dir = {0}
py_pylib_dir = {1}
sip_module_dir = {2}
'''.format(sysroot.target_py_include_dir, sysroot.target_lib_dir,
                sysroot.target_sitepackages_dir)

        cfg_name = 'sip-' + sysroot.target_arch_name + '.cfg'

        with open(cfg_name, 'wt') as cfg_file:
            cfg_file.write(cfg)

        # Configure, build and install.
        args = [sysroot.host_python, 'configure.py', '--static', '--sysroot',
                sysroot.sysroot_dir, '--no-pyi', '--no-tools', '--use-qmake',
                '--configuration', cfg_name]

        if version_nr >= 0x041309:
            args.append('--no-dist-info')

        if self.module_name:
            args.extend(['--sip-module', self.module_name])

        sysroot.run(*args)
        sysroot.run(sysroot.host_qmake)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')
