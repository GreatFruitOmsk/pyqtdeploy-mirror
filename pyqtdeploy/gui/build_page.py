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


from PyQt5.QtWidgets import (QCheckBox, QGridLayout, QGroupBox, QMessageBox,
        QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from ..builder import Builder
from ..user_exception import UserException

from .exception_handlers import handle_user_exception


class BuildPage(QWidget):
    """ The GUI for the build page of a project. """

    # The page's label.
    label = "Build"

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self.project = None

        # Create the page's GUI.
        layout = QGridLayout()

        self._log = QPlainTextEdit(readOnly=True)
        layout.addWidget(self._log, 0, 0, 4, 1)

        build = QPushButton("Build", clicked=self._build)
        layout.addWidget(build, 0, 1)

        steps = QGroupBox("Additional Build Steps")
        steps_layout = QVBoxLayout()

        steps_layout.addWidget(QCheckBox("Run qmake"))
        steps_layout.addWidget(QCheckBox("Run make"))
        steps_layout.addWidget(QCheckBox("Run application"))

        steps.setLayout(steps_layout)
        layout.addWidget(steps, 1, 1)

        options = QGroupBox("Build Options")
        options_layout = QVBoxLayout()

        options_layout.addWidget(QCheckBox("Show console output"))
        options_layout.addWidget(QCheckBox("Verbose output"))

        options.setLayout(options_layout)
        layout.addWidget(options, 2, 1)

        layout.setRowStretch(3, 1)

        self.setLayout(layout)

    def _build(self, _):
        """ Invoked when the user clicks the build button. """

        project = self.project

        # Check the prerequisites.  Note that we don't disable the button if
        # these are missing because (as they are spread across the GUI) the
        # user would have difficulty knowing what needed fixing.
        if project.application_script == '':
            self._missing_prereq("main script file")
            return

        if project.python_host_interpreter == '':
            self._missing_prereq("host interpreter")
            return

        if project.application_script == '':
            self._missing_prereq("target Python include directory")
            return

        if project.application_script == '':
            self._missing_prereq("target Python library")
            return

        builder = Builder(project)

        try:
            builder.build()
        except UserException as e:
            handle_user_exception(e, self.label, self)

    def _missing_prereq(self, missing):
        """ Tell the user about a missing prerequisite. """

        QMessageBox.warning(self, self.label,
                "The project cannot be built because the name of the {0} has "
                        "not been set.".format(missing))
