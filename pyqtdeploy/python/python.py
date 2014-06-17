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


import os

from ..file_utilities import (copy_embedded_file, get_embedded_dir,
        get_embedded_file_names)
from ..user_exception import UserException


def configure_python(target, output, message_handler):
    """ Configure a Python source directory for a particular target. """

    # Avoid a circular import.
    from ..targets import normalised_target

    # Validate the target.
    target = normalised_target(target)

    # Get the name of the Python source directory and extract the Python
    # version.
    if output is None:
        output = '.'

    py_src_dir = os.path.abspath(output)
    _, py_version_str = os.path.basename(py_src_dir).split('-', maxsplit=1)

    while py_version_str != '' and not py_version_str[-1].isdigit():
        py_version_str = py_version_str[:-1]

    version_parts = py_version_str.split('.')

    if len(version_parts) == 2:
        version_parts.append('0')

    py_version = 0

    if len(version_parts) == 3:
        for part in version_parts:
            try:
                part = int(part)
            except ValueError:
                py_version = 0
                break

            py_version = (py_version << 8) + part

    if py_version == 0:
        raise UserException(
                "Unable to determine the Python version from the name of {0}.".format(py_src_dir))

    # Sanity check the version number.
    if py_version < 0x020600 or (py_version >= 0x030000 and py_version < 0x030300) or py_version >= 0x040000:
        raise UserException(
                "Python v{0} is not supported.".format(py_version_str))

    message_handler.verbose_message(
            "Configuring {0} as Python v{1} for {2}.".format(
                    py_src_dir, py_version_str, target))

    # Copy the modules config.c file.
    config_c_src_dir = get_embedded_dir(__file__, 'configurations')
    config_c_dst_file = os.path.join(py_src_dir, 'Modules', 'config.c')

    message_handler.verbose_message(
            "Installing {0}.".format(config_c_dst_file))

    copy_embedded_file(config_c_src_dir.absoluteFilePath('config.c'),
            config_c_dst_file)

    # Copy the pyconfig.h file.
    pyconfig_h_src_dir = get_embedded_dir(__file__, 'configurations',
            'pyconfig')
    pyconfig_h_dst_file = os.path.join(py_src_dir, 'pyconfig.h')

    message_handler.verbose_message(
            "Installing {0}.".format(pyconfig_h_dst_file))

    copy_embedded_file(
            pyconfig_h_src_dir.absoluteFilePath(
                    'pyconfig-{0}.h'.format(target)),
            pyconfig_h_dst_file)

def get_supported_targets():
    """ Return the list of supported targets. """

    # File names have the format 'pyconfig-TARGET.h'.
    return [os.path.basename(name)[9:-2]
            for name in get_embedded_file_names(__file__,
                    'configurations', 'pyconfig')]
