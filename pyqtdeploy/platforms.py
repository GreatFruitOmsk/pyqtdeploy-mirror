# Copyright (c) 2019, Riverbank Computing Limited
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
        for arch_name, arch_factory in archs:
            arch_factory(arch_name, self)

        self.all_platforms.append(self)

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
        """ Return the name of the Apple SDK. """

        raise NotImplementedError

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        # Platforms that can be hosts must reimplement this.
        raise NotImplementedError

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

    def configure(self):
        """ Configure the architecture for building. """

        self.platform.configure()

    def deconfigure(self):
        """ Deconfigure the architecture for building. """

        self.platform.deconfigure()

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

    def supported_target(self, target):
        """ Check that this architecture can host a target architecture. """

        # This default implementation checks that the architectures are the
        # same.
        return target is self


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


# Define and implement the different platforms and architectures.  These should
# be done in alphabetical order.

class AndroidArchitecture(Architecture):
    """ A base class for any Android architecture. """

    def configure(self):
        """ Configure the architecture for building. """

        # Configure the platform first.
        self.platform.configure()

        # Set the various property values.
        ndk_root = self.platform.ndk_root
        toolchain_version = self.platform.ndk_toolchain_version
        toolchain_prefix = self.android_toolchain_prefix
        android_host = '{}-x86_64'.format(
                'darwin' if sys.platform == 'darwin' else 'linux')

        self.android_ndk_sysroot = os.path.join(ndk_root, 'platforms',
                'android-{}'.format(self.platform.android_api), 'arch-arm')

        if not os.path.exists(self.android_ndk_sysroot):
            raise UserException("'{0}' does not exist, make sure ANDROID_NDK_ROOT and ANDROID_NDK_PLATFORM are set correctly".format(self.android_ndk_sysroot))

        # Assume the toolchain is gcc-based (as that is the historical
        # behaviour).
        self.android_toolchain_cflags = []

        self.android_toolchain_bin = os.path.join(ndk_root, 'toolchains',
                toolchain_prefix + toolchain_version, 'prebuilt',
                android_host, 'bin')

        if not os.path.exists(self.android_toolchain_bin):
            raise UserException("'{0}' does not exist, make sure ANDROID_NDK_ROOT and ANDROID_NDK_TOOLCHAIN_VERSION are set correctly".format(self.android_toolchain_bin))

        self.android_toolchain_cc = toolchain_prefix + 'gcc'

        if os.path.exists(os.path.join(self.android_toolchain_bin, self.android_toolchain_cc)):
            # The architecture-neutral C compiler flags.
            self.android_toolchain_cflags.append(
                    '--sysroot=' + self.android_ndk_sysroot)

            self.android_toolchain_cflags.extend(self.gcc_toolchain_cflags)
        else:
            # There is no gcc so assume we have a clang-based toolchain.
            gcc_toolchain_bin = self.android_toolchain_bin
            self.android_toolchain_bin = os.path.join(ndk_root, 'toolchains',
                    'llvm', 'prebuilt', android_host, 'bin')

            self.android_toolchain_cc = 'clang'

            # The architecture-neutral C compiler flags.
            self.android_toolchain_cflags.append('-gcc-toolchain')
            self.android_toolchain_cflags.append(gcc_toolchain_bin)

            sysroot = os.path.join(ndk_root, 'sysroot')
            self.android_toolchain_cflags.append('--sysroot=' + sysroot)

            self.android_toolchain_cflags.append('-isystem')
            self.android_toolchain_cflags.append(
                    os.path.join(sysroot, 'usr', 'include',
                    toolchain_prefix[:-1]))

            self.android_toolchain_cflags.extend(self.clang_toolchain_cflags)

    def supported_target(self, target):
        """ Check that this architecture can host a target architecture. """

        # Android can never be a host.
        return False


class Android_arm_32(AndroidArchitecture):
    """ Encapsulate the Android 32-bit Arm architecture. """

    @property
    def android_toolchain_prefix(self):
        """ The name of the Android toolchain's prefix. """

        return 'arm-linux-androideabi-'

    @property
    def clang_toolchain_cflags(self):
        """ The architecture-specific clang compiler flags. """

        return ['-target', 'armv7-none-linux-androideabi']


    @property
    def gcc_toolchain_cflags(self):
        """ The architecture-specific gcc compiler flags. """

        return ['-march=armv7-a', '-mfloat-abi=softfp', '-mfpu=vfp',
                '-fno-builtin-memmove', '-mthumb']


