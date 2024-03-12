# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import time
from PyQt5 import uic
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import sys, os

# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")
# from main_form import *
ui_path = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(ui_path, "forms")
form_action1, _ = uic.loadUiType(os.path.join(ui_path, "fenetre1_testDesignV0.1.ui"))


class MainDialog(QDialog, form_action1):
    def __init__(self, interface):
        QWidget.__init__(self)
        self.setupUi(self)

        self.cb_choixLayerInterscet.currentIndexChanged.connect(self.RecupererCoucheDansProjets)
        self.RemplirComboBox()

        # self.CB_enti_selection.isChecked.connect(self.EntiteSelectionner)
        # self.RemplirComboBox()

        #gestion des clics
        self.pb_aide.clicked.connect(self.ouvrirAide)
        self.pb_choixscr.clicked.connect(self.choixScr)
        self.pb_folderFinder.clicked.connect(self.saveFolder)
        self.le_exitPath.textChanged.connect(self.pathFolder)
        self.cb_choixscr.setCurrentIndex(-1) #on s'assure qu'on affiche une valeur blank par défaut sur la cb box

        #Sur Pyqt, il est obligatoire de renseigner un signal à un slot uniquement, d'où la redondance des lignes suivantes
        self.pb_ok.clicked.connect(self.exportSelectionVecto)#click sur OK = lancement des exports avec les formats cochés au répertoire souhaité
        self.pb_ok.clicked.connect(self.exportSelectionFields)

        #gestion des entrées utilisateur pour la combo box des SCR
        self.cb_choixscr.currentTextChanged.connect(self.choixScrCb)

        #récupère l'instance du projet courant
        project = QgsProject.instance()

        #récupère le système de référence spatiale (CRS) du projet
        crs = project.crs()

        #transforme le code EPSG du CRS sous forme de chaîne de caractères
        epsg_code = crs.authid()

        #Met à jour le texte du QLabel avec le code EPSG
        self.label_scr.setText(epsg_code)


    #Fonction pour sauvegarder lors du click boutons le repertoire
    def saveFolder(self):
        self.Folder = QFileDialog.getExistingDirectory(self)
        self.Folder = self.Folder + "/"
        self.le_exitPath.setText(self.Folder)

    #fonction pour enregistrer lors de l'écriture dans le QlineEdit
    def pathFolder(self):
        self.Folder = self.le_exitPath.text()
        self.Folder = self.Folder.replace('\\', '/')
        self.Folder = self.Folder + '/' #sinon on se retrouve dans le dossier du dessus
        #print(self.Folder)

    #A faire : réussir à désigner spécifiquement l'attributaire
    def exportSelectionFields(self):
        layer = iface.mapCanvas().currentLayer()  # désigne la couche que tu veux du coup
        if self.cb_xls.isChecked():
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.Folder, 'XLS')
            if error == QgsVectorFileWriter.NoError:
                print("L'exportation a réussi.")
            else:
                print(f"Erreur d'exportation : {message}")

        if self.cb_csv.isChecked():
            layer = iface.mapCanvas().currentLayer()  # désigne la couche que tu veux du coup
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.Folder, 'UTF-8',driverName='CSV')
            if error == QgsVectorFileWriter.NoError:
                print("L'exportation a réussi.")
            else:
                print(f"Erreur d'exportation : {message}")

        if self.cb_ods.isChecked():
            layer = iface.mapCanvas().currentLayer()  # désigne la couche que tu veux du coup
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.Folder, 'UTF-8',driverName='ODS')
            if error == QgsVectorFileWriter.NoError:
                print("L'exportation a réussi.")
            else:
                print(f"Erreur d'exportation : {message}")
        return

    #A faire : réussir à désigner spécifiquement le vecto souhaité
    def exportSelectionVecto(self):
        layer = iface.mapCanvas().currentLayer()  # désigne la couche que tu veux du coup
        print(self.Folder)
        if self.cb_shp.isChecked():
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.Folder, 'UTF-8',driverName='ESRI Shapefile')
            if error == QgsVectorFileWriter.NoError:
                print("L'exportation a réussi.")
            else:
                print(f"Erreur d'exportation : {message}")

        if self.cb_geopackage.isChecked():
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.Folder, 'UTF-8',driverName='GPKG')
            if error == QgsVectorFileWriter.NoError:
                print("L'exportation a réussi.")
            else:
                print(f"Erreur d'exportation : {message}")

        if self.cb_geoJson.isChecked():
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, self.Folder, 'UTF-8',driverName='GeoJSON')
            if error == QgsVectorFileWriter.NoError:
                print("L'exportation a réussi.")
            else:
                print(f"Erreur d'exportation : {message}")

    def choixScrCb(self):
        #affichage de la sélection
        selected_scr_cbox = self.cb_choixscr.currentText()
        self.label_scr.setText(selected_scr_cbox)

        #récupération de l'epsg pour l'utiliser lors de l'export
        #print(type(selected_scr_cbox))
        split = selected_scr_cbox.split(" ") #renvoie une liste

        #print(split, "Je suis le split")
        self.epsg_code = split[0] #récupération de l'EPSG
        print(self.epsg_code)

    def choixScr(self):
        dialog = QgsProjectionSelectionDialog()
        dialog.exec_()

        if dialog.exec_():
            UsersScr = dialog.crs().authid()
            crsDescription = dialog.crs().description()
            #print(type(UsersScr), " test 1")
            #print(type(crsDescription), " test 2")
            concatenate = UsersScr + " " + crsDescription

            print(concatenate)
            #met a jour le label en fonction du choix si utilisation de "autre" scr
            self.label_scr.setText(concatenate)

            index = self.cb_choixscr.findText(concatenate)#on cherche l'index où le texte du scr choisis se situe, si n'existe pas renvoie -1

            if index == -1:
                #On ajoute dans la première ligne de notre cbbox le SCR sélectionné pour visualisation / compréhension
                self.cb_choixscr.insertItem(0, concatenate)
                self.cb_choixscr.setCurrentIndex(0)  #On se positionne sur l'item

            else:
                self.cb_choixscr.setCurrentIndex(index)

    def ouvrirAide(self):
        localHelp = (os.path.dirname(__file__) + "/help/user_manual.pdf")
        localHelp = localHelp.replace("\\", "/")

        QDesktopServices.openUrl(QUrl(localHelp))

    def RemplirComboBox(self):
        # Récupérer toutes les couches du projet actif
        layers = QgsProject.instance().mapLayers().values()

        # Créer une liste des noms de couches
        layer_names = [layer.name() for layer in layers]

        # Ajouter les noms des couches à la ComboBox
        self.cb_choixLayerInterscet.addItems(layer_names)

    def RecupererCoucheDansProjets(self, index):
        self.selected_layer_name = self.cb_choixLayerInterscet.itemText(index)
        return self.selected_layer_name

    def EntiteSelectionner(self, selected_layer_name):
        selected_features = layer.getFeatures(QgsFeatureRequest().setFilterFids(layer.selectedFeatureIds()))