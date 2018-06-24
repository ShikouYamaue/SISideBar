# -*- coding: utf-8 -*-
from maya import cmds
from . import weight
from . import common
from . import freeze
from . import lang
import os
import json

#UVを簡単にコピーペーストするクラス
class UVCopyPaste():
    copy_uvs = []
    def __init__(self):
        #ホットキーからの利用に対応するため外部ファイル書き出し
        self.saveDir = os.path.join(
            os.getenv('MAYA_APP_DIR'),
            'Scripting_Files')
        try:
            if not os.path.exists(self.saveDir):
                os.makedirs(os.path.dirname(self.saveDir))
        except Exception as e:
            print e.message
        self.saveFile = self.saveDir+'\\copy_uv.json'
        
    def copy_uv(self):
        sel = cmds.ls(sl=True, l=True)
        self.copy_uvs = cmds.polyListComponentConversion(sel, tuv=True)
        self.copy_uvs = cmds.filterExpand(self.copy_uvs, sm=35)
        if self.copy_uvs:
            save_uv_data = {'copy_uv':self.copy_uvs }
            with open(self.saveFile, 'w') as f:
                json.dump(save_uv_data, f)
            
    def paste_uv(self, mode='component'):
        if os.path.exists(self.saveFile):
            with open(self.saveFile, 'r') as f:
                save_uv_data = json.load(f)
            self.copy_uvs = save_uv_data['copy_uv']
        else:
            return
        sel = cmds.ls(sl=True, l=True)
        self.paste_uvs = cmds.polyListComponentConversion(sel, tuv=True)
        self.paste_uvs = cmds.filterExpand(self.paste_uvs, sm=35)
        cmds.select(self.paste_uvs, r=True)
        cmds.selectMode(o=True)
        target_obj = [obj.split('.')[0] for obj in cmds.ls(sl=True, l=True)]
        #print 'get target :', target_obj
        freeze_m.main(mesh=target_obj)
        if not self.paste_uvs:
            return
        paste_objects = list(set([uv.split('.')[0] for uv in self.paste_uvs]))
        #cmds.bakePartialHistory(paste_objects, pre=True)
        #print paste_objects
        paste_uvs_dict = {obj:[] for obj in paste_objects}
        #print paste_uvs_dict
        for uv in map(lambda uv:uv.split('.'), self.paste_uvs):
            paste_uvs_dict[uv[0]] += ['.'.join(uv)]
        #print paste_uvs_dict
        for paste_uvs in paste_uvs_dict.values():
            #print paste_uvs
            cmds.select(cl=True)
            cmds.select(self.copy_uvs, r=True)
            cmds.select(paste_uvs, add=True) 
            if mode == 'component':
                sample_space = 4 
            if mode == 'world':
                sample_space = 0
            #print mode
            cmds.transferAttributes(flipUVs=0, transferPositions=0, transferUVs=2, searchMethod=3, 
                                                transferNormals=0, transferColors=0, colorBorders=1, sampleSpace=sample_space)

        freeze_m.main(mesh=target_obj)
        cmds.select(target_obj, r=True) 

