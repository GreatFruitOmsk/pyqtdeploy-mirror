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


from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QButtonGroup, QCheckBox, QGridLayout, QGroupBox,
        QStackedWidget, QVBoxLayout, QWidget)


class PyQtPage(QStackedWidget):
    """ The GUI for the PyQt configuration page of a project. """

    # The page's label.
    label = "PyQt Modules"

    class _PyQtModules:
        """ Encapsulate the PyQt modules for a particular version. """

        def __init__(self, modules=(), opengl_modules=(), addon_modules=()):
            """ Initialise the object. """

            self.modules = modules
            self.opengl_modules = opengl_modules
            self.addon_modules = addon_modules

    # The PyQt5 modules.
    _pyqt5_modules = _PyQtModules(
            modules=(
                'QAxContainer', 'Qt', 'QtBluetooth', 'QtCore', 'QtDBus',
                'QtDesigner', 'QtGui', 'QtHelp', 'QtMacExtras', 'QtMultimedia',
                'QtMultimediaWidgets', 'QtNetwork', 'QtOpenGL',
                'QtPositioning', 'QtPrintSupport', 'QtQml', 'QtQuick',
                'QtSensors', 'QtSerialPort', 'QtSql', 'QtSvg', 'QtTest',
                'QtWebKit', 'QtWebKitWidgets', 'QtWidgets', 'QtWinExtras',
                'QtX11Extras', 'QtXmlPatterns', 'uic'),
            opengl_modules=('_QOpenGLFunctions_ES2', '_QOpenGLFunctions_2_0'),
            addon_modules=('Qsci', 'QtChart', 'QtDataVisualization'))

    # The PyQt4 modules.
    _pyqt4_modules = _PyQtModules(
            modules=(
                'QAxContainer', 'Qt', 'QtCore', 'QtDBus', 'QtDeclarative',
                'QtDesigner', 'QtGui', 'QtHelp', 'QtMultimedia', 'QtNetwork',
                'QtOpenGL', 'QtScript', 'QtScriptTools', 'QtSql', 'QtSvg',
                'QtTest', 'QtWebKit', 'QtXml', 'QtXmlPatterns', 'phonon',
                'uic'),
            addon_modules=('Qsci', 'QtChart'))

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value
            self._update_page()

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None

        # Create the stacked pages for each PyQt version.
        self._pyqt5_page = _PyQtVersionPage(self._pyqt5_modules)
        self.addWidget(self._pyqt5_page)

        self._pyqt4_page = _PyQtVersionPage(self._pyqt4_modules)
        self.addWidget(self._pyqt4_page)

    @pyqtSlot(bool)
    def set_pyqt_version(self, is_pyqt5):
        """ Configure the page according to the PyQt version. """

        page = self._pyqt5_page if is_pyqt5 else self._pyqt4_page
        page.update_project()
        self.setCurrentWidget(page)

    def _update_page(self):
        """ Update the page using the current project. """

        project = self._project

        self._pyqt5_page.project = project
        self._pyqt4_page.project = project

        if project.application_is_pyqt5:
            self._pyqt5_page.configure()
            self._pyqt4_page.clear()

            self.setCurrentWidget(self._pyqt5_page)
        else:
            self._pyqt5_page.clear()
            self._pyqt4_page.configure()

            self.setCurrentWidget(self._pyqt4_page)


class _PyQtVersionPage(QWidget):
    """ The GUI for a PyQt version specific configuration page. """

    def __init__(self, modules):
        """ Initialise the page. """

        super().__init__()

        self._modules = modules
        self.project = None

        # Create the page's GUI.
        layout = QVBoxLayout()

        self._modules_bg = self._create_button_group(layout,
                "Imported Modules", self._modules.modules)
        self._opengl_modules_bg = self._create_button_group(layout,
                "Internal OpenGL Modules", self._modules.opengl_modules)
        self._addon_modules_bg = self._create_button_group(layout,
                "Add-on Modules", self._modules.addon_modules)
        layout.addStretch()

        self.setLayout(layout)

    def update_project(self):
        """ Update the project to contain the currently selected modules. """

        modules = self.project.pyqt_modules

        del modules[:]

        for b in self._get_buttons():
            if b.isChecked():
                modules.append(b.text())

    def configure(self):
        """ Update the page according to modules specified in the project. """

        modules = self.project.pyqt_modules

        self._block_signals(True)

        for b in self._get_buttons():
            b.setChecked(b.text() in modules)

        self._block_signals(False)

    def clear(self):
        """ Deselect all modules. """

        self._block_signals(True)

        for b in self._get_buttons():
            b.setChecked(False)

        self._block_signals(False)

    def _create_button_group(self, layout, title, modules):
        """ Add a check box for each module to a layout and return a connected
        button group.
        """

        if len(modules) == 0:
            return None

        b_group = QButtonGroup(exclusive=False)
        imports = QGroupBox(title)
        grid = QGridLayout()

        row = column = 0
        for m in modules:
            b = QCheckBox(m)

            b_group.addButton(b)
            grid.addWidget(b, row, column)

            column += 1
            if column == 5:
                row += 1
                column = 0

        imports.setLayout(grid)
        layout.addWidget(imports)

        b_group.buttonToggled.connect(self._module_toggled)

        return b_group

    def _get_buttons(self):
        """ A generator that returns all of the buttons in the page. """

        if self._modules_bg is not None:
            for b in self._modules_bg.buttons():
                yield b

        if self._opengl_modules_bg is not None:
            for b in self._opengl_modules_bg.buttons():
                yield b

        if self._addon_modules_bg is not None:
            for b in self._addon_modules_bg.buttons():
                yield b

    def _block_signals(self, block):
        """ Block (or unblock) all button group signals. """

        if self._modules_bg is not None:
            self._modules_bg.blockSignals(block)

        if self._opengl_modules_bg is not None:
            self._opengl_modules_bg.blockSignals(block)

        if self._addon_modules_bg is not None:
            self._addon_modules_bg.blockSignals(block)

    def _module_toggled(self, button, checked):
        """ Invoked when a module button is toggled. """

        if checked:
            self.project.pyqt_modules.append(button.text())
        else:
            self.project.pyqt_modules.remove(button.text())

        self.project.modified = True
