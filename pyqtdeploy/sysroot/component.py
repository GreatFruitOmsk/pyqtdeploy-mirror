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


from abc import ABC, abstractmethod


class ComponentBase(ABC):
    """ The base class for the implementation of a component plugin. """

    # A sequence of ComponentOption instances describing the options that can
    # be specified for the component in the specification file.  These are made
    # available as attributes of the plugin instance.
    options = []

    @abstractmethod
    def build(self, sysroot):
        """ Build the component. """

    def configure(self, sysroot):
        """ Complete the configuration of the component. """


class ComponentOption:
    """ Encapsulate an option for the component in the specification file. """

    def __init__(self, name, type=str, required=False, default=None, values=None, help=''):
        """ Initialise the object. """

        self.name = name
        self.type = type
        self.required = required
        self.default = default
        self.values = values
        self.help = help if help else "None available."

        if values:
            self.help += " The possible values are: {0}.".format(
                    ', '.join([self._format_value(v) for v in values]))

        if default is not None:
            self.help += " The default value is {0}.".format(
                    self._format_value(default))

    def _format_value(self, value):
        """ Format a value according to the type of the option. """

        value = str(value)

        if self.type is not int:
            value = "'" + value + "'"

        return value
