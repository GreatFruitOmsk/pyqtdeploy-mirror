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


from .metadata import Metadata


class PyQt4Metadata(Metadata):
    """ Encapsulate the meta-data for a single PyQt4 module. """

    def __init__(self, group='base', deps=(), qt=(), config=(), needs_suffix=True):
        """ Initialise the object. """

        super().__init__(group=group, deps=deps, qt=qt, config=config,
                needs_suffix=needs_suffix)


# The dictionary of meta-data for the PyQt4 modules.
pyqt4_metadata = {
    'QAxContainer':     PyQt4Metadata(
                            deps=['QtGui'],
                            config=['qaxcontainer']),

    'Qt':               PyQt4Metadata(),

    'QtCore':           PyQt4Metadata(
                            qt=['-gui']),

    'QtDBus':           PyQt4Metadata(
                            deps=['QtCore'],
                            qt=['dbus', '-gui']),

    'QtDeclarative':    PyQt4Metadata(
                            deps=['QtGui', 'QtNetwork'],
                            qt=['declarative', 'network']),

    'QtDesigner':       PyQt4Metadata(
                            deps=['QtGui'],
                            config=['designer']),

    'QtGui':            PyQt4Metadata(
                            deps=['QtCore']),

    'QtHelp':           PyQt4Metadata(
                            deps=['QtGui'],
                            config=['help']),

    'QtMultimedia':     PyQt4Metadata(
                            deps=['QtGui'],
                            qt=['multimedia']),

    'QtNetwork':        PyQt4Metadata(
                            deps=['QtCore'],
                            qt=['network', '-gui']),

    'QtOpenGL':         PyQt4Metadata(
                            deps=['QtGui'],
                            qt=['opengl']),

    'QtScript':         PyQt4Metadata(
                            deps=['QtCore'],
                            qt=['script', '-gui']),

    'QtScriptTools':    PyQt4Metadata(
                            deps=['QtGui', 'QtScript'],
                            qt=['scripttools', 'script']),

    'QtSql':            PyQt4Metadata(
                            deps=['QtGui'],
                            qt=['sql']),

    'QtSvg':            PyQt4Metadata(
                            deps=['QtGui'],
                            qt=['svg']),

    'QtTest':           PyQt4Metadata(
                            deps=['QtGui'],
                            qt=['testlib']),

    'QtWebKit':         PyQt4Metadata(
                            deps=['QtGui', 'QtNetwork'],
                            qt=['webkit', 'network']),

    'QtXml':            PyQt4Metadata(
                            deps=['QtCore'],
                            qt=['xml', '-gui']),

    'QtXmlPatterns':    PyQt4Metadata(
                            deps=['QtNetwork'],
                            qt=['xmlpatterns', '-gui', 'network']),

    'phonon':           PyQt4Metadata(
                            deps=['QtGui'],
                            qt=['phonon']),

    'uic':              PyQt4Metadata(
                            deps=['QtGui']),

    'QtChart':          PyQt4Metadata(
                            group='addon',
                            deps=['QtGui'],
                            config=['qtcommercialchart'],
                            needs_suffix=False),

    'Qsci':             PyQt4Metadata(
                            group='addon',
                            deps=['QtGui'],
                            config=['qscintilla2'],
                            needs_suffix=False),
}
