#!/usr/bin/env python
# -*- coding: utf-8 -*-
from maya import cmds
from . import qt
from . import common
from . import lang
import os
import shutil

# PySide2、PySide両対応
import imp

try:
    imp.find_module("PySide2")
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except ImportError:
    from PySide.QtGui import *
    from PySide.QtCore import *


def clean_up_texture():
    # シーン内の重複したテクスチャをまとめる&適正な名前にリネーム
    attrPort = [".outColor", ".outAlpha", ".outTransparency"]
    # クリーンアップ除外リスト#[[リストの中はand指定], [リストの外はor指定]]
    excludeList = [["WiiU", "Eye"], ["_UVanim"]]
    # 除外リストを有効化するために先にリネームを一回かけておく
    rename_textures(attrPort)
    # もっかいテクスチャ取得
    textures = cmds.ls(tex=True)
    cmpareTex = cmds.ls(tex=True)
    # 重複したテクスチャの接続を1枚にまとめる
    for texA in textures:
        # 除外リストの項目を探索
        for exd in excludeList:
            for exStr in exd:
                # 項目が含まれなかったらbreakしてクリーンアップ処理に入る
                if not exStr in texA:
                    break
            else:
                print("Exclude Crean Up Texture :", texA)
                # 項目がすべて含まれたら外周ループでbreakしてクリーンアップ処理に入らない
                break
        else:  # 除外項目探索でブレイクされなかったら処理
            try:
                sourceNameA = cmds.getAttr(texA + ".fileTextureName")
            except:
                print("Get source file error : " + texA)
                continue
            del cmpareTex[0]  # 2重に比較しないように1番目の変数を削除
            for texB in cmpareTex:
                if texA != texB:
                    try:
                        sourceNameB = cmds.getAttr(texB + ".fileTextureName")
                    except:
                        print("Get source file error : " + texB)
                        continue
                    if sourceNameA == sourceNameB:
                        # print(texB)
                        for portName in attrPort:
                            # 接続されたノードを返す。pフラグでアトリビュート名を合わせて取得。
                            connectItems = cmds.listConnections(
                                texB + portName, p=True
                            )
                            # 接続を取得した変数がnoneTypeでなければ（接続があれば）
                            if connectItems is not None:
                                for cItem in connectItems:
                                    cmds.connectAttr(
                                        texA + portName, cItem, f=True
                                    )
    # 念のためもっかいリネーム
    rename_textures(attrPort)


def rename_textures(delUnuseTex=True):
    attrPort = [".outColor", ".outAlpha", ".outTransparency"]
    textures = cmds.ls(tex=True)
    # テクスチャを一括リネーム、未使用のものは削除
    for tex in textures:
        deleteFlag = True  # 削除フラグ
        for portName in attrPort:
            # 接続されたノードを返す。pフラグでアトリビュート名を合わせて取得。
            try:
                connectItems = cmds.listConnections(tex + portName, p=True)
            except:
                print("Get Attribute Error : " + texA + "." + portName)
                continue
            # 接続を取得した変数がnoneTypeでなければ（接続があれば）
            if connectItems is not None:
                # if not isinstance(connectItems,type(None)):
                deleteFlag = False  # 削除フラグをFalseに
        if deleteFlag and delUnuseTex:  # 削除フラグがTrueなら
            cmds.delete(tex)  # テクスチャ削除
            continue  # 以降のリネーム処理を行わずfor文の最初に戻る
        try:
            sourceName = cmds.getAttr(tex + ".fileTextureName")
            fileExpName = sourceName.split("/")[-1]
            fileExpName = fileExpName.split("\\")[-1]
            fileName = fileExpName.split(".")[0]
            cmds.rename(tex, fileName)
        except:
            print("Rename Error : " + tex)
            continue


def set_color_gain():
    textures = cmds.ls(tex=True)
    # カラーのゲインを1に
    for tex in textures:
        print(tex)
        cmds.setAttr(
            tex + ".colorGain",
            1,
            1,
            1,
            type="double3",
        )


