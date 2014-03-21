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


from PyQt5.QtWidgets import (QButtonGroup, QCheckBox, QGridLayout, QGroupBox,
        QVBoxLayout, QWidget)


class PyQtPage(QWidget):
    """ The GUI for the PyQt configuration page of a project. """

    # The page's label.
    label = "PyQt Modules"

    # The PyQt modules.
    modules = ('QAxContainer', 'Qt', 'QtBluetooth', 'QtCore', 'QtDBus',
            'QtDesigner', 'QtGui', 'QtHelp', 'QtMacExtras', 'QtMultimedia',
            'QtMultimediaWidgets', 'QtNetwork', 'QtOpenGL', 'QtPositioning',
            'QtPrintSupport', 'QtQml', 'QtQuick', 'QtSensors', 'QtSerialPort',
            'QtSql', 'QtSvg', 'QtTest', 'QtWebKit', 'QtWebKitWidgets',
            'QtWidgets', 'QtWinExtras', 'QtX11Extras', 'QtXmlPatterns', 'uic')

    # The internal OpenGL modules.
    opengl_modules = ('_QOpenGLFunctions_ES2', '_QOpenGLFunctions_2_0')

    # The add-on modules.
    addon_modules = ('Qsci', 'QtChart', 'QtDataVisualization')

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

        # Create the page's GUI.
        layout = QVBoxLayout()

        self._modules_bg = self._create_button_group(layout,
                "Imported Modules", self.modules)
        self._opengl_modules_bg = self._create_button_group(layout,
                "Internal OpenGL Modules", self.opengl_modules)
        self._addon_modules_bg = self._create_button_group(layout,
                "Add-on Modules", self.addon_modules)
        layout.addStretch()

        self.setLayout(layout)

    def _create_button_group(self, layout, title, modules):
        """ Add a check box for each module to a layout and return a connected
        button group.
        """

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

    def _module_toggled(self, button, checked):
        """ Invoked when a module button is toggled. """

        project = self._project

        if checked:
            project.pyqt_modules.append(button.text())
        else:
            project.pyqt_modules.remove(button.text())

        project.modified = True

    def _update_page(self):
        """ Update the page using the current project. """

        self._update_button_group(self._modules_bg)
        self._update_button_group(self._opengl_modules_bg)
        self._update_button_group(self._addon_modules_bg)

    def _update_button_group(self, b_group):
        """ Update the state of a button group according to the current
        modules.
        """

        was_blocked = b_group.blockSignals(True)

        modules = self._project.pyqt_modules

        for b in b_group.buttons():
            b.setChecked(b.text() in modules)

        b_group.blockSignals(was_blocked)
