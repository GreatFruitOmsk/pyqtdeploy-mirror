# Copyright (c) 2014 Riverbank Computing Limited.
#
# This file is part of pyqtdeploy.
#
# This file may be used under the terms of the GNU General Public License
# v2 or v3 as published by the Free Software Foundation which can be found in
# the files LICENSE-GPL2.txt and LICENSE-GPL3.txt included in this package.
# In addition, as a special exception, Riverbank gives you certain additional
# rights.  These rights are described in the Riverbank GPL Exception, which
# can be found in the file GPL-Exception.txt in this package.
#
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


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


    def _update_button_group(self, b_group):
        """ Update the state of a button group according to the current
        modules.
        """

        was_blocked = b_group.blockSignals(True)

        modules = self._project.pyqt_modules

        for b in b_group.buttons():
            b.setChecked(b.text() in modules)

        b_group.blockSignals(was_blocked)
