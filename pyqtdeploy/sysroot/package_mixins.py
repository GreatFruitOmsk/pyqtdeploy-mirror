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


from ..user_exception import UserException

from .abstract_package import PackageOption


class DebugPackageMixin:
    """ A mixin for a package that has a debug option. """

    # The options.
    options = [
        PackageOption('debug', bool,
                help="A debug version of the package is to be used."),
    ]


class OptionalSourcePackageMixin:
    """ A mixin for a package optionally built from source. """

    # The options.
    options = [
        PackageOption('source', str,
                help="The source archive to build the package from if an existing installation is not to be used."),
    ]


class SourcePackageMixin:
    """ A mixin for a package built from source. """

    # The options.
    options = [
        PackageOption('source', str, required=True,
                help="The source archive to build the package from."),
    ]


class PythonPackageMixin(OptionalSourcePackageMixin):
    """ A mixin for host and target Python packages. """

    # The options.
    options = [
        PackageOption('installed_version', str,
                help="The major.minor version number of an existing Python installation to use. If it is not specified then the installation will be built from source."),
    ]

    def get_windows_install_path(self, target_name):
        """ Return the name of the directory containing the root of the Python
        installation directory for an existing installation.  It must not be
        called on a non-Windows platform.
        """

        from ..windows import get_python_install_path

        py_major, py_minor = self.installed_version.split('.')
        reg_version = self.installed_version
        if int(py_major) == 3 and int(py_minor) >= 5 and target_name.endswith('-32'):
            reg_version += '-32'

        return get_python_install_path(reg_version)

    def validate_install_source_options(self):
        """ Validate the values of the 'installed_version' and 'source'
        options.  An exception is raised if there was an error.
        """

        if self.source:
            if self.installed_version:
                raise UserException(
                        "the 'installed_version' and 'source' options cannot both be specified")
        elif self.installed_version:
            parts = self.installed_version.split('.')
            if len(parts) != 2:
                raise UserException(
                        "'installed_version' option must be in the form major.minor and not '{0}'".format(self.installed_version))
        else:
            raise UserException(
                    "either the 'installed_version' or 'source' option must be specified")
