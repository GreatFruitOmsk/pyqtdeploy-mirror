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


import glob
import os
import struct
import subprocess
import sys

from .user_exception import UserException


class Platform:
    """ Encapsulate a platform. """

    # The list of all platforms.
    all_platforms = []

    def __init__(self, full_name, name, archs):
        """ Initialise the object. """

        self.full_name = full_name
        self.name = name

        # Create the architectures.
        for arch in archs:
            Architecture(arch, self)

        self.all_platforms.append(self)

    @property
    def android_api(self):
        """ The number of the Android API.  None is returned if the platform
        doesn't have Android APIs, otherwise an exception is raised for any
        other sort of error.
        """

        # This default implementation does not support Android APIs.
        return None

    def configure(self):
        """ Configure the platform for building. """

        pass

    def deconfigure(self):
        """ Deconfigure the platform for building. """

        pass

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name

    def get_apple_sdk(self, message_handler):
        """ Return the name of the Apple SDK.  None is returned if the platform
        doesn't have Apple SDKs, otherwise an exception is raised for any other
        sort of error.
        """

        # This default implementation does not support Apple SDKs.
        return None

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        # Platforms that can be hosts must reimplement this.
        return None

    @classmethod
    def platform(cls, name):
        """ Return the singleton Platform instance for a platform.  A
        UserException is raised if the platform is unsupported.
        """

        for platform in cls.all_platforms:
            if platform.name == name:
                return platform

        raise UserException("'{0}' is not a supported platform.".format(name))

    @staticmethod
    def run(*args, message_handler, capture=False):
        """ Run a command, optionally capturing stdout. """

        message_handler.verbose_message("Running '{0}'".format(' '.join(args)))

        detail = None
        stdout = []

        try:
            with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True) as process:
                try:
                    while process.poll() is None:
                        line = process.stdout.readline()
                        if not line:
                            continue

                        if capture:
                            stdout.append(line)
                        else:
                            message_handler.verbose_message(line.rstrip())

                    if process.returncode != 0:
                        detail = "returned exit code {}".format(
                                process.returncode)

                except Exception as e:
                    process.kill()
        except Exception as e:
            detail = str(e)

        if detail:
            raise UserException("Execution failed: {}".format(detail))

        return ''.join(stdout).strip() if capture else None


class Architecture:
    """ Encapsulate an architecture. """

    # The list of all architectures.
    all_architectures = []

    def __init__(self, name, platform):
        """ Initialise the object. """

        self.name = name
        self.platform = platform

        self.all_architectures.append(self)

    def configure(self):
        """ Configure the architecture for building. """

        self.platform.configure()

    def deconfigure(self):
        """ Deconfigure the architecture for building. """

        self.platform.deconfigure()

    @classmethod
    def architecture(cls, name=None):
        """ Return a singleton Architecture instance for an architecture.  If
        name is None then the host architecture is returned.  A UserException
        is raised if the architecture is unsupported.
        """

        if name is None:
            if sys.platform == 'darwin':
                name = 'macos'
            elif sys.platform == 'win32':
                name = 'win'
            elif sys.platform.startswith('linux'):
                name = 'linux'
            else:
                raise UserException(
                        "'{0}' is not a supported host platform.".format(
                                sys.platform))

            name = '{0}-{1}'.format(name, 8 * struct.calcsize('P'))
        elif name.startswith('osx-'):
            # Map the deprecated values.  Such values can only come from the
            # command line.
            name = 'macos-' + name.split('-')[1]

        # Find the architecture instance.
        for arch in cls.all_architectures:
            if arch.name == name:
                return arch

            # If it is a platform then use the first architecture.
            if arch.platform.name == name:
                return arch

        raise UserException(
                "'{0}' is not a supported architecture.".format(name))

    def is_targeted(self, targets):
        """ Returns True if the architecture is covered by a set of targets.
        If the set of targets has a False value then the architecture is
        covered.  If the set of targets is a sequence of platform names then
        the architecture platform must appear in the sequence.  If the set of
        targets is a string then it is an expression of architecture or
        platform names which must contain the architecture or platform name.
        """

        if targets:
            if isinstance(targets, str):
                # See if the string is a '|' separated list of targets.
                targets = targets.split('|')
                if len(targets) == 1:
                    # There was no '|' so restore the original string.
                    targets = targets[0]

            if isinstance(targets, str):
                # String targets can come from the project file (ie. the user)
                # and so need to be validated.
                if targets[0] == '!':
                    # Note that this assumes that the target is a platform
                    # rather than an architecture.  If this is incorrect then
                    # it is a bug in the meta-data somewhere.
                    platform = Platform.platform(targets[1:])
                    covered = (self.platform is not platform)
                elif '-' in targets:
                    architecture = Architecture.architecture(targets)
                    covered = (self is architecture)
                else:
                    platform = Platform.platform(targets)
                    covered = (self.platform is platform)
            else:
                covered = (self.platform.name in targets)
        else:
            covered = True

        return covered


