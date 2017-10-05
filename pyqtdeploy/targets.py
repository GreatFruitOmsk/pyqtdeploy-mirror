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


import struct
import sys

from .user_exception import UserException


class TargetPlatform:
    """ Encapsulate a target platform and sub-architectures. """

    def __init__(self, full_name, name, archs, cpp, qmake_scope, subscopes=()):
        """ Initialise the object. """

        self.full_name = full_name
        self.name = name
        self._archs = archs
        self.cpp = cpp
        self.qmake_scope = qmake_scope
        self.subscopes = subscopes

    @staticmethod
    def find_platform(target_platform_name):
        """ Return the platform with the given name. """

        for platform in _TARGET_PLATFORMS:
            if platform.name == target_platform_name:
                return platform

        return None

    @staticmethod
    def get_host_platform_name():
        """ Return the well known name of the host platform. """

        if sys.platform.startswith('linux'):
            return 'linux'

        if sys.platform == 'win32':
            return 'win'

        if sys.platform == 'darwin':
            return 'macos'

        raise UserException(
                "'{0}' is not a supported host platform.".format(sys.platform))

    @staticmethod
    def get_platforms():
        """ Get the sequence of all supported platforms. """

        return _TARGET_PLATFORMS

    def is_native(self):
        """ Return True if the target platform is native. """

        return self.name == self.get_host_platform_name()


class TargetArch:
    """ Encapsulate a target architecture. """

    def __init__(self, name, qmake_scope, platform):
        """ Initialise the object. """

        self.name = name
        self.qmake_scope = qmake_scope
        self.platform = platform

    @classmethod
    def factory(cls, target_arch_name=None):
        """ Return a TargetArch instance for a target architecture.  If
        target_arch is None then the host platform is returned with '-32' or
        '-64' appended.  A UserException is raised if the target architecture
        is unsupported.
        """

        if target_arch_name is None:
            target_arch_name = '{0}-{1}'.format(
                    TargetPlatform.get_host_platform_name,
                    8 * struct.calcsize('P'))
        elif target_arch_name.startswith('osx-'):
            # Map the deprecated values.  Such values can only come from the
            # command line.
            target_arch_name = 'macos-' + target_arch_name.split('-')[1]

        # Find the target instance.
        arch = cls.find_arch(target_arch_name)

        if arch is None:
            raise UserException(
                    "'{0}' is not a supported target architecture.".format(
                            target_arch_name))

        return arch

    @staticmethod
    def find_arch(target_arch_name):
        """ Return the architecture with the given name. """

        for arch in _TARGET_ARCHITECTURES:
            if arch.name == target_arch_name:
                return arch

        return None


# The sequence of supported target platforms in alphabetical order.
_TARGET_PLATFORMS = (
    TargetPlatform("Android", 'android', ('android-32', ), 'Q_OS_ANDROID',
            'android'),
    TargetPlatform("iOS", 'ios', ('ios-64', ), 'Q_OS_IOS', 'ios'),
    TargetPlatform("Linux", 'linux', ('linux-32', 'linux-64'), 'Q_OS_LINUX',
            'linux-*'),
    TargetPlatform("macOS", 'macos', ('macos-64', ), 'Q_OS_MAC', 'macx'),
    TargetPlatform("Windows", 'win', ('win-32', 'win-64'), 'Q_OS_WIN', 'win32',
            ('win32:!contains(QMAKE_TARGET.arch, x86_64)',
                    'win32:contains(QMAKE_TARGET.arch, x86_64)'))
)


# The sequence of target architectures.
_TARGET_ARCHITECTURES = []

def _create_archs(platform):
    """ Create the archtitectures for a platform. """

    for a, arch in enumerate(platform._archs):
        if platform.subscopes:
            qmake_scope = platform.subscopes[a]
        else:
            qmake_scope = platform.qmake_scope

        _TARGET_ARCHITECTURES.append(TargetArch(arch, qmake_scope, platform))

for _platform in _TARGET_PLATFORMS:
    _create_archs(_platform)
