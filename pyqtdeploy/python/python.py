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
import sys

from ..file_utilities import (copy_embedded_file, get_embedded_dir,
        get_embedded_file_names)
from ..user_exception import UserException


# The mapping of supported targets to Python platforms.
_TARGET_PYPLATFORM_MAP = {
    'linux':    'linux',
    'win':      'win32',
    'osx':      'darwin',
    'ios':      'darwin',
    'android':  'linux'
}


def configure_python(target, output, message_handler):
    """ Configure a Python source directory for a particular target. """

    print("Configuring Python for %s in %s" % (target, output))
    return
    # Get the package directory and check it is valid.
    package_dir = get_embedded_dir(__file__, 'configurations', package)

    if package_dir is None:
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
    else:
        # Remove any target variant.
        target, _ = target.split('-', maxsplit=1)

    try:
        py_platform = _TARGET_PYPLATFORM_MAP[target]
    except KeyError:
        raise UserException("{0} is not a supported target.".format(target))

    # Make sure we have a name to write to.
    if output is None:
        output = _get_configuration_name(package, target)

    # See if there is a target-specific file.
    name = _get_configuration_name(package, target)
    if not package_dir.exists(name):
        name = _get_configuration_name(package)
        if not package_dir.exists(name):
            raise UserException("Internal error - no configuration file.")

    # Copy the configuration file.
    copy_embedded_file(package_dir.absoluteFilePath(name), output,
            macros={'@PY_PLATFORM@': py_platform})


def get_supported_targets():
    """ Return the list of supported targets. """

    # File names have the format 'pyconfig-TARGET.h'.
    return [os.path.basename(name)[9:-2]
            for name in get_embedded_file_names(__file__,
                    'configurations', 'pyconfig')]


def show_targets():
    """ Write the list of supported targets to stdout. """

    for target in sorted(get_supported_targets()):
        print(target)
