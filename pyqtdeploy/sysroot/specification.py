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


import importlib
import json
import os
import shutil

from collections import OrderedDict

from ..user_exception import UserException
from .abstract_package import AbstractPackage


class Specification:
    """ Encapsulate the specification of a system root directory. """

    def __init__(self, spec_file, plugin_path, target_name):
        """ Initialise the object. """

        self.specification_file = os.path.abspath(spec_file)

        self.packages = []

        # Load the JSON file.
        with open(spec_file) as f:
            try:
                spec = json.load(f)
            except json.JSONDecodeError as e:
                raise UserException(
                        "{0}:{1}: {2}".format(spec_file, e.lineno, e.msg))

        # Do a high level parse and import the plugins.
        for name, value in spec.items():
            if name == 'Description':
                # Check its type even though we don't actually use it.
                if not isinstance(value, str):
                    self._bad_type(name, spec_file)
            else:
                # Find the package's plugin.
                plugin = None

                # Search any user specified directories.
                if plugin_path:
                    for plugin_dir in plugin_path.split(os.pathsep):
                        plugin = self._plugin_from_file(name, plugin_dir)
                        if plugin is not None:
                            break

                # Search the included plugin packages.
                if plugin is None:
                    # The name of the package root.
                    package_root = '.'.join(__name__.split('.')[:-1])

                    for package in ('.packages', '.packages.contrib'):
                        plugin = self._plugin_from_package(name, package,
                                package_root)
                        if plugin is not None:
                            break
                    else:
                        raise UserException(
                                "unable to find a plugin for '{0}'".format(
                                        name))

                # Create the package plugin.
                package = plugin()
                setattr(package, 'name', name)

                # Remove values unrelated to the target.
                if not isinstance(value, dict):
                    self._bad_type(name, spec_file)

                config = {}
                for opt_name, opt_value in value.items():
                    # Extract any scope.
                    parts = opt_name.split('#', maxsplit=1)
                    if len(parts) == 2:
                        scope, opt_name = parts

                        # Remember if we are negating.
                        if scope.startswith('!'):
                            negate = True
                            scope = scope[1:]
                        else:
                            negate = False

                        # See if the scope matches the target.  The scope may
                        # or may not include the word size.
                        if '-' in scope:
                            matches = (target_name == scope)
                        else:
                            matches = target_name.startswith(scope + '-')

                        if negate:
                            matches = not matches

                        # Ignore if it isn't relevant.
                        if not matches:
                            continue

                    # The value is relevant so save it.
                    config[opt_name] = opt_value

                # Parse the package-specific options.
                for cls in plugin.__mro__:
                    options = cls.__dict__.get('options')
                    if options:
                        self._parse_options(config, options, package, spec_file)

                    if cls is AbstractPackage:
                        break

                unused = config.keys()
                if unused:
                    self._parse_error(
                            "unknown value(s): {0}".format(', '.join(unused)),
                            spec_file, name)

                self.packages.append(package)

    def _plugin_from_file(self, name, plugin_dir):
        """ Try and load a package plugin from a file. """

        plugin_file = os.path.join(plugin_dir, name + '.py')
        spec = importlib.util.spec_from_file_location(name, plugin_file)
        plugin_module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(plugin_module)
        except FileNotFoundError:
            return None

        return self._plugin_from_module(name, plugin_module)

    def _plugin_from_package(self, name, package, package_root):
        """ Try and load a package plugin from a Python package. """

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

        for package_type in plugin_module.__dict__.values():
            if isinstance(package_type, type):
                if issubclass(package_type, AbstractPackage):
                    # Make sure the type is defined in the plugin and not
                    # imported by it.  Allow for a plugin implemented as a
                    # sub-package.
                    if package_type.__module__.split('.')[:len(fq_name_parts)] == fq_name_parts:
                        return package_type

        return None

    def _parse_options(self, json_array, options, package, spec_file):
        """ Parse a JSON array according to a set of options and add the
        corresponding values as attributes of a package object.
        """

        for option in options:
            value = json_array.get(option.name)

            if value is None:
                if option.required:
                    self._parse_error(
                            "'{0}' has not been specified".format(option.name),
                            spec_file, package.name)

                # Create a default value.
                value = option.type()
            elif not isinstance(value, option.type):
                self._bad_type(option.name, spec_file, package.name)

            setattr(package, option.name, value)

            try:
                del json_array[option.name]
            except KeyError:
                pass

    def _bad_type(self, name, spec_file, package_name=None):
        """ Raise an exception when an option name has the wrong type. """

        self._parse_error("value of '{0}' has an unexpected type".format(name),
                spec_file, package_name)

    def _parse_error(self, message, spec_file, package_name):
        """ Raise an exception for by an error in the specification file. """

        if package_name:
            exception = "{0}: Package '{1}': {2}".format(spec_file,
                    package_name, message)
        else:
            exception = "{0}: {1}".format(spec_file, message)

        raise UserException(exception)

    def show_options(self, packages, message_handler):
        """ Show the options for a sequence of packages. """

        headings = ("Package", "Option [*=required]", "Type", "Description")
        widths = [len(h) for h in headings]
        options = OrderedDict()

        # Collect the options for each package while working out the required
        # column widths.
        for package in packages:
            name_len = len(package.name)
            if widths[0] < name_len:
                widths[0] = name_len

            # Allow sub-classes to override super-classes.
            package_options = OrderedDict()

            for cls in type(package).__mro__:
                for option in cls.__dict__.get('options', []):
                    if option.name not in package_options:
                        package_options[option.name] = option

                        name_len = len(option.name)
                        if option.required:
                            name_len == 1

                        if widths[1] < name_len:
                            widths[1] = name_len

                if cls is AbstractPackage:
                    break

            options[package.name] = package_options

        # Display the formatted options.
        self._show_row(headings, widths, message_handler)

        ulines = ['-' * len(h) for h in headings]
        self._show_row(ulines, widths, message_handler)

        # Calculate the room available for the description column.
        avail = shutil.get_terminal_size()[0] - 1

        for w in widths[:-1]:
            avail -= 2 + w

        avail = max(avail, widths[-1])

        for package_name, package_options in options.items():
            package_col = package_name

            for option_name, option in package_options.items():
                if option.required:
                    option_name += '*'

                row = [package_col, option_name]

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

                # Don't repeat the package name.
                package_col = ''

    @staticmethod
    def _show_row(columns, widths, message_handler):
        """ Show one row of the options table. """

        row = ['{:{width}}'.format(columns[i], width=w) 
                for i, w in enumerate(widths)]

        message_handler.message('  '.join(row))
