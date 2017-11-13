# -*- coding: utf-8 -*-
from maya import mel
from maya import cmds
from . import lang
from . import common
import os
import json

class WeightCopyPaste():
    def main(self, skinMeshes, mode='copy', saveName='default', method='index', weightFile='auto', 
                        threshold=0.2, engine='maya', tgt=1, path='default'):
        '''
        ウェイトデータの保存、読み込み関数
        mode→コピーするかペーストするか'copy'or'paste'
        saveName→ウェイトデータの保存フォルダ名。ツール、モデル名とかで分けたい場合に指定
        method→ペーストの仕方,「index」、「nearest」、「barycentric」、「over」
        「index」法は、頂点インデックスを使用してウェイトをオブジェクトにマッピングします。マッピング先のオブジェクトと書き出し後のデータのトポロジが同じ場合、これが最も便利な手法です。
        「nearest」法は、読み込んだデータのニアレスト頂点を検索し、ウェイト値をその値に設定します。これは、高解像度メッシュを低解像度メッシュにマッピングする場合に最適です。
        「barycentric」法はポリゴン メッシュでのみサポートされます。ターゲット ジオメトリのニアレスト三角を検索し、
        ソース ポイントと頂点の距離に応じてウェイトを再スケールします。これは通常、高解像度メッシュにマッピングされる粗いメッシュで使用されます。
        「over」法は「index」法に似ていますが、マッピング前に対象メッシュのウェイトがクリアされないため、一致していないインデックスのウェイトがそのまま維持されます。

        nearest と barycentricは不具合のため現状仕様不可能(処理が終わらない)2016/11/03現在
        →barycentric、bylinearはMaya2016Extention2から利用可能

        weightFile→メッシュ名検索でなく手動指定したい場合にパスを指定。methodのnearest、barycentricとセットで使う感じ。
        →Mayaコピー時にファイル名指定すると複数保存できないので注意。
        
        threshold→nearest,barycentricの位置検索範囲
        '''
        self.skinMeshes = skinMeshes
        self.saveName = saveName
        self.method = method
        self.weightFile = weightFile
        self.threshold = threshold
        self.engine = engine
        self.memShapes = {}
        self.target = tgt
        self.pasteMode = {'index':1, 'nearest':3}
        # リストタイプじゃなかったらリストに変換する
        if not isinstance(self.skinMeshes, list):
            temp = self.skinMeshes
            self.skinMeshes = []
            self.skinMeshes.append(temp)
        # ファイルパスを生成しておく
        if path == 'default':
            self.filePath = os.getenv('MAYA_APP_DIR') + '\\Scripting_Files\\weight\\' + self.saveName
        elif path == 'project':
            self.scene_path = '/'.join(cmds.file(q=True, sceneName=True).split('/')[:-1])
            self.protect_path = os.path.join(self.scene_path, 'weight_protector')
            try:
                if not os.path.exists(self.protect_path):
                    os.makedirs(self.protect_path)
            except Exception as e:
                print e.message
                return
            self.filePath = self.protect_pat+'\\' + self.saveName
        self.fileName = os.path.join(self.filePath, self.saveName + '.json')
        self.apiName = os.path.join(self.filePath, self.saveName + '.skn')
        # コピーかペーストをそれぞれ呼び出し
        if mode == 'copy':
            self.weightCopy()
        if mode == 'paste':
            self.weightPaste()

    def weightPaste(self):
        dummy = cmds.spaceLocator()
        for skinMesh in self.skinMeshes:
            # 読みに行くセーブファイル名を指定、autoならメッシュ名
            if self.weightFile == 'auto':
                weightFile = skinMesh
            else:
                weightFile = self.weightFile
            dstSkinCluster = cmds.ls(cmds.listHistory(skinMesh), type='skinCluster')
            # スキンクラスタがない場合はあらかじめ取得しておいた情報をもとにバインドする
            if not dstSkinCluster:
                meshName = str(weightFile).replace('|', '__pipe__')
                if os.path.exists(self.fileName):
                    try:
                        with open(self.fileName, 'r') as f:
                            saveData = json.load(f)
                            skinningMethod = saveData[weightFile + ';skinningMethod']
                            dropoffRate = saveData[weightFile + ';dropoffRate']
                            maintainMaxInfluences = saveData[weightFile + ';maintainMaxInfluences']
                            maxInfluences = saveData[weightFile + ';maxInfluences']
                            bindMethod = saveData[weightFile + ';bindMethod']
                            normalizeWeights = saveData[weightFile + ';normalizeWeights']
                            influences = saveData[weightFile + ';influences']
                        # 子のノードがトランスフォームならダミーに親子付けして退避
                        common.TemporaryReparent().main(skinMesh, dummyParent=dummy, mode='cut')
                        # バインド
                        dstSkinCluster = cmds.skinCluster(
                            skinMesh,
                            influences,
                            omi=maintainMaxInfluences,
                            mi=maxInfluences,
                            dr=dropoffRate,
                            sm=skinningMethod,
                            nw=normalizeWeights,
                            tsb=True,
                        )
                        dstSkinCluster = dstSkinCluster[0]
                        # 親子付けを戻す
                        common.TemporaryReparent().main(skinMesh, dummyParent=dummy, mode='parent')
                        tempSkinNode = skinMesh#親を取得するためスキンクラスタのあるノードを保存しておく
                    except Exception as e:
                        print e.message
                        print 'Not exist seved weight JSON data : ' + skinMesh
                        continue
            else:
                dstSkinCluster = dstSkinCluster[0]
                tempSkinNode = skinMesh#親を取得するためスキンクラスタのあるノードを保存しておく
            if self.engine == 'maya':
                # Pipeはファイル名に出来ないので変換しておく
                meshName = str(weightFile).replace('|', '__pipe__')
                # コロンはファイル名に出来ないので変換しておく
                meshName = str(meshName).replace(':', '__colon__')
                if os.path.isfile(self.filePath + '\\' + meshName + '.xml'):
                    if self.method == 'index' or self.method == 'over':
                        cmds.deformerWeights(meshName + '.xml',
                                             im=True,
                                             method=self.method,
                                             deformer=dstSkinCluster,
                                             path=self.filePath + '\\')
                    else:
                        cmds.deformerWeights(meshName + '.xml',
                                             im=True,
                                             deformer=dstSkinCluster,
                                             method=self.method,
                                             worldSpace=True,
                                             positionTolerance=self.threshold,
                                             path=self.filePath + '\\')
                    cmds.skinCluster(dstSkinCluster, e=True, forceNormalizeWeights=True)
                    print 'Weight paste to : ' + str(skinMesh)
                else:
                    print 'Not exist seved weight XML file : ' + skinMesh
        # ダミー親削除
        cmds.delete(dummy)
        cmds.select(self.skinMeshes, r=True)
            
    # ウェイト情報を保存する関数
    def weightCopy(self):
        saveData = {}
        # 保存ディレクトリが無かったら作成
        if not os.path.exists(self.filePath):
            os.makedirs(os.path.dirname(self.filePath + '\\'))  # 末尾\\が必要なので注意
        else:  # ある場合は中身を削除
            files = os.listdir(self.filePath)
            if files is not None:
                for file in files:
                    os.remove(self.filePath + '\\' + file)
        skinFlag = False
        for skinMesh in self.skinMeshes:
            try:
                cmds.bakePartialHistory(skinMesh, ppt=True)
            except:
                pass
            # ノードの中からスキンクラスタを取得してくる#inMesh直上がSkinClusterとは限らないので修正
            srcSkinCluster = cmds.ls(cmds.listHistory(skinMesh), type='skinCluster')
            if not srcSkinCluster:
                continue  # スキンクラスタがなかったら次に移行
            tempSkinNode = skinMesh#親を取得するためスキンクラスタのあるノードを保存しておく
            # スキンクラスタのパラメータ色々を取得しておく
            srcSkinCluster = srcSkinCluster[0]
            skinningMethod = cmds.getAttr(srcSkinCluster + ' .skm')
            dropoffRate = cmds.getAttr(srcSkinCluster + ' .dr')
            maintainMaxInfluences = cmds.getAttr(srcSkinCluster + ' .mmi')
            maxInfluences = cmds.getAttr(srcSkinCluster + ' .mi')
            bindMethod = cmds.getAttr(srcSkinCluster + ' .bm')
            normalizeWeights = cmds.getAttr(srcSkinCluster + ' .nw')
            influences = cmds.skinCluster(srcSkinCluster, q=True, inf=True)
            saveData[skinMesh + ';skinningMethod'] = skinningMethod
            saveData[skinMesh + ';dropoffRate'] = dropoffRate
            saveData[skinMesh + ';maintainMaxInfluences'] = maintainMaxInfluences
            saveData[skinMesh + ';maxInfluences'] = maxInfluences
            saveData[skinMesh + ';bindMethod'] = bindMethod
            saveData[skinMesh + ';normalizeWeights'] = normalizeWeights
            saveData[skinMesh + ';influences'] = influences
            skinFlag = True
            if self.engine == 'maya':
                # 読みに行くセーブファイル名を指定、autoならメッシュ名
                if self.weightFile == 'auto':
                    weightFile = skinMesh
                else:
                    weightFile = self.weightFile
                # Pipeはファイル名に出来ないので変換しておく
                meshName = str(weightFile).replace('|', '__pipe__')
                # コロンはファイル名に出来ないので変換しておく
                meshName = str(meshName).replace(':', '__colon__')
                cmds.deformerWeights(meshName + '.xml', export=True, deformer=srcSkinCluster, path=self.filePath + '\\')
        with open(self.fileName, 'w') as f:  # ファイル開く'r'読み込みモード'w'書き込みモード
            json.dump(saveData, f)