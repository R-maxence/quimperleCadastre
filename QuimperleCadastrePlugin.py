# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
import os
import subprocess

from .about_dialog import *
from .main_dialog import *

class QuimperleCadastrePlugin:
    def __init__(self, iface):
        self.interface = iface
    def initGui(self):

        # definition du traitement
        iconMain = QIcon(os.path.dirname(__file__) + "/icons/quimperleCadastre.png")
        self.actionMain = QAction(iconMain, u"Traitement", self.interface.mainWindow())
        # QObject.connect(self.actionMain, SIGNAL("triggered()"), self.gereActionMain)
        self.actionMain.triggered.connect(self.gereActionMain)

        # definition de l'aide
        iconMain = QIcon(os.path.dirname(__file__) + "/icons/aide.png")
        self.ActionAide = QAction(iconMain, u"Aide", self.interface.mainWindow())
        # QObject.connect(self.actionMain, SIGNAL("triggered()"), self.gereActionMain)
        self.ActionAide.triggered.connect(self.gereActionAide)

        # definition de l'apropos
        iconMain = QIcon(os.path.dirname(__file__) + "/icons/a_propos.png")
        self.ActionApropos = QAction(iconMain, u"A propos", self.interface.mainWindow())
        # QObject.connect(self.actionMain, SIGNAL("triggered()"), self.gereActionMain)
        self.ActionApropos.triggered.connect(self.gereActionApropos)

        self.menuQuimperleCadastre = QMenu(u"Quimperle Cadastre")
        self.menuQuimperleCadastre.setIcon(QIcon(os.path.dirname(__file__) + "/icons/quimperleCadastre.png"))
        self.menuQuimperleCadastre.addAction(self.actionMain)  # Ajout de l'action de traitement
        self.menuQuimperleCadastre.addAction(self.ActionAide)  # Ajout de l'action d'aide
        self.menuQuimperleCadastre.addAction(self.ActionApropos)  # Ajout de l'action à propos
        self.interface.pluginMenu().addMenu(self.menuQuimperleCadastre)

        self.toolbarRechercheCommune = self.interface.addToolBar(u"Quimperle Cadastre")
        self.toolbarRechercheCommune.setObjectName("barreOutilQuimperle Cadastre")
        self.toolbarRechercheCommune.addAction(self.actionMain)


    def unload(self):
        self.interface.mainWindow().menuBar().removeAction(self.menuQuimperleCadastre.menuAction())
        self.interface.mainWindow().removeToolBar(self.toolbarRechercheCommune)


    #On appel la fenetre de traitement
    def gereActionMain(self):
        dlg = MainDialog(self.interface)
        # dlg.show() # ligne à mettre en commentaire pour avoir une fenêtre modale
        result = dlg.exec_()
        if result:
            pass

    #On appel la fenetre d'aide'
    def gereActionAide(self):
        dlg = MainDialog(self.interface)
        dlg.show() # ligne à mettre en commentaire pour avoir une fenêtre modale
        result = dlg.exec_()
        if result:
            pass

    #On appel la fenetre d'A prpos
    def gereActionApropos(self):
        dlg = DialogAbout(self.interface)
        #dlg.show()  # ligne à mettre en commentaire pour avoir une fenêtre modale
        result = dlg.exec_()
        if result:
            pass