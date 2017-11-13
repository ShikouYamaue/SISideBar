#!/usr/bin/env python
# -*- coding: utf-8 -*-
from maya import cmds
from maya import mel
import os, json
import pymel.core as pm
from . import weight
from . import common
from . import qt
import maya.api.OpenMaya as om
import re

#クラスタデフォーマの書き戻し
class ClusterCopy():
    def copy(self, mesh):
        self.cluster_list = []
        self.point_dict = {}
        self.cls_weight_dict = {}
            
        dummy = common.TemporaryReparent().main(mode='create')
        common.TemporaryReparent().main(mesh, dummyParent=dummy, mode='cut')
        
        cluster = cmds.ls(cmds.listHistory(mesh), type='cluster', l=True)
        for cls in cluster:
            set_node = cmds.ls(cmds.listHistory(cls, f=True), type='objectSet', l=True)[0]
            cmds.select(set_node)
            vertices = cmds.ls(sl=True)
            vertices = cmds.filterExpand(vertices, sm=31)
            cmds.select(vertices, r=True)
            try:
                weights = cmds.percent(cls, q=True, v=True)
                print weights
            #値が取れないときアンドゥするとなぜか直ることがある
            except Exception as e:
                print e.message
                cmds.delete(cls)
                cmds.undo()
                set_node = cmds.ls(cmds.listHistory(cls, f=True), type='objectSet', l=True)[0]
                vertices = cmds.ls(sl=True)
                vertices = cmds.filterExpand(vertices, sm=31)
                cmds.select(vertices, r=True)
                weights = cmds.percent(cls, q=True, v=True)
            self.cluster_list.append(cls)
            self.cls_weight_dict[cls] = weights
            self.point_dict[cls] = vertices
        common.TemporaryReparent().main(mesh, dummyParent=dummy, mode='parent')#コピーのおわったメッシュの子供を元に戻す
        common.TemporaryReparent().main(dummyParent=dummy, mode='delete')#ダミー親削除
        return self.point_dict, self.cls_weight_dict
        
    def paste(self, mesh):
        if not self.cluster_list:
            return
        for cls in self.cluster_list:
            weights = self.cls_weight_dict[cls]
            print 'paste cls :',cls
            cmds.select(cl=True)            
            points = self.point_dict[cls]
            newcls = cmds.cluster(points, n=cls)
            for i, v in enumerate(points):
                cmds.percent(newcls[0], v, v=(weights[i])) 
        return newcls
        
#ポリゴンメッシュをウェイト付きで複製する関数
def duplicate_with_skin(nodes, parentNode=None):
    #親子付けがあってもエラーはかないように修正
    print nodes
    # リストタイプじゃなかったらリストに変換する
    if not isinstance(nodes, list):
        nodes = [nodes]
    dupObjs = []
    for node in nodes:
        #子供のノード退避用ダミーペアレントを用意
        dummy = common.TemporaryReparent().main(mode='create')
        common.TemporaryReparent().main(node,dummyParent=dummy, mode='cut')
        #複製
        dup = cmds.duplicate(node)[0]
        #ウェイト転送メソッドをSimpleWeightコピペに変更
        weight.SimpleWeightCopyPaste().main(node, mode='copy', saveName=__name__, weightFile=node)
        weight.SimpleWeightCopyPaste().main(dup, mode='paste', saveName=__name__, weightFile=node)
        #親子付けを戻す
        common.TemporaryReparent().main(node,dummyParent=dummy, mode='parent')
        #ダミーペアレントを削除
        common.TemporaryReparent().main(dummyParent=dummy, mode='delete')
        if parentNode is not None:
            cmds.parent(dup, parentNode)
        dupObjs.append(dup)
    return dupObjs
    
#シーン内、もしくは入力メッシュ内にゼロポリゴンオブジェクトがあるかどうか調べる関数
def cehck_zero_poly_object(mesh=None, pop_msg=True):
    #mesh 入力メッシュ
    #pop_msg　探索結果を表示するかどうか
    if mesh == None:
        polyMeshes = common.search_polygon_mesh(cmds.ls(tr=True))
    else:
        polyMeshes = common.search_polygon_mesh(mesh)
    zeroPolyObj = []
    if polyMeshes == None:
        if pop_msg:
            cmds.confirmDialog( title="Check",message='Zero Polygon Object Count :  0')
        return zeroPolyObj
    for p in polyMeshes:
        vtx = cmds.polyListComponentConversion(p, tv=True)
        if vtx == []:
            zeroPolyObj.append(p)
    if not pop_msg:
        return zeroPolyObj
    if zeroPolyObj == []:
        cmds.confirmDialog( title="Check",message='Zero Polygon Object Count :  0')
    else:
        msg = 'Zero Polygon Object Count : '+str(len(zeroPolyObj))
        for p in zeroPolyObj:
            msg+='\n[ '+p+' ]'
        cmds.confirmDialog( title="Check",message=msg )
        cmds.select(zeroPolyObj, r=True)
    return zeroPolyObj
    