class Android(Platform):
    """ Encapsulate the Android platform. """

    # The environment variables that should be set.
    REQUIRED_ENV_VARS = ('ANDROID_NDK_ROOT', 'ANDROID_NDK_PLATFORM')

    def __init__(self):
        """ Initialise the object. """

        super().__init__("Android", 'android',
                [('android-32', Android_arm_32)])

    def configure(self):
        """ Configure the platform for building. """

        for name in self.REQUIRED_ENV_VARS:
            if name not in os.environ:
                raise UserException(
                        "The {0} environment variable must be set.".format(
                                name))

        self.ndk_root = os.environ['ANDROID_NDK_ROOT']

        self._original_toolchain_version = os.environ.get(
                'ANDROID_NDK_TOOLCHAIN_VERSION')

        if self._original_toolchain_version is None:
            self.ndk_toolchain_version = '4.9'
            os.environ['ANDROID_NDK_TOOLCHAIN_VERSION'] = self.ndk_toolchain_version
        else:
            self.ndk_toolchain_version = self._original_toolchain_version

        self._set_ndk_revision()
        self._set_api()

        # Blacklist r11-13 as they have problems finding standard library .h
        # files.  It is probably something simple, like a missing -I flag.
        if self.android_ndk_revision in (11, 12, 13):
            raise UserException(
                    "NDK r{0} is not supported.".format(
                            self.android_ndk_revision))

        # Force the gcc toolchain for r10 and earlier.
        self._original_qmakespec = os.environ.get('QMAKESPEC')
        os.environ['QMAKESPEC'] = 'android-g++' if self.android_ndk_revision <= 10 else 'android-clang'

    def deconfigure(self):
        """ Deconfigure the platform for building. """

        if self._original_qmakespec is None:
            del os.environ['QMAKESPEC']
        else:
            os.environ['QMAKESPEC'] = self._original_qmakespec

        if self._original_toolchain_version is None:
            del os.environ['ANDROID_NDK_TOOLCHAIN_VERSION']
        else:
            os.environ['ANDROID_NDK_TOOLCHAIN_VERSION'] = self._original_toolchain_version

    def _set_api(self):
        """ Set the number of the Android API. """

        api = None

        ndk_platform = os.environ['ANDROID_NDK_PLATFORM']

        if not os.path.isdir(os.path.join(self.ndk_root, 'platforms', ndk_platform)):
            raise UserException(
                    "NDK r{0} does not support {1}.".format(
                            self.android_ndk_revision, ndk_platform))

        parts = ndk_platform.split('-')

        if len(parts) == 2 and parts[0] == 'android':
            try:
                api = int(parts[1])
            except ValueError:
                api = None

        if api is None:
            raise UserException(
                    "Unable to determine the API level from the ANDROID_NDK_PLATFORM environment variable.")

        self.android_api = api

    def _set_ndk_revision(self):
        """ Set the revision number of the NDK. """

        revision_str = ''

        # source.properties is available from r11.
        source_properties = os.path.join(self.ndk_root, 'source.properties')
        if os.path.isfile(source_properties):
            with open(source_properties) as f:
                for line in f:
                    line = line.replace(' ', '')
                    parts = line.split('=')
                    if parts[0] == 'Pkg.Revision' and len(parts) == 2:
                        revision_str = parts[1].split('.')[0]
                        break
        else:
            # RELEASE.TXT is available in r10 and earlier.
            release_txt = os.path.join(self.ndk_root, 'RELEASE.TXT')
            if os.path.isfile(release_txt):
                with open(release_txt) as f:
                    for line in f:
                        if line.startswith('r'):
                            line = line[1:]
                            for i, ch in enumerate(line):
                                if not ch.isdigit():
                                    line = line[:i]
                                    break

                            revision_str = line

        try:
            self.android_ndk_revision = int(revision_str)
        except ValueError:
            self.android_ndk_revision = None

Android()


class iOS_arm_64(Architecture):
    """ Encapsulate the ios 64-bit Arm architecture. """

    def supported_target(self, target):
        """ Check that this architecture can host a target architecture. """

        # iOS can never be a host.
        return False


class iOS(ApplePlatform):
    """ Encapsulate the iOS platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("iOS", 'ios', [('ios-64', iOS_arm_64)])

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


class Linux_x86_32(Architecture):
    """ Encapsulate the Linux 32-bit x86 architecture. """

    pass


class Linux_x86_64(Architecture):
    """ Encapsulate the Linux 64-bit x86 architecture. """

    def supported_target(self, target):
        """ Check that this architecture can host a target architecture. """

        if target.platform.name == 'android':
            return True

        return super().supported_target(target)


class Linux(Platform):
    """ Encapsulate the Linux platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Linux", 'linux',
                [('linux-32', Linux_x86_32), ('linux-64', Linux_x86_64)])

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'

Linux()


class macOS_x86_64(Architecture):
    """ Encapsulate the macOS 64-bit x86 architecture. """

    def supported_target(self, target):
        """ Check that this architecture can host a target architecture. """

        if target.platform.name in ('android', 'ios'):
            return True

        return super().supported_target(target)


class macOS(ApplePlatform):
    """ Encapsulate the macOS platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("macOS", 'macos', [('macos-64', macOS_x86_64)])

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


class Windows_x86(Architecture):
    """ Encapsulate any Windows x86 architecture. """

    def supported_target(self, target):
        """ Check that this architecture can host a target architecture. """

        return target.platform is self.platform


class Windows(Platform):
    """ Encapsulate the Windows platform. """
    
    def __init__(self):
        """ Initialise the object. """
        
        super().__init__("Windows", 'win',
                [('win-32', Windows_x86), ('win-64', Windows_x86)])

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name + '.exe'

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'nmake'

Windows()
