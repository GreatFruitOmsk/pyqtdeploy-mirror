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


import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractSlider, QApplication, QCheckBox,
        QGridLayout, QGroupBox, QMessageBox, QPlainTextEdit, QPushButton,
        QVBoxLayout, QWidget)

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

        self._builder_viewer = QPlainTextEdit(readOnly=True)
        layout.addWidget(self._builder_viewer, 0, 0, 4, 1)

        build = QPushButton("Build", clicked=self._build)
        layout.addWidget(build, 0, 1)

        steps = QGroupBox("Additional Build Steps")
        steps_layout = QVBoxLayout()

        self._run_qmake_button = QCheckBox("Run qmake",
                stateChanged=self._run_qmake_changed)
        steps_layout.addWidget(self._run_qmake_button)
        self._run_make_button = QCheckBox("Run make",
                stateChanged=self._run_make_changed)
        steps_layout.addWidget(self._run_make_button)
        self._run_application_button = QCheckBox("Run application",
                stateChanged=self._run_application_changed)
        steps_layout.addWidget(self._run_application_button)

        steps.setLayout(steps_layout)
        layout.addWidget(steps, 1, 1)

        options = QGroupBox("Build Options")
        options_layout = QVBoxLayout()

        self._clean_button = QCheckBox("Clean before building", checked=True)
        options_layout.addWidget(self._clean_button)
        self._console_button = QCheckBox("Capture console output")
        options_layout.addWidget(self._console_button)
        self._verbose_button = QCheckBox("Verbose output")
        options_layout.addWidget(self._verbose_button)

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

        builder = LoggingBuilder(project, self._builder_viewer)
        builder.verbose = bool(self._verbose_button.checkState())

        builder.clear()
        builder.status("Generating code...")

        try:
            builder.build(clean=bool(self._clean_button.checkState()),
                    console=bool(self._console_button.checkState()))
        except UserException as e:
            handle_user_exception(e, self.label, self)
            return

        builder.status("Code generation succeeded.")

        if self._run_qmake_button.checkState() != Qt.Unchecked:
            qmake = os.path.expandvars(project.qmake)

            if qmake == '':
                QMessageBox.warning(self, self.label,
                    "qmake cannot be run because its name has not been set.")
            else:
                builder.status("Running qmake...")

                try:
                    builder.run([qmake], "qmake failed.", in_build_dir=True)
                except UserException as e:
                    handle_user_exception(e, self.label, self)
                    return

                builder.status("qmake succeeded.")

        if self._run_make_button.checkState() != Qt.Unchecked:
            make = 'nmake' if sys.platform == 'win32' else 'make'

            builder.status("Running {0}...".format(make))

            try:
                builder.run([make], "{0} failed.".format(make),
                        in_build_dir=True)
            except UserException as e:
                handle_user_exception(e, self.label, self)
                return

            builder.status("{0} succeeded.".format(make))

        if self._run_application_button.checkState() != Qt.Unchecked:
            build_dir = project.absolute_path(project.build_dir)
            app_name = project.application_basename()

            if sys.platform == 'win32':
                application = os.path.join(build_dir, 'Release',
                        app_name + '.exe')
            elif sys.platform == 'darwin':
                application = os.path.join(build_dir, app_name + '.app',
                        'Contents', 'MacOS', app_name)
            else:
                application = os.path.join(build_dir, app_name)

            builder.status("Running {0}...".format(app_name))

            try:
                builder.run([application], "{0} failed.".format(application))
            except UserException as e:
                handle_user_exception(e, self.label, self)
                return

            builder.status("{0} succeeded.".format(app_name))

    def _missing_prereq(self, missing):
        """ Tell the user about a missing prerequisite. """

        QMessageBox.warning(self, self.label,
                "The project cannot be built because the name of the {0} has "
                        "not been set.".format(missing))

    def _run_qmake_changed(self, state):
        """ Invoked when the user clicks on the run qmake button. """

        if state == Qt.Unchecked:
            self._run_make_button.setCheckState(Qt.Unchecked)

    def _run_make_changed(self, state):
        """ Invoked when the user clicks on the run make button. """

        if state == Qt.Unchecked:
            self._run_application_button.setCheckState(Qt.Unchecked)
        else:
            self._run_qmake_button.setCheckState(Qt.Checked)

    def _run_application_changed(self, state):
        """ Invoked when the user clicks on the run application button. """

        if state != Qt.Unchecked:
            self._run_make_button.setCheckState(Qt.Checked)


class LoggingBuilder(Builder):
    """ A Builder that captures user messages and displays them in a widget.
    """

    def __init__(self, project, viewer):
        """ Initialise the object. """

        super().__init__(project)

        self._viewer = viewer

        self._default_format = self._viewer.currentCharFormat()

        self._error_format = self._viewer.currentCharFormat()
        self._error_format.setForeground(QColor('#7f0000'))

        self._status_format = self._viewer.currentCharFormat()
        self._status_format.setForeground(QColor('#007f00'))

    def clear(self):
        """ Clear the viewer. """

        self._viewer.setPlainText('')
        QApplication.processEvents()

    def status(self, text):
        """ Add some status text to the viewer. """

        self._append_text(text, self._status_format)

    def information(self, text):
        """ Reimplemented to handle information messages. """

        self._append_text(text, self._default_format)

    def error(self, text):
        """ Reimplemented to handle error messages. """

        self._append_text(text, self._error_format)

    def _append_text(self, text, char_format):
        """ Append text to the viewer using a specific character format. """

        viewer = self._viewer

        viewer.setCurrentCharFormat(char_format)
        viewer.appendPlainText(text)
        viewer.setCurrentCharFormat(self._default_format)

        # Make sure the new text is visible.
        viewer.verticalScrollBar().triggerAction(
                QAbstractSlider.SliderToMaximum)

        QApplication.processEvents()
