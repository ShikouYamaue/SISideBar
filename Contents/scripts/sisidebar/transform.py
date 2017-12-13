# coding:utf-8
from . import freeze
from . import common
from . import lang
from . import qt
from maya import cmds
from maya import mel
import pymel.core as pm
import itertools
try:
    import numpy as np
    np_flag = True
except:
    np_flag = False
    
def reset_pivot_pos(nodes):
    if not nodes:
        nodes = cmds.ls(sl=True, tr=True, l=True)
    for s in nodes:
        cmds.xform(s+'.scalePivot', t=[0, 0, 0], os=True)
        cmds.xform(s+'.rotatePivot', t=[0, 0, 0], os=True)
        
def move_center_each_object():
    object_mode = cmds.selectMode( q=True, o=True )
    cmds.selectMode(o=True)
    selection = cmds.ls(sl=True, l=True)
    meshes = common.search_polygon_mesh(selection, fullPath=True, nurbs=True)
    if not meshes:
        return
    dummy = common.TemporaryReparent().main(mode='create')
    for m in meshes:
        cmds.selectMode(o=True)
        common.TemporaryReparent().main(m, dummyParent=dummy, mode='cut')
        cmds.select(m, r=True)
        if not object_mode:
            cmds.selectMode(co=True)
        move_center2selection()
        common.TemporaryReparent().main(m, dummyParent=dummy, mode='parent')
    common.TemporaryReparent().main(dummyParent=dummy, mode='delete')
    freeze.main(mesh=selection)
    cmds.select(selection, r=True)
        
def move_center2selection():
    if not cmds.ls(sl=True):
        return
    if cmds.selectMode( q=True, co=True ):
        selection = cmds.ls(sl=True)
        selMode='component'
        #カーブもとっておく
        cv_selection = cmds.ls(sl=True, type='double3', fl=True)
        verticies = cmds.polyListComponentConversion(selection, tv=True)
        if verticies:
            verticies = cmds.filterExpand(verticies, sm=31)+cv_selection
        else:
            verticies = cv_selection
        #print verticies
        center = [0, 0, 0]
        for i in range(3):
            center[i] = sum([cmds.pointPosition(vtx, w=True)[i] for vtx in verticies])/len(verticies)
        #print center
    elif cmds.selectMode( q=True, o=True ):
        selMode='object'
    #スムース直後だとうまくオブジェクト選択にならないときがあるのでいったんコンポーネントを経由
    cmds.selectMode(co=True)
    cmds.selectMode(o=True)
    selection = cmds.ls(sl=True, l=True, tr=True)
    
    childeNodes = common.search_polygon_mesh(selection, serchChildeNode=True, fullPath=True, nurbs=True)
    #print childeNodes
    
    selection = list(set(selection + childeNodes))
    preLock = {}
    for sel in selection:
        preLock[sel] = cmds.getAttr(sel+'.translateX', lock=True)
        for ax in ['X','Y','Z']:
            cmds.setAttr(sel+'.translate'+ax, lock=False)
            
    if selMode == 'object':
        #正しいバウンディングボックスを得るために複製、ベイク、取得、削除する
        duplicate_mesh = cmds.duplicate(selection, rc=True)#子の名前を固有にしてエラー回避rc=True
        cmds.bakePartialHistory(duplicate_mesh, ppt=True)
        bBox = cmds.exactWorldBoundingBox(duplicate_mesh, ignoreInvisible=False)
        center = [(bBox[i]+bBox[i+3])/2 for i in range(3)]
        cmds.delete(duplicate_mesh)
        
    for sel in selection:
        if np_flag:
            sel_pos = np.array(cmds.xform(sel, q=True, t=True, ws=True))
            offset = sel_pos - np.array(center)
           # offset *= 2
        else:
            sel_pos = cmds.xform(sel, q=True, t=True, ws=True)
            offset = [p-c for p, c in zip(sel_pos, center)]
            
        dummy = common.TemporaryReparent().main(mode='create')#モジュールでダミーの親作成
        common.TemporaryReparent().main(sel, dummyParent=dummy, mode='cut')

        cmds.xform(sel, t=center, ws=True)

        #カーブもとっておく
        cv_selection = cmds.ls(sel+'.cv[*]', fl=True)
        #print cv_selection
        verticies = cmds.polyListComponentConversion(sel, tv=True)
        if verticies:
            verticies = cmds.filterExpand(verticies, sm=31)+cv_selection
        else:
            verticies = cv_selection
        #print verticies
        #print offset
        cmds.xform(verticies, t=offset, r=True, ws=True)
        
        cmds.xform(sel+'.scalePivot', t=center, ws=True)
        cmds.xform(sel+'.rotatePivot', t=center, ws=True)
        
        if preLock[sel]:
            for ax in ['X','Y','Z']:
                cmds.setAttr(sel+'.translate'+ax, lock=True)
                
        #cmds.xform(sel+'.scalePivot', t=[0, 0, 0], os=True)
        #cmds.xform(sel+'.rotatePivot', t=[0, 0, 0], os=True)

        common.TemporaryReparent().main(sel, dummyParent=dummy, mode='parent')
        common.TemporaryReparent().main(sel, dummyParent=dummy, mode='delete')

    freeze.main(mesh=selection)
    cmds.select(selection, r=True)
    
