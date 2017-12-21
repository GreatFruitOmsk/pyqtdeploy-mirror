#!/usr/bin/env python3


###############################################################################
# Copyright (c) 2017 Riverbank Computing Limited.
###############################################################################


import sys
import sysconfig

from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QLabel, QTreeView, QVBoxLayout,
        QWidget)
from sip import SIP_VERSION_STR

try:
    from pdytools import hexversion as pdy_hexversion
except ImportError:
    pdy_hexversion = 0


# Try and import the platform-specific modules.
platform_module = "Not available"

try:
    import PyQt5.QtAndroidExtras
    platform_module = 'QtAndroidExtras'
except ImportError:
    pass

try:
    import PyQt5.QtMacExtras
    platform_module = 'QtMacExtras'
except ImportError:
    pass

try:
    import PyQt5.QtWinExtras
    platform_module = 'QtWinExtras'
except ImportError:
    pass

try:
    import PyQt5.QtX11Extras
    platform_module = 'QtX11Extras'
except ImportError:
    pass


# Try and import the optional products.
optional_products = []

try:
    import PyQt5.Qt3DCore
    optional_products.append("PyQt3D")
except ImportError:
    pass

try:
    import PyQt5.QtChart
    optional_products.append("PyQtChart")
except ImportError:
    pass

try:
    import PyQt5.QtDataVisualization
    optional_products.append("PyQtDataVisualization")
except ImportError:
    pass

try:
    import PyQt5.QtPurchasing
    optional_products.append("PyQtPurchasing")
except ImportError:
    pass

try:
    import PyQt5.Qsci
    optional_products.append("QScintilla")
except ImportError:
    pass


class View(QTreeView):
    """ A read-only view for displaying a model. """

    def __init__(self, title, model):
        """ Initialise the object. """

        super().__init__(windowTitle=title)

        self.setModel(model)
        self.setRootIsDecorated(False)
        self.setEditTriggers(self.EditTrigger(0))
        self.resizeColumnToContents(0)


class Model(QStandardItemModel):
    """ A model containing a collection of interesting values. """

    def __init__(self):
        """ Initialise the object. """

        super().__init__()

        self.setHorizontalHeaderLabels(["Name", "Value"])

        # Populate the model.
        self.add_value("Platform", sysconfig.get_platform())
        self.add_value("PyQt version", PYQT_VERSION_STR)
        self.add_value("Python version", self.from_hexversion(sys.hexversion))
        self.add_value("Qt version", QT_VERSION_STR)
        self.add_value("sip version", SIP_VERSION_STR)
        self.add_value("sys.platform", sys.platform)
        self.add_value("sys.path", str(sys.path))
        self.add_value("sys.path_hooks", str(sys.path_hooks))
        self.add_value("sys.meta_path", str(sys.meta_path))

        self.add_value("Platform module", platform_module)

        avail = "unavailable"
        try:
            import ssl

            avail = "available ({0})".format(ssl.OPENSSL_VERSION)
        except ImportError:
            pass

        self.add_value("Python SSL support", avail)

        avail = "unavailable"
        try:
            from PyQt5.QtNetwork import QSslSocket

            if QSslSocket.supportsSsl():
                avail = "available ({0})".format(
                        QSslSocket.sslLibraryVersionString())
        except ImportError:
            pass

        self.add_value("Qt SSL support", avail)

        for product in optional_products:
            self.add_value(product, "imported")

    def add_value(self, name, value):
        """ Add a name/value pair to the model. """

        self.appendRow([QStandardItem(name), QStandardItem(value)])

    @staticmethod
    def from_hexversion(hexversion):
        """ Convert a hexadecimal version number to a string. """

        return '%s.%s.%s' % ((hexversion >> 24) & 0xff,
                (hexversion >> 16) & 0xff, (hexversion >> 8) & 0xff)


# Create the GUI.
app = QApplication(sys.argv)

shell = QWidget()
shell_layout = QVBoxLayout()

header = QLabel("""<p>
This is a simple Python application using the PyQt bindings for the
cross-platform Qt application framework.
</p>
<p>
It will run on macOS, Linux, Windows, iOS and Android without changes to the
source code.
</p>
<p>
For more information about PyQt go to
<a href="https://www.riverbankcomputing.com">www.riverbankcomputing.com</a>.
</p>""")
header.setOpenExternalLinks(True)
header.setWordWrap(True)
shell_layout.addWidget(header)

view = View("PyQt Demo", Model())
shell_layout.addWidget(view)

if pdy_hexversion != 0:
    footer = QLabel("<p>It is a self-contained executable created using pyqtdeploy v%s.</p>" % Model.from_hexversion(pdy_hexversion))
    footer.setWordWrap(True)
    shell_layout.addWidget(footer)

shell.setLayout(shell_layout)

# Show the GUI and interact with it.
shell.show()
app.exec()

# All done.
sys.exit()
