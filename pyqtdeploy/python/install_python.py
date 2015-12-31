# Copyright (c) 2015, Riverbank Computing Limited
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

from ..file_utilities import parse_version
from ..targets import normalised_target
from ..user_exception import UserException
from .supported_versions import check_version


def install_python(target, sysroot, system_python, message_handler):
    """ Install Python into a sysroot for a particular target. """

    # Validate the target.
    target = normalised_target(target)

    # At the moment we only support Windows Python installed from an official
    # installer.
    if not target.startswith('win') or system_python is None or sys.platform != 'win32':
        raise UserException(
                "install only supports Windows Python installed from an "
                "official installer at the moment.")

    sysroot = os.path.abspath(sysroot)

    py_version = parse_version(system_python)

    if py_version == 0:
        raise UserException(
                "Invalid Python version {0}.".format(system_python))

    check_version(py_version)

    py_major = py_version >> 16
    py_minor = (py_version >> 8) & 0xff

    message_handler.progress_message(
            "Installing Python v{0}.{1} for {2} in {3}".format(
                    py_major, py_minor, target, sysroot))

    _install_windows_system_python(py_major, py_minor, sysroot)


def _install_windows_system_python(py_major, py_minor, sysroot):
    """ Install the Windows system Python. """

    import winreg
