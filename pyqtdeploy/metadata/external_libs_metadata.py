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


class ExternalLibraryMetadata:
    """ Encapsulate the meta-data for an external C library used by the Python
    standard library.
    """

    def __init__(self, name, libs, user_name):
        """ Initialise the object. """

        # The well known internal identifier of the library.
        self.name = name

        # The default LIBS to add to the .pro file.
        self.libs = libs

        # The name of the library as presented to the user.
        self.user_name = user_name


# The meta-data for each external library that might be needed by the Python
# standard library..
external_libraries_metadata = (
    ExternalLibraryMetadata('crypt', '-lcrypt', "DES encryption library"),
    ExternalLibraryMetadata('ssl', '-lssl -lcrypto', "SSL encryption library"),
    ExternalLibraryMetadata('bz2', '-lbz2', "bz2 compression library"),
    ExternalLibraryMetadata('lzma', '-llzma', "LZMA compression library"),
    ExternalLibraryMetadata('zlib', '-lz', "zlib compression library"),
    ExternalLibraryMetadata('bsddb', '-ldb', "BSD db database library"),
    ExternalLibraryMetadata('dbm', '-lndbm', "dbm database library"),
    ExternalLibraryMetadata('gdbm', '-lgdbm', "gdbm database library"),
    ExternalLibraryMetadata('readline', '-lreadline -ltermcap',
            "readline library"),
    ExternalLibraryMetadata('curses', '-lcurses -ltermcap', "Curses library"),
    ExternalLibraryMetadata('panel', '-lpanel -lcurses',
            "Curses panel library"),
    ExternalLibraryMetadata('intl', '-lintl', "i18n library"),
    ExternalLibraryMetadata('math', '-lm', "Math library"),
    ExternalLibraryMetadata('nsl', '-lnsl', "Network services library"),
)
