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


from PyQt5.QtWidgets import (QFileDialog, QHBoxLayout, QLineEdit, QStyle,
        QToolButton)


class FilenameEditor(QHBoxLayout):
    """ A simple file name editor suitable to be added to a layout. Filenames
    are relative to the project if possbile.
    """

    def __init__(self, caption, directory=False, **kwds):
        """ Initialise the editor. """

        super().__init__()

        self._project = None
        self._caption = caption
        self._directory = directory

        self._line_edit = QLineEdit(**kwds)
        self.addWidget(self._line_edit)

        icon = self._line_edit.style().standardIcon(
                QStyle.SP_DirIcon if self._directory else QStyle.SP_FileIcon)

        self.addWidget(QToolButton(icon=icon, clicked=self._browse))

    def setProject(self, project):
        """ Set the project. """

        self._project = project

    def setText(self, text):
        """ Set the text of the embedded QLineEdit. """

        self._line_edit.setText(text)

    def _browse(self, value):
        """ Invoked when the user clicks on the browse button. """

        orig = default = self._line_edit.text()
        if default != '' and self._project is not None:
            default = self._project.absolute_path(default)

        if self._directory:
            name = QFileDialog.getExistingDirectory(self._line_edit,
                    self._caption, default)
        else:
            name, _ = QFileDialog.getOpenFileName(self._line_edit,
                    self._caption, default)

        if name != '':
            if self._project is not None:
                name = self._project.relative_path(name)

            if name != orig:
                self._line_edit.setText(name)
                self._line_edit.textEdited.emit(name)
