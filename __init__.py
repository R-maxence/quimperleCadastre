# -*- coding: utf-8 -*-
def classFactory(iface):
    from .QuimperleCadastrePlugin import QuimperleCadastrePlugin
    return QuimperleCadastrePlugin(iface)
