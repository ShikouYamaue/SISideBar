# coding:utf-8
from . import freeze
from . import common
from . import lang
from . import qt
from maya import cmds
from maya import mel
import pymel.core as pm
import itertools
import os
try:
    import numpy as np
    np_flag = True
except:
    np_flag = False
import imp
try:
    imp.find_module('PySide2')
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except ImportError:
    from PySide.QtGui import *
    from PySide.QtCore import *
maya_ver = int(cmds.about(v=True)[:4])
    
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
            
def reset_transform(mode='', c_comp=False, reset_pivot=True):
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
            if reset_pivot:
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
    #下からのマルチ選択でも正しく上からフリーズできるように階層深さでソート
    sel_depth = [[sel, check_depth(sel)] for sel in selections]
    sel_depth = sorted(sel_depth, key=lambda a:a[1])
    for sel in sel_depth:
        sel = sel[0]
        dummy = common.TemporaryReparent().main(mode='create')
        srt_dummy = common.TemporaryReparent().main(mode='create')
        #common.TemporaryReparent().main(sel, dummyParent=dummy, mode='cut')
        if not c_comp:
            set_maching(nodes=srt_dummy, mode='all', pre_sel=selections)
            matching_obj=srt_dummy
            trs_matching(node=sel, sel_org=False)
        common.TemporaryReparent().main(sel,dummyParent=dummy, srtDummyParent=srt_dummy, mode='custom_cut', preSelection=selections)
        attr_lock_flag_list = check_attr_locked(sel)
        try:
            if mode == 'all':
                cmds.makeIdentity(sel, n=0, s=1, r=1, jointOrient=1, t=1, apply=True, pn=1)
                cmds.xform(srt_dummy, t=[0, 0, 0])
                cmds.xform(srt_dummy, ro=[0, 0, 0])
                cmds.xform(srt_dummy, s=[1, 1, 1])
            if mode == 'trans':
                cmds.makeIdentity(sel, n=0, s=0, r=0, jointOrient=0, t=1, apply=True, pn=1)
                cmds.xform(srt_dummy, t=[0, 0, 0])
            if mode == 'rot':
                cmds.makeIdentity(sel, n=0, s=0, r=1, jointOrient=0, t=0, apply=True, pn=1)
                cmds.xform(srt_dummy, ro=[0, 0, 0])
            if mode == 'scale':
                cmds.makeIdentity(sel, n=0, s=1, r=0, jointOrient=0, t=0, apply=True, pn=1)
                cmds.xform(srt_dummy, s=[1, 1, 1])
            if mode == 'joint':
                if cmds.nodeType(sel) == 'joint':
                    cmds.makeIdentity(sel, n=0, s=0, r=0, jointOrient=1, t=0, apply=True, pn=1)
                    cmds.xform(srt_dummy, ro=[0, 0, 0])
            if mode == 'trans' or mode =='all':
                cmds.xform(sel+'.scalePivot', t=[0, 0, 0], os=True)
                cmds.xform(sel+'.rotatePivot', t=[0, 0, 0], os=True)
        except Exception as e:
            print e.message
            cmds.inViewMessage( amg=e.message, pos='midCenterTop', fade=True, ta=0.75, a=0.5)
        set_attr_locked(sel, attr_lock_flag_list)
        common.TemporaryReparent().main(sel, dummyParent=dummy, mode='parent')
        common.TemporaryReparent().main(sel, dummyParent=srt_dummy, mode='parent')
        common.TemporaryReparent().main(dummyParent=dummy, mode='delete')#
        common.TemporaryReparent().main(dummyParent=srt_dummy, mode='delete')#ダミー親削除
    cmds.select(selections, r=True)
    sisidebar_sub.get_matrix()

global all_attr_list
all_attr_list = [['.sx', '.sy', '.sz'], ['.rx', '.ry', '.rz'], ['.tx', '.ty', '.tz']]
def check_attr_locked(node):
    attr_lock_flag_list = [[None, None, None], [None, None, None], [None, None, None]]
    for i,attrs in enumerate(all_attr_list):
        for j, attr in enumerate(attrs):
            attr_lock_flag_list[i][j] = cmds.getAttr(node+attr, lock=True)
            cmds.setAttr(node+attr, lock=False)
    return attr_lock_flag_list 
def set_attr_locked(node, attr_lock_flag_list):
    for i,attrs in enumerate(all_attr_list):
        for j, attr in enumerate(attrs):
            cmds.setAttr(node+attr, lock=attr_lock_flag_list[i][j])
    
    
