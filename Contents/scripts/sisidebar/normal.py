# -*- coding: utf-8 -*-
from maya import cmds
from . import freeze

def convert_edge_lock():
    sel = cmds.ls(sl=True, l=True)
    meshes = common.search_polygon_mesh(sel, serchChildeNode=False)
    if not meshes:
        return
    for mesh in meshes:
        d_mesh = cmds.duplicate(mesh, rr=True)[0]
        modeling.setSoftEdge(mesh, angle=120)
        cmds.transferAttributes(d_mesh, mesh,
                                flipUVs=0, 
                                transferPositions=0, 
                                transferUVs=0, 
                                sourceUvSpace="map1", 
                                searchMethod=3, 
                                transferNormals=1, 
                                transferColors=0, 
                                targetUvSpace="map1", 
                                colorBorders=1, 
                                sampleSpace=5)
        freeze.main(mesh)
        cmds.polyNormalPerVertex(mesh, ufn=True)
        cmds.delete(d_mesh)
    cmds.select(meshes)