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
import sys

# Check the version of Python as early as possible.
if sys.hexversion < 0x03050000:
    sys.stderr.write("pyqtdeploy requires Python v3.5 or later\n")
    sys.exit(1)


from setuptools import find_packages, setup


# Get the version number.
version_file_name = os.path.join('pyqtdeploy', 'version.py')
try:
    version_file = open(version_file_name)
    version = version_file.read().strip().split('\n')[0].split()[-1][1:-1]
    version_file.close()
except FileNotFoundError:
    # Provide a minimal version file.
    version = '0.0.dev0'
    version_file = open(version_file_name, 'w')
    version_file.write(
            'PYQTDEPLOY_RELEASE = \'%s\'\nPYQTDEPLOY_HEXVERSION = 0\n' %
                    version)
    version_file.close()

# Get the long description for PyPI.
with open('README') as readme:
    long_description = readme.read()

# Do the setup.
setup(
        name='pyqtdeploy',
        version=version,
        description='PyQt Application Deployment Tool',
        long_description=long_description,
        author='Riverbank Computing Limited',
        author_email='info@riverbankcomputing.com',
        url='https://www.riverbankcomputing.com/software/pyqtdeploy/',
        license='BSD',
        platforms=['X11', 'OS/X', 'Windows'],
        packages=find_packages(),
        package_data={
            'pyqtdeploy.builder': ['lib/*.*', 'lib/*/*.*'],
            'pyqtdeploy.sysroot.plugins.python': ['configurations/*.*',
                    'configurations/*/*.*']
        },
        entry_points={
            'console_scripts': [
                'pyqtdeploy-build = pyqtdeploy.pyqtdeploybuild_main:main',
                'pyqtdeploy-sysroot = pyqtdeploy.pyqtdeploysysroot_main:main'],
            'gui_scripts': [
                'pyqtdeploy = pyqtdeploy.pyqtdeploy_main:main']
        }
     )
