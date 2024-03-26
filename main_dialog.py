from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import processing
import sys, os
import sqlite3
import psycopg2
from db_manager.db_plugins import createDbPlugin

# sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")
# from main_form import *
ui_path = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(ui_path, "forms")
form_action1, _ = uic.loadUiType(os.path.join(ui_path, "dialog.ui"))


class MainDialog(QDialog, form_action1):
    def __init__(self, interface):
        QDialog.__init__(self)
        self.setupUi(self)

        scr_principaux = ["--Choix SCR--", "EPSG:2154 RGF93 v1 / Lambert-93",
                          "EPSG:3948 RGF93 v1 / CC48"]
        self.cb_choixscr.addItems(scr_principaux)

        self.sb_buffer.setValue(0)
        self.crs_projected = QgsCoordinateReferenceSystem('EPSG:2154')
        self.copied_features = []
        self.rb_spatialite.toggled.connect(self.remplirComboboxBD)
        self.rb_postgis.toggled.connect(self.remplirComboboxBD)
        self.cb_choixConnexion.currentIndexChanged.connect(lambda: QTimer.singleShot(10, self.choixBD))
        self.cb_choixConnexionSchema.currentIndexChanged.connect(lambda: QTimer.singleShot(10, self.choixSchema))

        self.cb_choixLayerInterscet.currentIndexChanged.connect(self.recupererCoucheDansProjets)
        self.remplirComboBox()
        self.cb_enti_selection.stateChanged.connect(self.EntiteSelectionner)
        self.sb_buffer.valueChanged.connect(self.CreationBuffer)

        self.pb_aide.clicked.connect(self.ouvrirAide)
        self.pb_choixscr.clicked.connect(self.choixScr)
        self.pb_folderFinder.clicked.connect(self.recupFichierSauvegarde)
        self.le_exitPath.textChanged.connect(self.recupPathSauvegarde)

        # gestion des entrées utilisateur pour la combo box des SCR
        self.cb_choixscr.currentTextChanged.connect(self.choixScrCb)

        self.label_scr.setText("Merci de choisir un scr valide")
        # Empêcher la sélection du premier index
        self.cb_choixscr.model().item(0).setEnabled(False)

        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)

    # Fonction pour sauvegarder lors du click boutons le repertoire

    def ouvrirAide(self):
        localHelp = (os.path.dirname(__file__) + "/help/user_manual.pdf")
        localHelp = localHelp.replace("\\", "/")

        QDesktopServices.openUrl(QUrl(localHelp))

    def get_liste_cnx(self, wtype):
        # renvoie la liste des connexions d'un certain type'
        wlst = []
        dbpluginclass = createDbPlugin(wtype)

        for c in dbpluginclass.connections():
            wlst.append(c.connectionName())

        return wlst

    def get_info_spatialite(self, wnom):
        # renvoie le path de la BD Spatialite
        resu = None
        dbpluginclass = createDbPlugin("spatialite")

        for c in dbpluginclass.connections():
            if c.connectionName() == wnom:
                # print("c : ", c)
                settings = QgsSettings()
                settings.beginGroup(u"/%s/%s" % ('/SpatiaLite/connections', wnom))

                if settings.contains("sqlitepath"):
                    resu = settings.value("sqlitepath")

        return resu

    def get_info_postgis(self, wnom):
        # renvoie l'hôte, le port, le nom de la DB, le user et le pwd sous forme de tuple
        resu = None
        dbpluginclass = createDbPlugin("postgis")

        for c in dbpluginclass.connections():
            if c.connectionName() == wnom:
                # print("c : ", c)
                settings = QgsSettings()
                settings.beginGroup(u"/%s/%s" % ('/PostgreSQL/connections', wnom))

                if settings.contains("database"):
                    whost = settings.value("host")
                    wport = settings.value("port")
                    wdatabase = settings.value("database")
                    wusername = settings.value("username")
                    wpassword = settings.value("password")

                    resu = (whost, wport, wdatabase, wusername, wpassword)
        return resu

    def remplirComboboxBD(self):
        # Si le radio bouton est coché
        if self.rb_spatialite.isChecked():
            # Effacez les éléments de la ComboBox
            self.cb_choixConnexion.clear()
            # Peuplez la ComboBox avec les noms des bases de données SpatiaLite
            self.cb_choixConnexion.addItems(self.get_liste_cnx("spatialite"))
        else:
            # Effacez les éléments de la ComboBox
            self.cb_choixConnexion.clear()
            # Peuplez la ComboBox avec les noms des bases de données SpatiaLite
            self.cb_choixConnexion.addItems(self.get_liste_cnx("postgis"))

    def choixBD(self):
        index = self.cb_choixConnexion.currentIndex()

        # Récupérer le nom de la base de données sélectionnée dans la combobox
        selected_bd_name = self.cb_choixConnexion.itemText(index)

        if self.rb_spatialite.isChecked():
            self.path_db = self.get_info_spatialite(selected_bd_name)


        elif self.rb_postgis.isChecked():
            self.path_db = self.get_info_postgis(selected_bd_name)

            self.ajoutComboboxSchemaPostgis()

    def ajoutComboboxSchemaPostgis(self):
        self.cb_choixConnexionSchema.clear()
        try:
            whost, wport, wdatabase, wusername, wpassword = self.path_db
            conn = psycopg2.connect(
                host=whost,
                port=wport,
                database=wdatabase,
                user=wusername,
                password=wpassword
            )
            cursor = conn.cursor()
            cursor.execute("SELECT schema_name FROM information_schema.schemata;")
            results = cursor.fetchall()
            conn.commit()
            conn.close()
            for result in results:
                self.cb_choixConnexionSchema.addItem(result[0])
        except Exception as e:
            print("Erreur:", e)

    def choixSchema(self):
        index = self.cb_choixConnexionSchema.currentIndex()

        # Récupérer le nom de la base de données sélectionnée dans la combobox
        schema = self.cb_choixConnexionSchema.itemText(index)
        print(schema)

        return schema

    def remplirComboBox(self):
        # Récupérer toutes les couches du projet actif
        layers = QgsProject.instance().mapLayers().values()
        # Créer une liste des noms de couches
        layer_names = []
        for layer in layers:
            if layer.name() not in ["couche_resultat", "vue_intersect", "geo_parcelle"]:
                layer_names.append(layer.name())
        # Ajouter les noms des couches à la ComboBox
        self.cb_choixLayerInterscet.addItems(layer_names)

    def recupererCoucheDansProjets(self):
        self.label_tolerance.setText("Tolérance d'intersection ( m )")
        self.sb_buffer.setRange(0, 100000)
        self.sb_buffer.setValue(0)
        self.cb_enti_selection.setChecked(False)
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
        print(self.selectedLayer.geometryType())
        print(self.selectedLayer)

    def EntiteSelectionner(self):

        if self.cb_enti_selection.isChecked():
            request = QgsFeatureRequest().setFilterFids(self.selectedLayer.selectedFeatureIds())

            # Récupérer les entités sélectionnées dans la couche
            self.copied_features = []
            for feature in self.selectedLayer.getFeatures(request):
                # Copier l'entité
                copied_feature = QgsFeature()
                copied_feature.setGeometry(feature.geometry())

                # Ajouter l'entité copiée à la liste
                self.copied_features.append(copied_feature)

            self.selected_features = self.copied_features
            self.label_nbentite.setText(str(len(self.copied_features)))
            if self.sb_buffer.value() != 0:
                self.CreationBuffer()
        else:
            self.label_nbentite.setText("Néant")
            if self.sb_buffer.value() != 0:
                self.CreationBuffer()
            else:
                self.recupererCoucheDansProjets()

    def CreationBuffer(self):
        if self.sb_buffer.value() != 0:
            if self.selectedLayer.crs().isGeographic():
                message = "Attention la couche est dans un SCR Non projeté. \nLe buffer sera en degrès. \nMerci de reprojeter votre couche"
                self.warning(message)

            else:
                if self.cb_enti_selection.isChecked():
                    self.selected_features = self.copied_features
                else:
                    self.selected_features = self.selectedLayer.getFeatures()

            crs_cible = self.selectedLayer.crs()  # Get the CRS object
            epsg_code_cible = crs_cible.authid()  # Use .authid() to get EPSG code

            if self.selectedLayer.geometryType() == 0:
                temp_layer = QgsVectorLayer("Point?crs=" + str(epsg_code_cible),
                                            str(self.selected_layer_name) + "copie",
                                            "memory")
            elif self.selectedLayer.geometryType() == 1:
                temp_layer = QgsVectorLayer("LineString?crs=" + str(epsg_code_cible),
                                            str(self.selected_layer_name) + "copie", "memory")
            elif self.selectedLayer.geometryType() == 2:
                temp_layer = QgsVectorLayer("Polygon?crs=" + str(epsg_code_cible),
                                            str(self.selected_layer_name) + "copie",
                                            "memory")

            temp_layer.dataProvider().addFeatures(self.selected_features)
            input_layer = temp_layer
            buffer_distance = self.sb_buffer.value()
            buffer_layer_temp = QgsVectorLayer("Polygon?crs=" + "buffer_layer", "memory")

            # Définir les paramètres de l'algorithme de tampon
            buffer_params = {
                "INPUT": temp_layer,
                "DISTANCE": buffer_distance,
                "OUTPUT": "memory:"
            }

            # Exécuter l'algorithme de tampon
            buffer_result = processing.run("native:buffer", buffer_params)
            buffer_layer_temp = buffer_result["OUTPUT"]
            self.buffer_layer = buffer_layer_temp

        else:
            if self.cb_enti_selection.isChecked():
                self.EntiteSelectionner()
            else:
                self.recupererCoucheDansProjets()

    def ajoutGeo_parcelleSQL(self):
        try:
            # Créer l'URI de la source de données
            uri = QgsDataSourceUri()
            uri.setDatabase(self.path_db)
            uri.setDataSource("", "geo_parcelle", "geom", "")

            # Créer la couche vectorielle à partir de l'URI
            self.couche_source = QgsVectorLayer(uri.uri(), "geo_parcelle", "spatialite")

            # Vérifier si la couche est valide
            if self.couche_source.isValid():
                if len(QgsProject.instance().mapLayersByName("geo_parcelle")) > 0:
                    layer = QgsProject.instance().mapLayersByName("geo_parcelle")[0]
                    QgsProject.instance().removeMapLayer(layer.id())
                # Ajouter la couche à la carte
                QgsProject.instance().addMapLayer(self.couche_source)
        except Exception as e:
            message = "Une erreur s'est produite lors du chargement de la couche 'geo_parcelle' de la BD : %s" % str(e)
            self.critical(message)
            self.reject()

    def ajoutGeo_parcellePostgre(self):

        try:
            # Déballage des informations de connexion
            whost, wport, wdatabase, wusername, wpassword = self.path_db
            schema = self.choixSchema()

            # Création de l'URI de la source de données
            uri = QgsDataSourceUri()
            uri.setConnection(whost, str(wport), wdatabase, wusername, wpassword)
            uri.setDataSource("%s" % schema, "geo_parcelle", "geom", "")

            # Création de la couche vectorielle à partir de l'URI
            self.couche_source = QgsVectorLayer(uri.uri(), "geo_parcelle", "postgres")

            # Vérification de la validité de la couche
            if self.couche_source.isValid():
                # Suppression de la couche existante s'il y en a une
                existing_layers = QgsProject.instance().mapLayersByName("geo_parcelle")
                if existing_layers:
                    QgsProject.instance().removeMapLayer(existing_layers[0].id())
                # Ajout de la nouvelle couche à la carte
                QgsProject.instance().addMapLayer(self.couche_source)
        except Exception as e:
            message = "Une erreur s'est produite lors du chargement de la couche 'geo_parcelle' de la BD : %s" % str(e)
            self.critical(message)
            self.reject()

    def parcelle_str(self):
        # Définir les couches source et cible
        if self.rb_spatialite.isChecked():
            self.ajoutGeo_parcelleSQL()
            if self.ajoutGeo_parcelleSQL() == None:
                self.reject()
        elif self.rb_postgis.isChecked():
            self.ajoutGeo_parcellePostgre()
            if self.ajoutGeo_parcellePostgre() == None:
                self.reject()
        self.couche_source = QgsProject.instance().mapLayersByName('geo_parcelle')[0]
        crs_cible = self.selectedLayer.crs()  # Get the CRS object
        epsg_code_cible = crs_cible.authid()  # Use .authid() to get EPSG code

        if self.selectedLayer.geometryType() == 0:
            temp_layer = QgsVectorLayer("Point?crs=" + str(epsg_code_cible), str(self.selected_layer_name) + "copie",
                                        "memory")
        elif self.selectedLayer.geometryType() == 1:
            temp_layer = QgsVectorLayer("LineString?crs=" + str(epsg_code_cible),
                                        str(self.selected_layer_name) + "copie", "memory")
        elif self.selectedLayer.geometryType() == 2:
            temp_layer = QgsVectorLayer("Polygon?crs=" + str(epsg_code_cible), str(self.selected_layer_name) + "copie",
                                        "memory")

        if self.sb_buffer.value() == 0:
            temp_layer.dataProvider().addFeatures(self.selected_features)
        else:
            temp_layer = self.buffer_layer
            print(len(temp_layer))
        couche_cible = temp_layer

        # Définir les paramètres de l'algorithme
        params = {
            'INPUT': self.couche_source,
            'PREDICATE': [0],  # Utilisez 0 pour "intersecte"
            'INTERSECT': couche_cible,
            'OUTPUT': 'memory:'
            # Vous pouvez spécifier un chemin de fichier si vous voulez enregistrer le résultat dans un fichier
        }

        # Exécuter l'algorithme
        resultat = processing.run("native:extractbylocation", params)

        # Accéder à la couche résultante
        couche_resultat = resultat['OUTPUT']

        # Itérer sur les entités de la couche résultante + creation de la liste de sids des parcelles extraites
        parcelleID = []
        nb_geo_parcelle = 0
        for entite in couche_resultat.getFeatures():
            # Accéder à la valeur de l'attribut "geo_parcelle" pour chaque entité
            valeur_geo_parcelle = entite.attribute("geo_parcelle")
            parcelleID.append(valeur_geo_parcelle)
            nb_geo_parcelle += 1
        print(nb_geo_parcelle)

        # Initialisation de la liste des parcelle IDs formatées
        parcelleIDs_formatted = []

        # Parcours de chaque élément dans parcelleID
        for id in parcelleID:
            # Formatage de l'élément en tant que chaîne avec des guillemets simples
            formatted = "'%s'" % id
            # Ajout de l'élément formaté à la liste
            parcelleIDs_formatted.append(formatted)

        # Joindre les éléments formatés avec des virgules pour former la chaîne finale
        self.parcelleIDs_str = ','.join(parcelleIDs_formatted)
        # print(parcelleIDs_str)

    def intersectionCouches(self):
        print("intersectionCouches")
        if self.cb_shp.isChecked() or self.cb_geopackage.isChecked() or self.cb_geoJson.isChecked():
            try:
                self.parcelle_str()
                if len(QgsProject.instance().mapLayersByName("vue_intersect")) > 0:
                    layer = QgsProject.instance().mapLayersByName("vue_intersect")[0]
                    QgsProject.instance().removeMapLayer(layer)

                if self.rb_spatialite.isChecked():
                    cnx_parcelle = sqlite3.connect(self.path_db)
                    cursor = cnx_parcelle.cursor()
                    cursor.execute("DROP VIEW IF EXISTS vue_intersect;")
                    cnx_parcelle.commit()

                    sql_query = """
                                   CREATE VIEW vue_intersect AS 
                                   SELECT
                                       p.parcelle as id_parcelle
                                   FROM parcelle p 
                                   WHERE
                                       p.parcelle IN ({})
                                   GROUP BY
                                       p.parcelle
                                   ORDER BY
                                       p.parcelle;
                                   """.format(self.parcelleIDs_str)
                    cursor.execute(sql_query)
                    cnx_parcelle.commit()

                    wuri = QgsDataSourceUri()
                    wuri.setDatabase(self.path_db)
                    wuri.setDataSource("", "vue_intersect", "")
                    la_couche_test = QgsVectorLayer(wuri.uri(), "vue_intersect", "spatialite")
                    if la_couche_test.isValid():
                        QgsProject.instance().addMapLayer(la_couche_test)

                    wsql = "SELECT * FROM geo_parcelle, vue_intersect WHERE geo_parcelle = id_parcelle"
                    la_couche_resultat = QgsVectorLayer("?query=%s" % (wsql), "couche_resultat", "virtual")
                    QgsProject.instance().addMapLayer(la_couche_resultat)
                    return la_couche_resultat

                elif self.rb_postgis.isChecked():
                    whost, wport, wdatabase, wusername, wpassword = self.path_db
                    conn = psycopg2.connect(
                        host=whost,
                        port=wport,
                        database=wdatabase,
                        user=wusername,
                        password=wpassword
                    )
                    schema = self.choixSchema()
                    cnx_parcelle = conn.cursor()
                    cnx_parcelle.execute("DROP VIEW IF EXISTS {}.vue_intersect;".format(schema))
                    conn.commit()

                    sql_query = """
                                   CREATE VIEW {}.vue_intersect AS 
                                   SELECT
                                       p.parcelle as id_parcelle
                                   FROM {}.parcelle p 
                                   WHERE
                                       p.parcelle IN ({})
                                   GROUP BY
                                       p.parcelle
                                   ORDER BY
                                       p.parcelle;
                                   """.format(schema, schema, self.parcelleIDs_str)
                    cnx_parcelle.execute(sql_query)
                    conn.commit()

                    wuri = QgsDataSourceUri()
                    wuri.setConnection(whost, wport, wdatabase, wusername, wpassword)
                    wuri.setDataSource(schema, "vue_intersect", "", "", "id_parcelle")
                    la_couche_test = QgsVectorLayer(wuri.uri(), "vue_intersect", "postgres")
                    if la_couche_test.isValid():
                        QgsProject.instance().addMapLayer(la_couche_test)

                    wsql = "SELECT * FROM geo_parcelle, vue_intersect WHERE CAST(geo_parcelle AS TEXT) = CAST(id_parcelle AS TEXT)"
                    la_couche_resultat = QgsVectorLayer("?query=%s" % (wsql), "couche_resultat", "virtual")
                    if la_couche_resultat.isValid():
                        print('couche résultat valide')
                        QgsProject.instance().addMapLayer(la_couche_resultat)
                    else:
                        print('probleme avec la couche résultat')
                    return la_couche_resultat

            except Exception as e:
                message = "Une erreur s'est produite lors du chargement de la couche 'geo_parcelle' de la BD : %s" % str(
                    e)
                self.critical(message)
                self.reject()

    def exportRequeteAttributaire(self):
        if self.cb_xlsx.isChecked() or self.cb_csv.isChecked():
            self.parcelle_str()

            if len(QgsProject.instance().mapLayersByName("vue_attribut")) > 0:
                layer = QgsProject.instance().mapLayersByName("vue_attribut")[0]
                QgsProject.instance().removeMapLayer(layer.id())

            if self.rb_spatialite.isChecked():
                cnx_parcelle = sqlite3.connect(self.path_db)
                cursor = cnx_parcelle.cursor()
                cursor.execute("DROP VIEW IF EXISTS vue_attribut;")
                cnx_parcelle.commit()

                # Définir la requête SQL
                sql_query = """
                                CREATE VIEW  vue_attribut AS
                                SELECT
                                    proprietaire.comptecommunal AS compte_communal,
                                    CASE
                                        WHEN proprietaire.dnatpr IN ('ECF', 'FNL', 'DOM') THEN 'Personne physique'
                                        WHEN proprietaire.dnatpr IN ('HLM', 'SEM', 'TGV', 'RFF', 'CLL', 'CAA') THEN 'Personne Morale'
                                        ELSE
                                            CASE
                                                WHEN TRIM(proprietaire.dsiren) <> '' THEN 'Personne Morale'
                                                ELSE 'Personne Physique'
                                            END
                                    END AS type_prop,
                                    proprietaire.dqualp AS qualite,
                                    proprietaire.ddenom AS nom_complet,
                                    proprietaire.dnomlp AS nom_usage,
                                    proprietaire.dprnlp AS prenom_usage,
                                    proprietaire.dnvoiri AS adresse_num,
                                    TRIM(REPLACE(proprietaire.dlign4, '[0-9]', '')) AS adresse_voie,
                                    proprietaire.dlign6 AS commune,
                                    COUNT(p.parcelle) AS nombre_parcelles,
                                    GROUP_CONCAT(p.id_parcelle, ',') AS liste_parcelle
                                FROM
                                    (SELECT
                                        *,
                                        TRIM(substr(parcelle, 10)) || '-' || TRIM(commune.libcom) || '-' || TRIM(parcelle.dcntpa) || 'm²' AS id_parcelle
                                    FROM
                                        parcelle
                                    LEFT JOIN
                                        commune ON parcelle.ccocom = commune.ccocom) p
                                INNER JOIN 
                                    proprietaire ON p.comptecommunal = proprietaire.comptecommunal
                                 WHERE
                                        p.parcelle IN (%s)
                                GROUP BY 
                                    proprietaire.comptecommunal,
                                    type_prop,
                                    qualite,
                                    nom_complet,
                                    nom_usage,
                                    prenom_usage,
                                    adresse_num,
                                    adresse_voie,
                                    proprietaire.dlign6
                                ORDER BY 
                                    proprietaire.comptecommunal;

                                """ % self.parcelleIDs_str

                # Exécuter la requête SQL
                cursor = cnx_parcelle.cursor()
                cursor.execute(sql_query)

                wuri = QgsDataSourceUri()
                wuri.setDatabase(self.path_db)
                wuri.setDataSource("", "vue_attribut", "")

                la_couche_test = QgsVectorLayer(wuri.uri(), "vue_attribut", "spatialite")

                QgsProject.instance().addMapLayer(la_couche_test)
                return la_couche_test
            elif self.rb_postgis.isChecked():
                whost, wport, wdatabase, wusername, wpassword = self.path_db
                conn = psycopg2.connect(
                    host=whost,
                    port=wport,
                    database=wdatabase,
                    user=wusername,
                    password=wpassword
                )
                schema = self.choixSchema()
                cnx_parcelle = conn.cursor()
                cnx_parcelle.execute("DROP VIEW IF EXISTS {}.vue_attribut;".format(schema))
                conn.commit()
                sql_query = """
                                    CREATE VIEW {}.vue_attribut AS
                                    SELECT
                                            ROW_NUMBER() OVER () AS row_num,
                                            proprietaire.comptecommunal AS compte_communal,
                                        CASE
                                            WHEN proprietaire.dnatpr IN ('ECF', 'FNL', 'DOM') THEN 'Personne physique'
                                            WHEN proprietaire.dnatpr IN ('HLM', 'SEM', 'TGV', 'RFF', 'CLL', 'CAA') THEN 'Personne Morale'
                                            ELSE
                                                CASE
                                                    WHEN TRIM(proprietaire.dsiren::varchar) <> '' THEN 'Personne Morale'
                                                    ELSE 'Personne Physique'
                                                END
                                        END AS type_prop,
                                        proprietaire.dqualp AS qualite,
                                        proprietaire.ddenom AS nom_complet,
                                        proprietaire.dnomlp AS nom_usage,
                                        proprietaire.dprnlp AS prenom_usage,
                                        proprietaire.dnvoiri AS adresse_num,
                                        TRIM(REGEXP_REPLACE(proprietaire.dlign4, '[0-9]', '', 'g')) AS adresse_voie,
                                        proprietaire.dlign6 AS commune,
                                        COUNT(id_parcelle),
                                        SUM(p.dcntpa) AS contenance_total_parcelle,
                                        ARRAY_TO_STRING(ARRAY_AGG(p.id_parcelle), ', ') AS liste_parcelle
                                    FROM
                                        (SELECT
                                            *,
                                            TRIM(substring(parcelle.parcelle::varchar FROM 10)) || '-' || TRIM(commune.libcom) || '-' || TRIM(parcelle.dcntpa::varchar) || 'm²' AS id_parcelle
                                        FROM
                                            {}.parcelle
                                        LEFT JOIN
                                            {}.commune ON parcelle.ccocom = commune.ccocom) p
                                    INNER JOIN 
                                        {}.proprietaire ON p.comptecommunal = proprietaire.comptecommunal
                                    WHERE
                                        p.parcelle IN ({})
                                    GROUP BY 
                                        proprietaire.comptecommunal,
                                        type_prop,
                                        qualite,
                                        nom_complet,
                                        nom_usage,
                                        prenom_usage,
                                        adresse_num,
                                        adresse_voie,
                                        proprietaire.dlign6
                                    ORDER BY 
                                        proprietaire.comptecommunal;
                                    """.format(schema, schema, schema, schema, self.parcelleIDs_str)
                cnx_parcelle.execute(sql_query)
                conn.commit()

                if conn:
                    print("Connexion réussie à la base de données PostgreSQL")

                # Configurez la source de données QGIS
                wuri = QgsDataSourceUri()
                wuri.setConnection(whost, wport, wdatabase, wusername, wpassword)
                # wuri.setDataSource(schema, "vue_attribut", "", "", "id_parcelle")
                wuri.setDataSource(schema, "vue_attribut", "", "", "row_num")

                # Créez la couche vectorielle QGIS
                la_couche_test = QgsVectorLayer(wuri.uri(), "vue_attribut", "postgres")

                # Vérifiez si la couche est valide avant de l'ajouter au projet
                if la_couche_test.isValid():
                    print("La couche est valide")
                    QgsProject.instance().addMapLayer(la_couche_test)
                else:
                    print("La couche n'est pas valide")

                # Fermez la connexion à la base de données
                conn.close()

                return la_couche_test

    def coucheResultatStyle(self):

        # Créer un symbole de remplissage avec contour
        remplissage_symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        remplissage_symbol_layer = remplissage_symbol.symbolLayer(0)
        remplissage_symbol_layer.setColor(Qt.transparent)  # Couleur de remplissage transparente
        remplissage_symbol_layer.setStrokeColor(Qt.black)  # Couleur du contour
        remplissage_symbol_layer.setStrokeWidth(0.1)  # Largeur du contour

        # Créer un rendu de symbologie unique
        renderer = QgsSingleSymbolRenderer(remplissage_symbol)

        # Appliquer le rendu à la couche
        la_couche_resultat = QgsProject.instance().mapLayersByName('geo_parcelle')[0]
        la_couche_resultat.setRenderer(renderer)
        la_couche_resultat.triggerRepaint()

    def recupFichierSauvegarde(self):
        self.folder = QFileDialog.getExistingDirectory(self)
        self.folder = self.folder + "/"
        self.le_exitPath.setText(self.folder)

    # fonction pour enregistrer lors de l'écriture dans le QlineEdit
    def recupPathSauvegarde(self):
        self.folder = self.le_exitPath.text()
        self.folder = self.folder.replace('\\', '/')
        self.folder = self.folder + '/'  # sinon on se retrouve dans le dossier du dessus

    def choixScrCb(self):
        # affichage de la sélection
        selected_scr_cbox = self.cb_choixscr.currentText()
        if self.cb_choixscr.currentText() == "--Choix SCR--":
            self.label_scr.setText("Merci de choisir un scr valide")

        else:

            self.label_scr.setText(selected_scr_cbox)
            # récupération de l'epsg pour l'utiliser lors de l'export
            split = selected_scr_cbox.split(" ")  # renvoie une liste

            self.epsg_code = split[0]  # récupération de l'EPSG

    def choixScr(self):
        dialog = QgsProjectionSelectionDialog()
        dialog.exec_()

        if dialog.exec_():
            UsersScr = dialog.crs().authid()
            crsDescription = dialog.crs().description()
            concatenate = UsersScr + " " + crsDescription

            print(concatenate)
            index = self.cb_choixscr.findText(
                concatenate)  # on cherche l'index où le texte du scr choisis se situe, si n'existe pas renvoie -1

            if index == -1:
                # On ajoute dans la première ligne de notre cbbox le SCR sélectionné pour visualisation / compréhension
                self.cb_choixscr.addItem(concatenate)
                self.cb_choixscr.setCurrentIndex(self.cb_choixscr.count() - 1)  # On se positionne sur l'item


            else:
                self.cb_choixscr.setCurrentIndex(0)

    def exportSelectionVecto(self):
        print("exportSelectionVecto")
        if self.cb_shp.isChecked() or self.cb_geopackage.isChecked() or self.cb_geoJson.isChecked():
            layer_temp_export = self.intersectionCouches()
            try:
                crs = QgsCoordinateReferenceSystem(self.epsg_code)
            except:
                message = "Erreur lors de l'exportation epsg_code"
                self.critical(message)
            if self.folder == '':
                message = "Erreur lors de l'exportation folder"
                self.critical(message)
            if self.le_nom_sortie.text() == '':
                filename = str(self.selected_layer_name) + "_parcelleIntersect"
            else:
                filename = self.le_nom_sortie.text()

            filepath = os.path.join(self.folder, filename)

            if self.cb_shp.isChecked():

                error, message = QgsVectorFileWriter.writeAsVectorFormat(layer_temp_export, filepath, 'UTF-8', crs,
                                                                         driverName='ESRI Shapefile')
                if error == QgsVectorFileWriter.NoError:
                    message += "Exportation au format SHP Réussi"
                    self.information(message)
                else:
                    message += "Erreur lors de l'exportation"
                    self.critical(message)

            if self.cb_geopackage.isChecked():
                error, message = QgsVectorFileWriter.writeAsVectorFormat(layer_temp_export, filepath, 'UTF-8', crs,
                                                                         driverName='GPKG')
                if error == QgsVectorFileWriter.NoError:
                    message += "Exportation au format GPKG Réussi"
                    self.information(message)
                else:
                    message += "Erreur lors de l'exportation"
                    self.critical(message)

            if self.cb_geoJson.isChecked():
                error, message = QgsVectorFileWriter.writeAsVectorFormat(layer_temp_export, filepath, 'UTF-8', crs,
                                                                         driverName='GeoJSON')
                if error == QgsVectorFileWriter.NoError:
                    message += "Exportation au format GeoJson Réussi"
                    self.information(message)
                else:
                    message += "Erreur lors de l'exportation geojson"
                    self.critical(message)

    def exportAttributaire(self):
        layer = self.exportRequeteAttributaire()
        if self.cb_xlsx.isChecked():
            if self.le_nom_sortie.text() == '':
                filename = str(self.selected_layer_name) + "_publipostage.xlsx"
            else:
                filename = self.le_nom_sortie.text() + ".xlsx"
            filepath = os.path.join(self.folder, filename)
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, filepath, "utf-8", layer.crs(), 'xlsx')
            if error == QgsVectorFileWriter.NoError:
                message += "Exportation au format XLSX Réussi"
                self.information(message)
            else:
                message += "Erreur lors de l'exportation"
                self.critical(message)

        if self.cb_csv.isChecked():
            if self.le_nom_sortie.text() == '':
                filename = str(self.selected_layer_name) + "_publipostage.csv"
            else:
                filename = self.le_nom_sortie.text() + ".csv"
            filepath = os.path.join(self.folder, filename)
            QgsVectorFileWriter.writeAsVectorFormat(layer, filepath, "utf-8", layer.crs(), 'csv')
            error, message = QgsVectorFileWriter.writeAsVectorFormat(layer, filepath, "utf-8", layer.crs(), 'csv')
            if error == QgsVectorFileWriter.NoError:
                message += "Exportation au format CSV Réussi"
                self.information(message)
            else:
                message += "Erreur lors de l'exportation"
                self.critical(message)

        if len(QgsProject.instance().mapLayersByName("vue_attribut")) > 0:
            layer = QgsProject.instance().mapLayersByName("vue_attribut")[0]
            QgsProject.instance().removeMapLayer(layer.id())

    def enleverCouche(self):
        if len(QgsProject.instance().mapLayersByName("geo_parcelle")) > 0:
            layer1 = QgsProject.instance().mapLayersByName("geo_parcelle")[0]
            QgsProject.instance().removeMapLayer(layer1.id())
        if len(QgsProject.instance().mapLayersByName("couche_resultat")) > 0:
            layer2 = QgsProject.instance().mapLayersByName("couche_resultat")[0]
            QgsProject.instance().removeMapLayer(layer2.id())
        if len(QgsProject.instance().mapLayersByName("vue_intersect")) > 0:
            layer3 = QgsProject.instance().mapLayersByName("vue_intersect")[0]
            QgsProject.instance().removeMapLayer(layer3.id())

    def verif(self):
        if not self.rb_spatialite.isChecked() and not self.rb_postgis.isChecked():
            message = "Merci de sélectionner un type de base de donnée"
            self.warning(message)
            return False
        if self.cb_choixConnexion.currentText() == '':
            message = "Merci de sélectionner une base de donnée"
            self.warning(message)
            return False
        if self.cb_choixConnexionSchema.currentText() == '' and self.rb_postgis.isChecked():
            message = "Merci de sélectionner un schema"
            self.warning(message)
            return False
        if self.cb_choixLayerInterscet.currentText() == '':
            message = "Merci de sélectionner une donnée d'intersection"
            self.warning(message)
            return False
        if self.le_exitPath.text() == '':
            message = "Merci de sélectionner un chemin de sortie"
            self.warning(message)
            return False
        if self.cb_choixscr.currentText() == '--Choix SCR--' and (
                self.cb_shp.isChecked() or self.cb_geopackage.isChecked() or self.cb_geoJson.isChecked()):
            message = "Merci de sélectionner un SCR valide"
            self.warning(message)
            return False
        if not self.cb_shp.isChecked() and not self.cb_geopackage.isChecked() and not self.cb_geoJson.isChecked() and not self.cb_xlsx.isChecked() and not self.cb_csv.isChecked():
            message = "Merci de sélectionner un type de fichier de sortie"
            self.warning(message)
            return False
        return True

    # >>VICTOR FEATURES End

    def reject(self):
        QDialog.reject(self)

    def accept(self):
        if self.verif():
            self.exportSelectionVecto()  # click sur OK = lancement des exports avec les formats cochés au répertoire souhaité
            self.exportAttributaire()
            if len(QgsProject.instance().mapLayersByName("vue_attribut")) > 0:
                layer1 = QgsProject.instance().mapLayersByName("vue_attribut")[0]
                QgsProject.instance().removeMapLayer(layer1.id())
            if len(QgsProject.instance().mapLayersByName("couche_resultat")) > 0:
                layer2 = QgsProject.instance().mapLayersByName("couche_resultat")[0]
                QgsProject.instance().removeMapLayer(layer2.id())
            if len(QgsProject.instance().mapLayersByName("vue_intersect")) > 0:
                layer3 = QgsProject.instance().mapLayersByName("vue_intersect")[0]
                QgsProject.instance().removeMapLayer(layer3.id())
            self.coucheResultatStyle()
            QDialog.accept(self)

    def information(self, message):
        # QMessageBox.information(self, "Information", message)
        iface.messageBar().pushMessage("Géotraitement", message, level=Qgis.Success, duration=10)

    def warning(self, message):
        QMessageBox.warning(self, "Avertissement", message)

    def critical(self, message):
        if message == "Erreur lors de l'exportation":
            self.enleverCouche()
        QMessageBox.critical(self, "Erreur Critique", message)