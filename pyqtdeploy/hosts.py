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


import sys

from abc import ABC, abstractmethod

from .user_exception import UserException


class HostPlatform(ABC):
    """ Encapsulate a host platform. """

    def __init__(self, name):
        """ Initialise the object. """

        self._name = name

    @abstractmethod
    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

    @staticmethod
    def factory():
        """ Create an instance of the host platform. """

        if sys.platform == 'darwin':
            host = macOSHost()
        elif sys.platform == 'win32':
            host = WindowsHost()
        elif sys.platform.startswith('linux'):
            host = LinuxHost()
        else:
            raise UserException(
                    "'{0}' is not a supported host platform.".format(
                            sys.platform))

        return host

    @property
    @abstractmethod
    def make(self):
        """ The name of the make executable including any required path. """

    @property
    def name(self):
        """ The name of the host platform (using the same naming as the target
        platform).
        """

        return self._name


class WindowsHost(HostPlatform):
    """ The class that encapsulates a Windows host platform. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__('win')

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name + '.exe'

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        # Note that this will be wrong if we are targeting Android.
        return 'nmake'


class PosixHost(HostPlatform):
    """ The base class that encapsulates a POSIX based host platform. """

    def exe(self, name):
        """ Convert a generic executable name to a host-specific version. """

        return name

    @property
    def make(self):
        """ The name of the make executable including any required path. """

        return 'make'


class macOSHost(PosixHost):
    """ The class that encapsulates an macOS host. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__('macos')


class LinuxHost(PosixHost):
    """ The class that encapsulates a Linux host. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__('linux')