def reset_actor():
    from . import sisidebar_sub
    sel = cmds.ls(sl=True, l=True)
    joints = cmds.ls(sl=True, l=True, type='joint')
    if not joints:
        joints = []
    for s in sel:
        if cmds.nodeType(s) == 'KTG_ModelRoot':
            child_joints = cmds.ls(cmds.listRelatives(s, ad=True, f=True), l=True, type='joint')
            if child_joints:
                joints += child_joints
    if not sel:
        joints = cmds.ls(l=True, type='joint')
    for j in joints:
        con_info = cmds.connectionInfo(j+'.bindPose', dfs=True)
        if not con_info:
            continue
        con_info = con_info[0]
        bind_info = con_info.replace('world', 'xform')
        pose = cmds.getAttr(bind_info)
        cmds.xform(j, m=pose)
    sisidebar_sub.get_matrix()
        
def set_joint_orient(reset=True):
    from . import sisidebar_sub
    joints = cmds.ls(sl=True, type='joint')

    if len(joints) == 0:
        confirm_mes = lang.Lang(
            en='Joint is not selected\nDo you want to process all the joints in the scene? ',
            ja=u'ジョイントが選択されていません\nシーン内のすべてのジョイントを処理しますか？'
        )
        rtn = pm.cmds.confirmDialog(title='Confirm', message=confirm_mes.output(), button=['Yes', 'No'], defaultButton='Yes',
                              cancelButton='No', dismissString='No')
        if rtn != 'Yes':
            return False

        joints = cmds.ls('*', type='joint')
        if len(joints) == 0:
            pm.confirmDialog(title='Warning', message='Joint Object Nothing.', button='OK', icon='Warning')
            return False

    for j in joints:
        # マトリックス取得
        mat = cmds.xform(j, q=True, m=True)
        # 回転とジョイントの方向をいったん0に
        cmds.rotate(0, 0, 0, j, objectSpace=True)
        cmds.joint(j, e=True, orientation=[0, 0, 0])
        # マトリックス再設定、回転のみに数値が入る。
        cmds.xform(j, m=mat)

        if reset:
            # 回転取得
            rot = cmds.xform(j, q=True, ro=True)
            # 回転を0にしてジョイントの方向に同じ値を移す
            cmds.rotate(0, 0, 0, j, objectSpace=True)
            cmds.joint(j, e=True, orientation=rot)
    sisidebar_sub.get_matrix()
            
def reset_transform(mode='', c_comp=False):
    #print 'comp mode :', c_comp
    from . import sisidebar_sub
    if cmds.selectMode(q=True, co=True):
        return
    selections = cmds.ls(sl=True, l=True)
    #子供のノード退避用ダミーペアレントを用意
    dummy = common.TemporaryReparent().main(mode='create')
    for sel in selections:
        if c_comp:
            common.TemporaryReparent().main(sel, dummyParent=dummy, mode='cut')
        if mode == 'all':
            cmds.xform(sel, t=[0, 0, 0])
            cmds.xform(sel, ro=[0, 0, 0])
            cmds.xform(sel, s=[1, 1, 1])
        if mode == 'trans':
            cmds.xform(sel, t=[0, 0, 0])
        if mode == 'rot':
            cmds.xform(sel, ro=[0, 0, 0])
        if mode == 'scale':
            cmds.xform(sel, s=[1, 1, 1])
        if mode == 'trans' or mode =='all':
            cmds.xform(sel+'.scalePivot', t=[0, 0, 0], os=True)
            cmds.xform(sel+'.rotatePivot', t=[0, 0, 0], os=True)
        if c_comp:
            common.TemporaryReparent().main(sel, dummyParent=dummy, mode='parent')
    common.TemporaryReparent().main(dummyParent=dummy, mode='delete')#ダミー親削除
    cmds.select(selections, r=True)
    sisidebar_sub.get_matrix()
        
