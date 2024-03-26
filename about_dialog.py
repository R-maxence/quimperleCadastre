# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import sys, os

ui_path = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(ui_path, "forms")
about_ui, _ = uic.loadUiType(os.path.join(ui_path, "quimperleCadastre_about_form.ui"))


class DialogAbout(QDialog, about_ui):
    def __init__(self, interface):
        QDialog.__init__(self)
        self.setupUi(self)
        self.buttonBox.clicked.connect(self.clik_ok)
        self.setFixedSize(900, 1000)

    def clik_ok(self):
        QDialog.accept(self)