#UVセットをリネーム、マルチUVの削除など
class EditUVSet():
    msg01 = lang.Lang(
        en='No mesh selection.\nWould you like to process all of mesh in this scene?.',
        ja=u'選択メッシュがありません。\nシーン内のすべてのメッシュを処理しますか？'
    ).output()
    msg02 = lang.Lang(
        en='Yes',
        ja=u'はい'
    ).output()
    msg03 = lang.Lang(
        en='No',
        ja=u'いいえ'
    ).output()
    def main(self, mesh=None, delMultiUV=True, groupMultiUV=True, popUpMsg=True, exclusion=None, force=False):
        #popUpMsg→メッシュ全部を処理するメッセージを表示するかどうか
        #処理対象外UV_Set名を指定
        #force、空のセットも問い合わせず強制処理するか。
        # リストタイプじゃなかったらリストに変換する
        if not isinstance(exclusion, list):
            exclusion = [exclusion]
        self.exclusion = exclusion
        self.popUpMsg = popUpMsg
        self.delMultiUV = delMultiUV#UV削除指定フラッグ
        self.groupMultiUV = groupMultiUV
        self.force = force
        if mesh:
            polygonMeshs = common.search_polygon_mesh(mesh, serchChildeNode=False, fullPath=True)
        if not mesh:
            polygonMeshs = self.ajustSelection()
        #print len(polygonMeshs)
        #マルチUVセット化フラグが有効ならチェックしに行く
        if self.groupMultiUV is True:
            self.checkMultiUVSet()
        #メッシュがあったらメッシュごとに処理、内包表記
            
        [self.crenupMultiUV() for self.mesh in polygonMeshs if len(polygonMeshs) != 0]
        
        cmds.select(polygonMeshs)
            
        #処理後、マルチUVでなくなったメッシュを取り除くためもう一度チェック
        if self.groupMultiUV is True:
            self.checkMultiUVSet()
        #メンバーゼロのセットを取り除く
        if self.groupMultiUV is True:
            self.removeZeroSet()
        
    def checkMultiUVSet(self):
        self.set = cmds.ls('Multi_UV_Set')
        if not self.set:
            self.set = cmds.sets(em=True,n='Multi_UV_Set')
        else:
            self.set = self.set[0]
            #セットメンバーを検索してマルチUVでない場合は取り除く
            setMembers = []
            setMembers = cmds.sets(self.set, int=self.set)
            for menber in setMembers:
                uvSet = cmds.polyUVSet(menber, q=True, allUVSets=True)
                if len(uvSet) < 2:
                    cmds.sets(menber,rm='Multi_UV_Set')   #setに追加
                        
    def removeZeroSet(self):
        memberTemp = cmds.sets(self.set , int=self.set)
        if len(memberTemp)==0:
            cmds.delete(self.set)
        
    def ajustSelection(self):
        #選択したものからメッシュノードがあるものを取り出し。
        #何も選択されていなかったらシーン内のメッシュ全取得
        selection = cmds.ls(sl=True)
        #print len(selection)
        #print selection
        if self.popUpMsg:
            if len(selection) == 0:
                allMeshSel = cmds.confirmDialog(m=self.msg01, t='', b= [self.msg02, self.msg03], db=self.msg02, cb=self.msg03, icn='question',ds=self.msg03)
                #print allMeshSel
                if allMeshSel == self.msg02:
                    selection = cmds.ls(type='transform')
        else:
            if len(selection) == 0:
                #print 'process all of mesh'
                selection = cmds.ls(type='transform')
        #メッシュノードが存在したらリストに加える
        return [sel for sel in selection if common.search_polygon_mesh(sel)]
        
    def crenupMultiUV(self):
        self.defaultName = 'map'#デフォルト名
        #print self.mesh
        shapes = cmds.listRelatives(self.mesh, s=True, pa=True)
        self.shapes = shapes[0]
        #ヒストリ削除
        cmds.bakePartialHistory(self.shapes,ppt=True)
        #cmds.bakePartialHistory(self.shapes,preCache=True)
        
        self.uvSetAll = cmds.polyUVSet(self.mesh, q=True, allUVSets=True)
        self.currentSet = cmds.polyUVSet(self.mesh, q=True, currentUVSet=True)
        
        #現在のUVが空かどうか調べてスキップフラグがTrueなら関数抜ける
        if not self.checkCurrentUV():
            print 'Skip (No UV in Current UVSet) : ' + self.mesh
            return
        self.delUVFlag = True
        self.uvNum = 1#マルチUVリネーム用
        #マルチUVの指定名があれば削除フラグをFalseに
        if 'Multi_UV' in self.mesh or self.delMultiUV is False:
            self.delUVFlag = False
            self.uvNum = len(self.uvSetAll)#マルチUVリネーム用
        
        if len(self.uvSetAll) > 0:#UVセットがあったら
            self.deleteUV()
            #UVセットの名前を変更、マルチUVの場合は繰り返し処理
            self.renameUVSet()
        if self.groupMultiUV is True and len(self.uvSetAll) > 1:#UVセットが複数の場合セットに追加する
            cmds.sets(self.mesh,add='Multi_UV_Set')   #setに追加
            
    def checkCurrentUV(self):
        if self.force:
            return True
        if cmds.polyEvaluate(self.mesh, uv=True, uvs=self.currentSet[0]) == 0:
            msg04 = common.LanguageMessage(
                en=str(self.mesh)+' : Current UVSet ['+str(self.currentSet[0])+'] is empty.\nDo you skip this mesh?',
                ja=self.mesh+u' : 現在のUVSet ['+self.currentSet[0]+u'] が空です。\nこのメッシュをスキップしますか？'
            )   
            self.msg04 = msg04.output
            self.skipMesh = cmds.confirmDialog(m=self.msg04, t='', b= [self.msg02, self.msg03], db=self.msg02, cb=self.msg03, icn='question',ds=self.msg03)
        else:
            return True#スキップしない
        if self.skipMesh == self.msg02:
            return False#スキップする
        else:
            return True#スキップしない
    
    def deleteUV(self):
        #print self.uvSetAll
        #print self.uvSetAll
        if len(self.uvSetAll) > 1 and self.delUVFlag:#UVセットが複数あったら削除処理
            cmds.polyUVSet(self.mesh, uvSet=self.uvSetAll[0], e=True, currentUVSet=True)#カレントを1に
            dummy = common.TemporaryReparent().main(mode='create')
            for var in range(1,len(self.uvSetAll)):
                # print self.uvSetAll[var]
                # tempUV = cmds.polyUVSet(self.mesh, q=True, allUVSets=True)
                # for uv in tempUV:
                    # print u'UV名確認用 : '+str(uv)
                if self.uvSetAll[var] == self.currentSet[0]:
                    #親子付けしたまま親のノードを処理するとなぜかUVSet名で処理できないので退避しておく
                    common.TemporaryReparent().main(self.mesh, dummyParent=dummy, mode='cut')
                    #カレントUVを1番目にコピー
                    cmds.polyCopyUV( self.mesh, uvi=self.uvSetAll[var], uvs=self.uvSetAll[0])
                    #親子付けを戻す
                    common.TemporaryReparent().main(self.mesh, dummyParent=dummy, mode='parent')
                if self.uvSetAll[var].split('.')[-1] in self.exclusion:
                    print 'Skip UV in Exclusion List :', self.uvSetAll[var]
                    continue
                #最初のUVセット以外は削除
                try:
                    print 'Delete UV Set : '+self.mesh+'.'+self.uvSetAll[var]
                    cmds.polyUVSet(self.mesh, uvSet=self.uvSetAll[var], delete=True)
                except:
                    print 'Delete UV Set Error : '+self.mesh+'.'+self.uvSetAll[var]+' is not exsist\n'+\
                            'Skip this mesh object'
            #ダミー削除
            common.TemporaryReparent().main(dummyParent=dummy, mode='delete')
            #ヒストリ削除
            cmds.bakePartialHistory(self.shapes,ppt=True)
            # cmds.bakePartialHistory(self.shapes,preCache=True)
        
    def renameUVSet(self):
        #スキンウェイト書き戻し用、ウェイトを保存しておく。
        if self.uvSetAll[0] != 'map1' or len(self.uvSetAll) > 1:
            weight.WeightCopyPaste().main(self.mesh, mode='copy', saveName=__name__)
            for self.var in range(1, self.uvNum+1):
                var = str(self.var)
                renameSet = self.uvSetAll[self.var-1]
                if renameSet != self.defaultName+var:
                    print 'Rename UV Set : '+self.mesh+'.'+renameSet+' >>> '+self.defaultName+var
                    # transfer_weight(self.mesh,skinTemp[0])
                    cmds.bakePartialHistory(self.shapes,preCache=True)#デフォーマヒストリも削除しないとリネーム後UVなくなる
                    cmds.polyUVSet(self.mesh, uvSet=renameSet, newUVSet=self.defaultName+var, e=True, rename=True)
            #ウェイトを書き戻してくる
            weight.WeightCopyPaste().main(self.mesh, mode='paste', saveName=__name__)