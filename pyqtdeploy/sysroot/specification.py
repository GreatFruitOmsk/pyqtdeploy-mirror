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


import collections
import importlib
import json
import os
import shutil

from collections import OrderedDict

from ..user_exception import UserException
from .component import ComponentBase


class Specification:
    """ Encapsulate the specification of a system root directory. """

    def __init__(self, specification_file, plugin_dirs, target):
        """ Initialise the object. """

        self._specification_file = specification_file

        self.components = []

        # Load the JSON file.
        with open(specification_file) as f:
            try:
                spec = json.load(f, object_pairs_hook=collections.OrderedDict)
            except json.JSONDecodeError as e:
                raise UserException(
                        "{0}:{1}: {2}".format(specification_file, e.lineno,
                                e.msg))

        # Do a high level parse and import the plugins.
        for name, value in spec.items():
            if name == 'Description':
                # Check its type even though we don't actually use it.
                if not isinstance(value, str):
                    self._bad_type(name)
            else:
                # Allow target-specific plugins.
                name = self._value_for_target(name, target)
                if name is None:
                    continue

                # Find the component's plugin.
                plugin = None

                # Search any user specified directories.
                if plugin_dirs:
                    for plugin_dir in plugin_dirs:
                        plugin = self._plugin_from_file(name, plugin_dir)
                        if plugin is not None:
                            break

                # Search the included plugin packages.
                if plugin is None:
                    # The name of the package root.
                    package_root = '.'.join(__name__.split('.')[:-1])

                    for package in ('.plugins', '.plugins.contrib'):
                        plugin = self._plugin_from_package(name, package,
                                package_root)
                        if plugin is not None:
                            break
                    else:
                        raise UserException(
                                "unable to find a plugin for '{0}'".format(
                                        name))

                # Remove values unrelated to the target.
                if not isinstance(value, dict):
                    self._bad_type(name)

                options_values = {}
                for opt_name, opt_value in value.items():
                    # Allow target-specific options.
                    opt_name = self._value_for_target(opt_name, target)
                    if opt_name is None:
                        continue

                    # The value is relevant so save it.
                    options_values[opt_name] = opt_value

                # Create the component plugin.
                component = plugin()
                setattr(component, 'name', name)
                setattr(component, '_options_values', options_values)

                self.components.append(component)

    def parse_options(self):
        """ Parse all the components' options. """

        for component in self.components:
            options_values = component._options_values

            # Parse the component-specific options.
            for cls in type(component).__mro__:
                options = cls.__dict__.get('options')
                if options:
                    self._parse_options(options_values, options, component)

                if cls is ComponentBase:
                    break

            unused = options_values.keys()
            if unused:
                self._parse_error(
                        "unknown option(s): {0}".format(', '.join(unused)),
                        component.name)

            del component._options_values

    @staticmethod
    def _value_for_target(value, target):
        """ If a value is valid for a particular target architecture then
        return the value, otherwise return None.
        """

        # Extract any scope.
        parts = value.split('#', maxsplit=1)
        if len(parts) != 2:
            # Any unscoped value is valid.
            return value

        scope, value = parts

        # A scope is a '|' separated list of target names.
        for name in scope.replace(' ', '').split('|'):
            # Remember if we are negating.
            if name.startswith('!'):
                negate = True
                name = name[1:]
            else:
                negate = False

            # See if the name matches the target (either architecture or
            # platform).
            if '-' in name:
                matches = (target.name == name)
            else:
                matches = (target.platform.name == name)

            if negate:
                matches = not matches

            # We only need one to match.
            if matches:
                return value

        return None

    def _plugin_from_file(self, name, plugin_dir):
        """ Try and load a component plugin from a file. """

        plugin_file = os.path.join(plugin_dir, name + '.py')
        spec = importlib.util.spec_from_file_location(name, plugin_file)
        plugin_module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(plugin_module)
        except FileNotFoundError:
            return None

        return self._plugin_from_module(name, plugin_module)

    def _plugin_from_package(self, name, package, package_root):
        """ Try and load a component plugin from a Python package. """

        rel_name = package + '.' + name

        try:
            plugin_module = importlib.import_module(rel_name,
                    package=package_root)
        except ImportError:
            return None

        return self._plugin_from_module(package_root + rel_name, plugin_module)

    def _plugin_from_module(self, fq_name, plugin_module):
        """ Get any plugin implementation from a module. """

        fq_name_parts = fq_name.split('.')

        for component_type in plugin_module.__dict__.values():
            if isinstance(component_type, type):
                if issubclass(component_type, ComponentBase):
                    # Make sure the type is defined in the plugin and not
                    # imported by it.  Allow for a plugin implemented as a
                    # sub-package.
                    if component_type.__module__.split('.')[:len(fq_name_parts)] == fq_name_parts:
                        return component_type

        return None

    def _parse_options(self, json_array, options, component):
        """ Parse a JSON array according to a set of options and add the
        corresponding values as attributes of a component object.
        """

        for option in options:
            value = json_array.get(option.name)

            if value is None:
                if option.required:
                    self._parse_error(
                            "'{0}' has not been specified".format(option.name),
                            component.name)

                # Create a default value.
                if option.default is None:
                    value = option.type()
                else:
                    value = option.default
            elif not isinstance(value, option.type):
                self._bad_type(option.name, component.name)
            elif option.values:
                if value not in option.values:
                    self._parse_error(
                            "'{0}' must have be one of these values: {1}".format(option.name, ','.join(option.values)),
                            component.name)

            setattr(component, option.name, value)

            try:
                del json_array[option.name]
            except KeyError:
                pass

    def _bad_type(self, name, component_name=None):
        """ Raise an exception when an option name has the wrong type. """

        self._parse_error("value of '{0}' has an unexpected type".format(name),
                component_name)

    def _parse_error(self, message, component_name):
        """ Raise an exception for by an error in the specification file. """

        if component_name:
            exception = "{0}: Component '{1}': {2}".format(
                    self._specification_file, component_name, message)
        else:
            exception = "{0}: {1}".format(self._specification_file, message)

        raise UserException(exception)

    def show_options(self, components, message_handler):
        """ Show the options for a sequence of components. """

        headings = ("Component", "Option [*=required]", "Type", "Description")
        widths = [len(h) for h in headings]
        options = OrderedDict()

        # Collect the options for each component while working out the required
        # column widths.
        for component in components:
            name_len = len(component.name)
            if widths[0] < name_len:
                widths[0] = name_len

            # Allow sub-classes to override super-classes.
            component_options = OrderedDict()

            for cls in type(component).__mro__:
                for option in cls.__dict__.get('options', []):
                    if option.name not in component_options:
                        component_options[option.name] = option

                        name_len = len(option.name)
                        if option.required:
                            name_len == 1

                        if widths[1] < name_len:
                            widths[1] = name_len

                if cls is ComponentBase:
                    break

            options[component.name] = component_options

        # Display the formatted options.
        self._show_row(headings, widths, message_handler)

        ulines = ['-' * len(h) for h in headings]
        self._show_row(ulines, widths, message_handler)

        # Calculate the room available for the description column.
        avail = shutil.get_terminal_size()[0] - 1

        for w in widths[:-1]:
            avail -= 2 + w

        avail = max(avail, widths[-1])

        for component_name, component_options in options.items():
            component_col = component_name

            for option_name, option in component_options.items():
                if option.required:
                    option_name += '*'

                row = [component_col, option_name]

                if option.type is int:
                    type_name = 'int'
                elif option.type is str:
                    type_name = 'str'
                elif option.type is bool:
                    type_name = 'bool'
                elif option.type is list:
                    type_name = 'list'
                elif option.type is dict:
                    type_name = 'dict'
                else:
                    type_name = "???"

                row.append(type_name)

                row.append('')
                line = ''
                for word in option.help.split():
                    if len(line) + len(word) < avail:
                        # There is room for the word on this line.
                        if line:
                            line += ' ' + word
                        else:
                            line = word
                    else:
                        if line:
                            # Show what we have so far.
                            row[-1] = line
                            line = word
                        else:
                            # The word is too long so truncate it.
                            row[-1] = word[:avail]

                        self._show_row(row, widths, message_handler)

                        # Make the row blank for the next word.
                        row = [''] * len(headings)

                if line:
                    # The last line.
                    row[-1] = line
                    self._show_row(row, widths, message_handler)

                # Don't repeat the component name.
                component_col = ''

    @staticmethod
    def _show_row(columns, widths, message_handler):
        """ Show one row of the options table. """

        row = ['{:{width}}'.format(columns[i], width=w) 
                for i, w in enumerate(widths)]

        message_handler.message('  '.join(row))
