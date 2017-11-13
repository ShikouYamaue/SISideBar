# -*- coding: utf-8 -*-
from maya import cmds
from maya import mel
import pymel.core as pm
import re
import functools
import datetime
import os
import locale
import datetime as dt
import json

def search_polygon_mesh(object, serchChildeNode=False, fullPath=False):
    '''
    選択したものの中からポリゴンメッシュを返す関数
    serchChildeNode→子供のノードを探索するかどうか
    '''
    # リストタイプじゃなかったらリストに変換する
    if not isinstance(object, list):
        temp = object
        object = []
        object.append(temp)
    polygonMesh = []
    # 子供のノードを加えるフラグが有効な場合は追加
    if serchChildeNode is True:
        parentNodes = object
        for node in parentNodes:
            try:
                nodes = cmds.listRelatives(node, ad=True, c=True, typ='transform', fullPath=fullPath, s=False)
            except:
                pass
            if nodes is not None:
                object = object + nodes
    # メッシュノードを探して見つかったらリストに追加して返す
    for node in object:
        try:
            meshnode = cmds.listRelatives(node, s=True, pa=True, type='mesh', fullPath=True)
            if meshnode:
                polygonMesh.append(node)
        except:
            pass
    if len(polygonMesh) != 0:
        return polygonMesh
    else:
        return

class TemporaryReparent():
    '''
    一時的に子供のノードをダミーロケータの子供に退避、再親子付けする関数。
    ウェイト操作、UVSet操作など親子付けがあると処理が破たんする場合に利用
    parent→カットしてダミーに親子付けするか、ダミーから再親子付けするか 'cut'or'reparent'or'create'or'delete'
    createした場合はダミーペアレントを戻り値として返す
    objects→カット、リペアレントする対象親ノード
    dummyParent→リペアレントする場合は作成したダミーペアレントのノードを渡す。
    '''
    node_list = ['transform', 'joint', 'KTG_ModelRoot', 'KTG_SSCTransform']

    def main(self, objects='', dummyParent='', mode='cut'):
        self.objects = objects
        self.dummyParent = dummyParent
        # リストタイプじゃなかったらリストに変換する
        if not isinstance(self.objects, list):
            temp = self.objects
            self.objects = []
            self.objects.append(temp)
        for self.node in self.objects:
            if mode == 'create':
                self.dummyParent = cmds.spaceLocator(name='dummyLocatorForParent')
                return self.dummyParent
            elif mode == 'delete':
                cmds.delete(self.dummyParent)
                return
            elif mode == 'cut':
                self.cutChildNode()
                return
            elif mode == 'parent':
                self.reparentNode()
                return

    def cutChildNode(self):
        # 処理ノードの親子を取得しておく
        nodeChildren = cmds.listRelatives(self.node, children=True, fullPath=True)
        for child in nodeChildren:
            # 子のノードがトランスフォームならダミーに親子付けして退避
            if cmds.nodeType(child) in self.node_list:
                cmds.parent(child, self.dummyParent)

    def reparentNode(self):
        dummyChildren = cmds.listRelatives(self.dummyParent, children=True, fullPath=True)
        for child in dummyChildren:
            if cmds.nodeType(child) in self.node_list:
                cmds.parent(child, self.node)