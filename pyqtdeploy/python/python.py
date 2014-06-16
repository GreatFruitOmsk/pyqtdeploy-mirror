# Copyright (c) 2014, Riverbank Computing Limited
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


import sys

from PyQt5.QtCore import QDir, QFile, QFileInfo, QIODevice

from ..user_exception import UserException


# The mapping of supported targets to Python platforms.
_TARGET_PYPLATFORM_MAP = {
    'linux':    'linux',
    'win':      'win32',
    'osx':      'darwin',
    'ios':      'darwin',
    'android':  'linux'
}


def configure_python(target, output):
    """ Write a configuration file for a particular package and target. """

    print("Configuring python for %s in %s" % (target, output))
    return

    # Get the package directory and check it is valid.
    package_qdir = _config_qdir()

    if not package_qdir.cd(package):
        raise UserException("{0} is not a supported package.".format(package))

    # Get the target platform.
    if target is None:
        # Default to the host platform.
        if sys.platform.startswith('linux'):
            target = 'linux'
        elif sys.platform == 'win32':
            target = 'win'
        elif sys.platform == 'darwin':
            target = 'osx'

    try:
        py_platform = _TARGET_PYPLATFORM_MAP[target]
    except KeyError:
        raise UserException("{0} is not a supported target.".format(target))

    # Make sure we have a name to write to.
    if output is None:
        output = _config_name(package, target)

    # See if there is a target-specific file.
    name = _config_name(package, target)
    if not package_qdir.exists(name):
        name = _config_name(package)
        if not package_qdir.exists(name):
            raise UserException("Internal error - no configuration file.")

    # Read the configuration file.
    config_qfile = QFile(package_qdir.absoluteFilePath(name))

    if not config_qfile.open(QIODevice.ReadOnly|QIODevice.Text):
        raise UserException(
                "Unable to open file {0}.".format(config_qfile.fileName()),
                config_qfile.errorString())

    config = config_qfile.readAll()
    config_qfile.close()

    # Expand any macros.
    config.replace('@PY_PLATFORM@', py_platform)

    # Write the output.
    output_qfile = QFile(output)

    if not output_qfile.open(QIODevice.WriteOnly|QIODevice.Text):
        raise UserException(
                "Unable to create file {0}.".format(output_qfile.fileName()),
                output_qfile.errorString())

    if output_qfile.write(config) < 0:
        raise UserException(
                "Unable to write to file {0}.".format(output_qfile.fileName()),
                output_qfile.errorString())

    output_qfile.close()


def show_targets():
    """ Write the list of supported targets to stdout. """

    print("Showing targets")
    return

    packages = _config_qdir().entryList(QDir.Dirs|QDir.NoDotAndDotDot,
            QDir.Name)

    for package in packages:
        print(package)


def _config_name(package, target=None):
    """ Return the name of a configuration file for a platform and optional
    target.
    """

    if target is None:
        return '{0}.cfg'.format(package)

    return '{0}-{1}.cfg'.format(package, target)


def _config_qdir():
    """ Return a QDir set to the directory containing the configuration files.
    """

    qdir = QFileInfo(__file__).absoluteDir()
    qdir.cd('configurations')

    return qdir