class ApplePlatform(Platform):
    """ Encapsulate an Apple platform. """

    @staticmethod
    def find_sdk(sdk_name, message_handler):
        """ Find an SDK to use. """

        sdk = Platform.run('xcrun', '--sdk', sdk_name, '--show-sdk-path',
                message_handler=message_handler, capture=True)

        if not sdk:
            raise UserException("A valid SDK could not be found")

        return sdk


# Define and implement the different platforms.  These should be done in
# alphabetical order.

class Android(Platform):
    """ Encapsulate the Android platform. """

    # This is the minimum API required by Python v3.6.
    MINIMUM_API = 21

    # The environment variables that should be set.
    REQUIRED_ENV_VARS = ['ANDROID_NDK_ROOT']

    def __init__(self):
        """ Initialise the object. """

        super().__init__("Android", 'android', ['android-32'])

    @property
    def android_api(self):
        """ The number of the Android API. """

        api = None

        ndk_platform = os.environ.get('ANDROID_NDK_PLATFORM')

        if ndk_platform:
            parts = ndk_platform.split('-')

            if len(parts) == 2 and parts[0] == 'android':
                try:
                    api = int(parts[1])
                except ValueError:
                    api = 0

                if api < self.MINIMUM_API:
                    api = None

        if api is None:
            raise UserException(
                    "Use the ANDROID_NDK_PLATFORM environment variable to specify an API level >= {0}.".format(self.MINIMUM_API))

        return api

    def configure(self):
        """ Configure the platform for building. """

        for name in self.REQUIRED_ENV_VARS:
            if name not in os.environ:
                raise UserException(
                        "The {0} environment variable must be set.".format(
                                name))

Android()


class iOS(ApplePlatform):
    """ Encapsulate the iOS platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("iOS", 'ios', ['ios-64'])

        self._original_deployment_target = os.environ.get(
                'IPHONEOS_DEPLOYMENT_TARGET')

    def configure(self):
        """ Configure the platform for building. """

        if self._original_deployment_target is None:
            # If not set then use the value that Qt uses.
            os.environ['IPHONEOS_DEPLOYMENT_TARGET'] = '8.0'

    def deconfigure(self):
        """ Deconfigure the platform for building. """

        if self._original_deployment_target is None:
            del os.environ['IPHONEOS_DEPLOYMENT_TARGET']
        else:
            os.environ['IPHONEOS_DEPLOYMENT_TARGET'] = self._original_deployment_target

    def get_apple_sdk(self, message_handler):
        """ The name of the iOS SDK. """

        return self.find_sdk('iphoneos', message_handler)

iOS()


class Linux(Platform):
    """ Encapsulate the Linux platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Linux", 'linux', ['linux-32', 'linux-64'])

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'

Linux()


class macOS(ApplePlatform):
    """ Encapsulate the macOS platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("macOS", 'macos', ['macos-64'])

        self._original_deployment_target = os.environ.get(
                'MACOSX_DEPLOYMENT_TARGET')

    def configure(self):
        """ Configure the platform for building. """

        if self._original_deployment_target is None:
            # If not set then use the value that Qt uses.
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = '10.10'

    def deconfigure(self):
        """ Deconfigure the platform for building. """

        if self._original_deployment_target is None:
            del os.environ['MACOSX_DEPLOYMENT_TARGET']
        else:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = self._original_deployment_target

    def get_apple_sdk(self, message_handler):
        """ The name of the macOS SDK. """

        return self.find_sdk('macosx', message_handler)

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'

macOS()


class Windows(Platform):
    """ Encapsulate the Windows platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Windows", 'win', ['win-32', 'win-64'])

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name + '.exe'

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        # Note that this will be wrong if we are targeting Android.
        return 'nmake'

Windows()
