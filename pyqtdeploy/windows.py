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


from .user_exception import UserException


def get_py_install_path(version, target):
    """ Return the name of the directory containing the root of the Python
    installation directory for a particular version and target.  It must not be
    called on a non-Windows platform.
    """

    from winreg import HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, QueryValue

    major, minor, _ = version
    reg_version = '{0}.{1}'.format(major, minor)
    if (major, minor) >= (3, 5) and target.name.endswith('-32'):
        reg_version += '-32'

    sub_key_user = 'Software\\Python\\PythonCore\\{}\\InstallPath'.format(
            reg_version)
    sub_key_all_users = 'Software\\Wow6432Node\\Python\\PythonCore\\{}\\InstallPath'.format(
            reg_version)

    queries = (
        (HKEY_CURRENT_USER, sub_key_user),
        (HKEY_LOCAL_MACHINE, sub_key_user),
        (HKEY_LOCAL_MACHINE, sub_key_all_users))

    for key, sub_key in queries:
        try:
            install_path = QueryValue(key, sub_key)
        except OSError:
            pass
        else:
            break
    else:
        raise UserException(
                "Unable to find an installation of Python v{0}.".format(
                        reg_version))

    return install_path