#フリーズスケーリングをまとめて
def freeze_transform(mode='', c_comp=False):
    from . import sisidebar_sub
    selections = cmds.ls(sl=True, l=True)
    dummy = common.TemporaryReparent().main(mode='create')
    for sel in selections:
        try:
            if c_comp:
                common.TemporaryReparent().main(sel, dummyParent=dummy, mode='cut')
            if mode == 'all':
                cmds.makeIdentity(sel, n=0, s=1, r=1, jointOrient=1, t=1, apply=True, pn=1)
            if mode == 'trans':
                cmds.makeIdentity(sel, n=0, s=0, r=0, jointOrient=0, t=1, apply=True, pn=1)
            if mode == 'rot':
                cmds.makeIdentity(sel, n=0, s=0, r=1, jointOrient=0, t=0, apply=True, pn=1)
            if mode == 'scale':
                cmds.makeIdentity(sel, n=0, s=1, r=0, jointOrient=0, t=0, apply=True, pn=1)
            if mode == 'joint':
                cmds.makeIdentity(sel, n=0, s=0, r=0, jointOrient=1, t=0, apply=True, pn=1)
            if mode == 'trans' or mode =='all':
                cmds.xform(sel+'.scalePivot', t=[0, 0, 0], os=True)
                cmds.xform(sel+'.rotatePivot', t=[0, 0, 0], os=True)
            if c_comp:
                common.TemporaryReparent().main(sel, dummyParent=dummy, mode='parent')
        except Exception as e:
            print e.message
    common.TemporaryReparent().main(dummyParent=dummy, mode='delete')#ダミー親削除
    cmds.select(selections, r=True)
    sisidebar_sub.get_matrix()
        
def match_transform(mode=''):
    from . import sisidebar_sub
    pre_sel = cmds.ls(sl=True, l=True)
    selection = cmds.ls(sl=True, l=True, type='transform')
    if not selection:
        return
    sisidebar_sub.set_maching(nodes=selection, mode=mode ,pre_sel=pre_sel)
    
    msg = lang.Lang(en=u"<hl>Select Matching Object</hl>",
                            ja=u"<hl>一致対象オブジェクトを選択してください</hl>")
    cmds.inViewMessage( amg=msg.output(), pos='midCenterTop', fade=True )
    #cmds.select(cl=True)
    maching_tool = cmds.scriptCtx( title='Much Transform',
                        totalSelectionSets=3,
                        cumulativeLists=True,
                        expandSelectionList=True,
                        tct="edit",
                        setNoSelectionPrompt='Select the object you want to matching transform.'
                        )
    cmds.setToolTo(maching_tool)
    jobNum = cmds.scriptJob(ro=True, e=('SelectionChanged', qt.Callback(sisidebar_sub.trs_matching)), protected=True)
    sisidebar_sub.get_matrix()
    
#アトリビュートの桁数を丸める
def round_transform(mode='', digit=3):
    from . import sisidebar_sub
    sel = cmds.ls(sl=True, l=True)

    axis = ['X', 'Y', 'Z']
    if mode == 'all':
        mode_list = ['.translate', '.rotate', '.scale', '.jointOrient']
    else:
        mode_list = ['.' + mode]
    for s in sel:
        for a, m in itertools.product(axis, mode_list):
            #print cmds.nodeType(s) , m
            #print cmds.nodeType(s) != 'joint'
            if cmds.nodeType(s) != 'joint' and m == '.jointOrient':
                #print m == '.jointOrient'
                #print 'Node Type Error'
                continue
            try:
                v = cmds.getAttr(s+m+a)
                #print v
                v = round(v, digit)
                cmds.setAttr(s+m+a, v)
                #print v
            except Exception as e:
                print e.message
    sisidebar_sub.get_matrix()

    
    
    
    