class GatherPlace2d:
    def __init__(self):
        materials = cmds.ls(mat=True)
        for mat in materials:
            self.__nodeName = []  # サイクル接続されたノードどうしでの無限ループ回避
            self.place2dItems = []
            self.searchPlace2d(mat)
            if len(self.place2dItems) != 0:
                self.reconnectAttr()

    # place2dをつなぎ直すメソッド
    def reconnectAttr(self):
        base2d = self.place2dItems[0]
        del self.place2dItems[0]
        for place2d in self.place2dItems:
            attributes = cmds.listAttr(place2d)
            for attr in attributes:
                # 接続されたノードを返す。pフラグでアトリビュート名を合わせて取得。
                connectItems = cmds.listConnections(
                    place2d + "." + attr, p=True, d=True, s=False
                )
                # 接続を取得した変数がnoneTypeでなければ（接続があれば）
                if connectItems is not None:
                    for cItem in connectItems:
                        # アトリビュート接続
                        try:
                            cmds.connectAttr(
                                base2d + "." + attr, cItem, f=True
                            )
                        except:
                            print(
                                "can not connect : "
                                + base2d
                                + "."
                                + attr
                                + " to "
                                + cItem
                            )
                # ソース側の接続
                connectItems = cmds.listConnections(
                    place2d + "." + attr, p=True, d=False, s=True
                )
                if connectItems is not None:
                    for cItem in connectItems:
                        try:
                            cmds.connectAttr(
                                cItem, base2d + "." + attr, f=True
                            )
                        except:
                            print(
                                "can not connect : "
                                + cItem
                                + " to "
                                + base2d
                                + "."
                                + attr
                            )
        for place2d in self.place2dItems:
            deleteFlag = True  # 削除フラグ
            attributes = cmds.listAttr(place2d)
            for attr in attributes:
                if attr != "message":
                    # 接続されたノードを返す。pフラグでアトリビュート名を合わせて取得。
                    connectItems = cmds.listConnections(
                        place2d + "." + attr, p=True
                    )
                    # 接続を取得した変数がnoneTypeでなければ（接続があれば）
                    if not isinstance(connectItems, type(None)):
                        deleteFlag = False  # 削除フラグをFalseに
            if deleteFlag is True:
                cmds.delete(place2d)

    # 再帰処理しながら末端のplace2dノードを探索する

    def searchPlace2d(self, parentNode):
        # ノード接続のソース側のみ取得、dフラグで目的側は取得除外
        self.__nodeName.append(parentNode)  # 無限ループ回避リスト
        if cmds.nodeType(parentNode) == "place2dTexture":  # ノードタイプがplace2dなら
            self.place2dItems.append(parentNode)
            return
        connectNodes = cmds.listConnections(parentNode, s=True, d=False)
        if connectNodes is not None:
            for nextNode in connectNodes:
                recicleFlag = False  # 無限サイクル回避フラグ
                for nN in self.__nodeName:  # 既に処理済みのノードなら
                    if nN == nextNode:
                        recicleFlag = True  # サイクルフラグをTrueに
                if recicleFlag is False:  # 処理済みでないノードであれば再帰的呼び出しする
                    self.searchPlace2d(nextNode)


def textrue_path_2_local():
    selection = cmds.ls(type="file")
    for texture in selection:
        texName = cmds.getAttr(texture + ".fileTextureName")

        splitText = "/"
        # 区切り文字が\\の場合の対応
        if not splitText in texName:
            splitText = "\\"

        tempName = texName.split(splitText)
        newName = "sourceimages" + splitText + tempName[-1]
        cmds.setAttr(texture + ".fileTextureName", newName, type="string")


def texture_path_2_local_with_copy():
    all_textures = cmds.ls(type="file")
    pj_path = cmds.workspace(q=1, rd=1)
    tx_path = pj_path + "sourceimages/"

    copy_textures = []
    un_copy_texture = []
    same_texture = []
    msg = "- Result -"
    for texture in all_textures:
        texName = cmds.getAttr(texture + ".fileTextureName")

        splitText = "/"
        # 区切り文字が\\の場合の対応
        if not splitText in texName:
            splitText = "\\"
        tempName = texName.split(splitText)
        file_name = tempName[-1]
        # 外部ファイルコピー
        if not texName.startswith("sourceimages"):
            if os.path.exists(texName):
                try:
                    local_path = tx_path + file_name
                    shutil.copyfile(texName, local_path)
                    copy_textures.append(file_name)
                except shutil.Error:
                    same_texture.append(file_name)
            else:
                un_copy_texture.append(file_name)

        newName = "sourceimages" + splitText + file_name
        cmds.setAttr(texture + ".fileTextureName", newName, type="string")
    if copy_textures:
        msg += "\n*** Copy file to local directory ***"
        for tex in copy_textures:
            msg += "\n" + tex
    if un_copy_texture:
        msg += "\n*** Copy Error / Texture file not found ***"
        for tex in un_copy_texture:
            msg += "\n" + tex
    if same_texture:
        msg += "\n*** Copy Error / Texture already exist in locals ***"
        for tex in same_texture:
            msg += "\n" + tex
    cmds.confirmDialog(m=msg)
