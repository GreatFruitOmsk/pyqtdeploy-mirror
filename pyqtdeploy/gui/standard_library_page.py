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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QStackedWidget, QTabWidget

from .stdlib_extension_modules_subpage import StdlibExtensionModulesSubpage
from .stdlib_packages_subpage import StdlibPackagesSubpage


class StandardLibraryPage(QStackedWidget):
    """ The GUI for the standard library page of a project. """

    # The page's label.
    label = "Standard Library"

    @property
    def project(self):
        """ The project property getter. """

        return self._project

    @project.setter
    def project(self, value):
        """ The project property setter. """

        if self._project != value:
            self._project = value

            if self._update_page():
                self._packages.project = value
                self._extension_modules.project = value

            if self._tab_widget is None:
                self._tab_widget = self.parent().parent()
                self._tab_widget.currentChanged.connect(self._tab_changed)

    def __init__(self):
        """ Initialise the page. """

        super().__init__()

        self._project = None
        self._tab_widget = None

        # Create the page's GUI.
        self._sub_pages = QTabWidget()

        self._packages = StdlibPackagesSubpage()
        self._sub_pages.addTab(self._packages, self._packages.label)

        self._extension_modules = StdlibExtensionModulesSubpage()
        self._sub_pages.addTab(self._extension_modules,
                self._extension_modules.label)

        self.addWidget(self._sub_pages)

        self._warning = QLabel()
        self._warning.setAlignment(Qt.AlignCenter)
        self.addWidget(self._warning)

    def _update_page(self):
        """ Update the page using the current project.  Return True if the
        sub-pages are enabled.
        """

        project = self.project

        major, minor = project.python_target_version

        if major is None:
            warning_text = "The Python version cannot be obtained from the " \
                    "<b>Python library</b> field of the <b>Locations</b> tab."
        elif major == 3 and minor < 3:
            warning_text = "You seem to be using Python v{0}.{1}. When " \
                    "targetting Python v3, Python v3.3 or later is " \
                    "required.".format(major, minor)
        elif major == 2 and minor < 6:
            warning_text = "You seem to be using Python v{0}.{1}. When " \
                    "targetting Python v2, Python v2.6 or later is " \
                    "required.".format(major, minor)
        else:
            warning_text = ''

        if warning_text == '':
            self.setCurrentWidget(self._sub_pages)
            enabled = True
        else:
            self._warning.setText(warning_text)
            self.setCurrentWidget(self._warning)
            enabled = False

        return enabled

    def _tab_changed(self, idx):
        """ Invoked when the current tab of the containing widget changes. """

        if self._tab_widget.widget(idx) is self:
            self._update_page()