def check_depth(node):
    count = 0
    while True:
        parent = cmds.listRelatives(node, p=True)
        if not parent:
            break
        node = parent
        count+=1
    return count
    
def match_transform(mode='', child_comp=False):
    from . import sisidebar_sub
    pre_sel = cmds.ls(sl=True, l=True)
    selection = cmds.ls(sl=True, l=True, type='transform')
    if not selection:
        return
    cmds.undoInfo(openChunk=True)
    set_maching(nodes=selection, mode=mode ,pre_sel=pre_sel, child_comp=child_comp)
    
    msg = lang.Lang(en=u"<hl>Select Matching Object</hl>",
                            ja=u"<hl>一致対象オブジェクトを選択してください</hl>")
    cmds.inViewMessage( amg=msg.output(), pos='midCenterTop', fade=True )
    #cmds.select(cl=True)
    maching_tool = cmds.scriptCtx( title='Much Transform',
                        totalSelectionSets=3,
                        cumulativeLists=True,
                        expandSelectionList=True,
                        toolCursorType="edit",
                        setNoSelectionPrompt='Select the object you want to matching transform.'
                        )
    #カスタムカーソルを設定
    image_path = os.path.join(os.path.dirname(__file__), 'icon/')
    my_cursor = QCursor(QPixmap(image_path+'picker.png'))
    QApplication.setOverrideCursor(my_cursor)
    #cmds.hudButton('HUDHelloButton', e=True, s=7, b=5, vis=1, l='Button', bw=80, bsh='roundRectangle', rc=match_cancel )
    global hud_but
    if maya_ver != 2017:
        try:
            hud_but = cmds.hudButton('HUD_match_cancel', s=7, b=5, vis=1, l='Cancel', bw=80, bsh='roundRectangle', rc=finish_matching)
            #print 'create'
        except:
            #print 'change'
            hud_but = cmds.hudButton('HUD_match_cancel',e=True, s=7, b=5, vis=1, l='Cancel', bw=80, bsh='roundRectangle', rc=finish_matching)
    jobNum = cmds.scriptJob(ro=True, e=('SelectionChanged', qt.Callback(trs_matching)), protected=True)
    sisidebar_sub.get_matrix()
def finish_matching():
    global hud_but
    global matching_obj
    cmds.select(cl=True)
    cmds.select(matching_obj, r=True)
    #print hud_but
    #キャンセルボタン削除
    if maya_ver != 2017:
        cmds.headsUpDisplay(removeID=int(hud_but))
    
    QApplication.restoreOverrideCursor()
    cmds.undoInfo(closeChunk=True)
    cmds.headsUpDisplay(removeID=int(hud_but))
    
#マッチトランスフォームオブジェクト情報を格納しておく
def set_maching(nodes=None, mode='', pre_sel=None, child_comp=False):
    global matching_obj
    global matching_mode
    global matching_pre_sel
    global child_comp_flag
    child_comp_flag = child_comp
    matching_obj = nodes
    matching_mode = mode
    matching_pre_sel = pre_sel
    
#マッチングを実行
def trs_matching(node=None, sel_org=True):
    global matching_obj
    global matching_mode
    global child_comp_flag
    #print matching_mode, matching_obj
    mode = matching_mode
    if node is None:
        mached_obj = cmds.ls(sl=True, l=True, type='transform')
    else:
        #print 'muched obj', node
        mached_obj = node
    if not mached_obj:
        if sel_org:
            finish_matching()
        return
    else:
        if isinstance(mached_obj, list):
            mached_obj = mached_obj[0]
    scl = cmds.xform(mached_obj, q=True, s=True, ws=True)
    rot = cmds.xform(mached_obj, q=True, ro=True, ws=True)
    pos = cmds.xform(mached_obj, q=True, t=True, ws=True)
    for obj in matching_obj:
        if mode == 'scale' or mode == 'all':
            cmds.scale(1.0, 1.0, 1.0, obj, pcp=True)
            ws_scl = cmds.xform(obj, q=True, s=True, ws=True)
            cmds.scale(scl[0]/ws_scl[0], scl[1]/ws_scl[1], scl[2]/ws_scl[2], obj, pcp=child_comp_flag)
        if mode == 'rotate' or mode == 'all':
            cmds.rotate(rot[0], rot[1], rot[2], obj, ws=True, pcp=child_comp_flag)
        if mode == 'translate' or mode == 'all':
            cmds.move(pos[0], pos[1], pos[2], obj, ws=True, pcp=child_comp_flag)
    if sel_org:
        finish_matching()
    
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

    
    
    
    