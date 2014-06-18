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

from .patch import apply_diff


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
    py_version = _extract_version(py_src_dir)

    if py_version == 0:
        raise UserException(
                "Unable to determine the Python version from the name of {0}.".format(py_src_dir))

    py_version_str = '{0}.{1}.{2}'.format(py_version >> 16,
            (py_version >> 8) & 0xff, py_version & 0xff)

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

    # Copy the most appropriate qmake .pro file.
    python_pro_src_file = _get_file_for_version('qmake', py_version)
    python_pro_dst_file = os.path.join(py_src_dir, 'python.pro')

    message_handler.verbose_message(
            "Installing {0}.".format(python_pro_dst_file))

    copy_embedded_file(python_pro_src_file, python_pro_dst_file)

    # Patch with the most appropriate diff.
    python_diff_src_file = _get_file_for_version('patches', py_version)

    message_handler.verbose_message("Patching {0}.".format(py_src_dir))

    apply_diff(python_diff_src_file, py_src_dir)


def get_supported_targets():
    """ Return the list of supported targets. """

    # File names have the format 'pyconfig-TARGET.h'.
    return [os.path.basename(name)[9:-2]
            for name in get_embedded_file_names(__file__,
                    'configurations', 'pyconfig')]


def _get_file_for_version(subdir, version):
    """ Return the name of a file in a sub-directory of the 'configurations'
    directory that is most appropriate for a particular version.
    """

    best_version = 0
    best_name = None

    for name in get_embedded_file_names(__file__, 'configurations', subdir):
        this_version = _extract_version(name)

        if this_version <= version and this_version > best_version:
            best_version = this_version
            best_name = name

    if best_version == 0:
        raise UserException(
                "Internal error", "No '{0}' file for version".format(subdir))

    return best_name


def _extract_version(name):
    """ Return a two or three part version number from the name of a file or
    directory.  0 is returned if a version number could not be extracted.
    """

    name, _ = os.path.splitext(os.path.basename(name))
    _, version_str = name.split('-', maxsplit=1)

    while version_str != '' and not version_str[-1].isdigit():
        version_str = version_str[:-1]

    version_parts = version_str.split('.')

    if len(version_parts) == 2:
        version_parts.append('0')

    version = 0

    if len(version_parts) == 3:
        for part in version_parts:
            try:
                part = int(part)
            except ValueError:
                version = 0
                break

            version = (version << 8) + part

    return version
