# -*- coding: utf-8 -*-
def classFactory(iface):
    from .quimperleCadastre import QuimperleCadastrePlugin
    return QuimperleCadastrePlugin(iface)
