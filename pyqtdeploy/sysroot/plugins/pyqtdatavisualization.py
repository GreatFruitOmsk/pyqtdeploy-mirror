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


class PyQtDataVisualizationComponent(ComponentBase):
    """ The PyQtDataVisualization component. """

    # The component options.
    options = [
        ComponentOption('source', required=True,
                help="The archive containing the PyQtDataVisualization source code."),
    ]

    def build(self, sysroot):
        """ Build PyQtDataVisualization for the target. """

        sysroot.progress("Building PyQtDataVisualization")

        # Get the PyQt version number.
        pyqt5 = sysroot.find_component('pyqt5')
        pyqt5_archive = sysroot.find_file(pyqt5.source)
        pyqt5_version_nr = sysroot.extract_version_nr(pyqt5_archive)

        # Get this package's source and version number.
        archive = sysroot.find_file(self.source)
        version_nr = sysroot.extract_version_nr(archive)

        sysroot.unpack_archive(archive)

        # Create a configuration file.
        cfg = '''py_platform = {0}
py_inc_dir = {1}
py_pylib_dir = {2}
py_pylib_lib = {3}
py_sip_dir = {4}
[PyQt 5]
module_dir = {5}
'''.format(sysroot.target_pyqt_platform, sysroot.target_py_include_dir,
                sysroot.target_lib_dir, sysroot.target_py_lib,
                sysroot.target_sip_dir,
                os.path.join(sysroot.target_sitepackages_dir, 'PyQt5'))

        if pyqt5.disabled_features:
            cfg += 'pyqt_disabled_features = {0}\n'.format(
                    ' '.join(pyqt5.disabled_features))

        if pyqt5_version_nr >= 0x050b00:
            cfg += 'sip_module = PyQt5.sip\n'

        cfg_name = 'pyqtdatavisualization-' + sysroot.target_arch_name + '.cfg'

        with open(cfg_name, 'wt') as cfg_file:
            cfg_file.write(cfg)

        # Configure, build and install.
        args = [sysroot.host_python, 'configure.py', '--static', '--qmake',
            sysroot.host_qmake, '--sysroot', sysroot.sysroot_dir,
            '--no-qsci-api', '--no-sip-files', '--no-stubs', '--configuration',
            cfg_name, '--sip', sysroot.host_sip, '-c']

        if version_nr >= 0x050b00:
            args.append('--no-dist-info')

        if sysroot.verbose_enabled:
            args.append('--verbose')

        sysroot.run(*args)
        sysroot.run(sysroot.host_make)
        sysroot.run(sysroot.host_make, 'install')
