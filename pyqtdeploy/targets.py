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


import glob
import struct
import sys

from .user_exception import UserException


class TargetPlatform:
    """ Encapsulate a target platform and sub-architectures. """

    # The list of all platforms.
    platforms = []

    def __init__(self, full_name, name, archs, cpp, qmake_scope, subscopes=()):
        """ Initialise the object. """

        self.full_name = full_name
        self.name = name
        self.cpp = cpp
        self.qmake_scope = qmake_scope

        for a, arch in enumerate(archs):
            qmake_scope = subscopes[a] if subscopes else qmake_scope

            TargetArch(arch, qmake_scope, self)

        self.platforms.append(self)

    @classmethod
    def find_platform(cls, target_platform_name):
        """ Return the platform with the given name. """

        for platform in cls.platforms:
            if platform.name == target_platform_name:
                return platform

        return None

    def get_apple_sdk(self, user_sdk):
        """ Return the name of a target-specific Apple SDK.  None is returned
        if the platform doesn't have Apple SDKs, otherwise an exception is
        raised for any other sort of error.
        """

        # This default implementation does not support Apple SDKs.
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

    def is_native(self):
        """ Return True if the target platform is native. """

        return self.name == self.get_host_platform_name()


class TargetArch:
    """ Encapsulate a target architecture. """

    # The list of all architectures.
    architectures = []

    def __init__(self, name, qmake_scope, platform):
        """ Initialise the object. """

        self.name = name
        self.qmake_scope = qmake_scope
        self.platform = platform

        self.architectures.append(self)

    @classmethod
    def factory(cls, target_arch_name=None):
        """ Return a TargetArch instance for a target architecture.  If
        target_arch is None then the host platform is returned with '-32' or
        '-64' appended.  A UserException is raised if the target architecture
        is unsupported.
        """

        if target_arch_name is None:
            target_arch_name = '{0}-{1}'.format(
                    TargetPlatform.get_host_platform_name(),
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

    @classmethod
    def find_arch(cls, target_arch_name):
        """ Return the architecture with the given name. """

        for arch in cls.architectures:
            if arch.name == target_arch_name:
                return arch

        return None


class AppleTargetPlatform(TargetPlatform):
    """ Encapsulate an Apple target platform. """

    @staticmethod
    def find_sdk(user_sdk, sdk_name):
        """ Find an SDK to use. """

        if user_sdk and '/' in user_sdk:
            # The user specified an explicit path so use it.
            sdk = user_sdk
            if not os.path.isdir(sdk):
                sdk = None
        else:
            sdk_dirs = (
                '/Applications/Xcode.app/Contents/Developer/Platforms/%s.platform/Developer/SDKs' % sdk_name,
                '/Developer/SDKs'
            )

            pattern = '/%s*.sdk' % sdk_name

            for sdk_dir in sdk_dirs:
                if os.path.isdir(sdk_dir):
                    if user_sdk:
                        sdk = os.path.join(sdk_dir, user_sdk)
                    else:
                        # Use the latest SDK we find.
                        sdks = glob.glob(sdk_dir + pattern)
                        if len(sdks) == 0:
                            sdk = None
                        else:
                            sdks.sort()
                            sdk = sdks[-1]

                    break
            else:
                sdk = None

        if sdk is None:
            raise UserException(
                    "A valid SDK was not specified or could not be found")

        return sdk


# Define and implement the different platforms.  These should be done in
# alphabetical order.

class Android(TargetPlatform):
    """ Encapsulate the Android platform. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__("Android", 'android', ('android-32', ),
                'Q_OS_ANDROID', 'android')

Android()


class iOS(AppleTargetPlatform):
    """ Encapsulate the iOS platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("iOS", 'ios', ('ios-64', ), 'Q_OS_IOS', 'ios')


class Linux(TargetPlatform):
    """ Encapsulate the Linux platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Linux", 'linux', ('linux-32', 'linux-64'),
                'Q_OS_LINUX', 'linux-*')

Linux()


class macOS(AppleTargetPlatform):
    """ Encapsulate the macOS platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("macOS", 'macos', ('macos-64', ), 'Q_OS_MAC', 'macx')

    def get_apple_sdk(self, user_sdk):
        """ Return the name of a target-specific Apple SDK. """

        return self.find_sdk(user_sdk, 'MacOSX')

macOS()


class Windows(TargetPlatform):
    """ Encapsulate the Windows platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Windows", 'win', ('win-32', 'win-64'), 'Q_OS_WIN',
                'win32', ('win32:!contains(QMAKE_TARGET.arch, x86_64)',
                        'win32:contains(QMAKE_TARGET.arch, x86_64)'))

Windows()
