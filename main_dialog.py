# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

from qgis.core import *

from qgis.gui import *
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

        self.sb_buffer.setValue(0)
        self.buffer = []
        self.crs_projected = QgsCoordinateReferenceSystem('EPSG:2154')

        self.cb_choixLayerInterscet.currentIndexChanged.connect(self.RecupererCoucheDansProjets)
        self.RemplirComboBox()
        self.cb_enti_selection.stateChanged.connect(self.EntiteSelectionner)
        self.sb_buffer.valueChanged.connect(self.CreationBuffer)
        self.pb_ok.clicked.connect(self.TestExport)


    def RemplirComboBox(self):
        # Récupérer toutes les couches du projet actif
        layers = QgsProject.instance().mapLayers().values()
        # Créer une liste des noms de couches
        layer_names = []
        for layer in layers:
            layer_names.append(layer.name())
        # Ajouter les noms des couches à la ComboBox
        self.cb_choixLayerInterscet.addItems(layer_names)

    def RecupererCoucheDansProjets(self):
        index = self.cb_choixLayerInterscet.currentIndex()
        self.selected_layer_name = self.cb_choixLayerInterscet.itemText(index)

        self.selectedLayer = QgsProject.instance().mapLayersByName(self.selected_layer_name)[0]

        copied_features = []
        for feature in self.selectedLayer.getFeatures():
            # Copier l'entité
            copied_feature = QgsFeature()
            copied_feature.setGeometry(feature.geometry())

            # Ajouter l'entité copiée à la liste
            copied_features.append(copied_feature)

        self.selected_features = copied_features


    def EntiteSelectionner(self):

        if self.cb_enti_selection.isChecked():
            request = QgsFeatureRequest().setFilterFids(self.selectedLayer.selectedFeatureIds())

            # Récupérer les entités sélectionnées dans la couche
            copied_features = []
            for feature in self.selectedLayer.getFeatures(request):
                # Copier l'entité
                copied_feature = QgsFeature()
                copied_feature.setGeometry(feature.geometry())

                # Ajouter l'entité copiée à la liste
                copied_features.append(copied_feature)

            self.selected_features = copied_features
            self.label_nbentite.setText(str(len(copied_features)))
            if self.sb_buffer.value() != 0:
                self.CreationBuffer()

        else :
            self.label_nbentite.setText("Néant")
            if self.sb_buffer.value() != 0:
                self.CreationBuffer()

    def TransformScr(self, selectedLayer, crs_projected):
        """
        Fonction pour transformer les entités d'une couche dans un SCR projeté.

        Args:
            selectedLayer (QgsVectorLayer): La couche dont les entités doivent être transformées.
            crs_projected (QgsCoordinateReferenceSystem): Le système de référence de coordonnées projeté.
        """

        # Créer une transformation de coordonnées
        transformContext = QgsProject.instance().transformContext()
        coord_transformation = QgsCoordinateTransform(selectedLayer.crs(), crs_projected, transformContext)

        # Transformer les entités sélectionnées en SCR projeté
        transformed_features = []
        for feature in selectedLayer.getFeatures():
            try:
                copied_feature = QgsFeature()

                # Obtenir la géométrie de l'entité
                geometry = feature.geometry()

                # Transformer la géométrie en utilisant la transformation
                geometry.transform(coord_transformation)

                # Définir la géométrie de l'entité avec la géométrie transformée
                copied_feature.setGeometry(geometry)

                # Ajouter l'entité transformée à la liste
                transformed_features.append(copied_feature)
            except Exception as e:
                # Afficher une fenêtre d'alerte avec l'ID de la feature et le message d'erreur
                message = "Erreur lors de la transformation de l'entité %i : %s" % (feature.id(), str(e))
                self.show_alert_dialog(message)

        # Remplacer les entités sélectionnées par les entités transformées
        self.selected_features = transformed_features

        # Vérifier si toutes les entités transformées ont une géométrie
        for feature in transformed_features:
            if not feature.hasGeometry():
                # Afficher un message d'alerte avec l'ID de la feature
                message = "Aucune géométrie pour l'entité %i après la transformation. Veuillez vérifier le système de référence de coordonnées projeté." % (feature.id())
                self.show_alert_dialog(message)
                # Arrêter la boucle
                break
        if self.selected_features is None:
            print("coucou")
        # Si toutes les entités ont une géométrie, continuer le traitement

    def CreationBuffer(self):
        if self.sb_buffer.value() != 0:
            print("coucou")
            if self.selectedLayer.crs().isGeographic():
                # Transformer les entités sélectionnées en SCR projeté
                self.selected_features = self.TransformScr(self.selectedLayer, self.crs_projected)
            else:
                if self.cb_enti_selection.isChecked():
                    self.EntiteSelectionner
                else:
                    self.selected_features = self.selectedLayer.getFeatures()

            # Créer une liste qui contiendras les buffers
            buffered_features = []
            #créer les paramètres du Buffer
            rayon = self.sb_buffer.value()  # La distance du buffer
            nombre_segment = 5 #valeur par défaut Qgis - le nombre de segments permet de définir un quart de cercle approximatif
            # style_terminaison = 1 #le style de terminaison est un entier associé aux valeurs suivantes : 1 : arrondi (round) 2 : plat (flat) 3 : carré (square)
            # style_jointure = 1 #le style de jointure est un entier associé aux valeurs suivantes : 1 : arrondi (round) 2 : saillant (mitre) 3 : biseauté (bevel)
            # print(f"rayon: {rayon}, nombre_segment: {nombre_segment}, style_terminaison: {style_terminaison}, style_jointure: {style_jointure}")

            for feature in self.selected_features:
                copied_feature = QgsFeature()
                buffered_geometry = feature.geometry().buffer(rayon, nombre_segment)  # Création du buffer
                # buffered_geometry = feature.geometry().buffer(rayon, nombre_segment, style_terminaison,style_jointure)  # Création du buffer
                copied_feature.setGeometry(buffered_geometry)
                buffered_features.append(copied_feature)  # Ajout du buffer à la liste buffered_features

            # Notre buffer devient sur ce qu'on doit travaillé
            self.buffer = buffered_features
        else:
            if self.cb_enti_selection.isChecked():
                self.EntiteSelectionner()
            else:
                self.RecupererCoucheDansProjets()

    def show_alert_dialog(self, message):
        # Créer une boîte de message Qt
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(message)
        msg_box.exec_()

    def TestExport(self):
        # Create a temporary layer with polygon geometry
        crs = self.selectedLayer.crs()  # Get the CRS object
        epsg_code = crs.authid()  # Use .authid() to get EPSG code
        temp_layer = QgsVectorLayer("Polygon?crs=" + str(epsg_code), str(self.selected_layer_name) + "copie", "memory")
        print(epsg_code)
        # temp_layer.setCrs(QgsCoordinateReferenceSystem(str(epsg_code)))


        # Add the layer to the map
        QgsProject.instance().addMapLayer(temp_layer)

        # # Check if features have valid geometry
        # for feature in self.selected_features:
        #     if not feature.hasGeometry():
        #         print("Feature {} has no geometry!".format(feature.id()))
        #         continue

        # Add features to the layer
        if self.sb_buffer.value() == 0 :
            temp_layer.dataProvider().addFeatures(self.selected_features)
        else :
            temp_layer.dataProvider().addFeatures(self.buffer)