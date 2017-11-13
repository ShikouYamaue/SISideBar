# -*- coding: utf-8 -*- 
#SI Side Bar Culc
from maya import cmds
from maya import mel
import math
import qt
import datetime as dt
import imp
import os
from . import sisidebar_main as sb
try:
    import numpy as np
    np_flag = True
except:
    np_flag = False

global current_mode
global pre_mode
global group_mode
group_mode = False

def change_np_mode(mode):
    global np_flag
    np_flag = mode
    
def change_group_mode(mode):
    global group_mode
    group_mode = mode
    
#コンテキストが変更されたらmainに戻ってツール反映する
def change_context():
    #print 'culc get context :', cmds.currentCtx()
    #テクスチャUVエディタ上でのコンテキスト変更に対応するためにこちらからも実行
    sb.change_context()
    sb.check_option_parm()
    #sb.MainWindow().set_disable(mode=None)

#選択変更時のみの通り道を別途用意
pre_mode = None
def change_selection():
    #print '*+*+*+*+*+*+*+selection changed+*+*+*+*+*+*+* :', cmds.ls(sl=True)
    global bake_mode
    #print 'check bake_mode in culc sel:', bake_mode
    if bake_mode:
        #print 'return for center bake mode from change_selection:'
        return
    #return
    if group_mode:
        group_selection()
        #return
    get_matrix()
    #コンテキストのpodモードを選択タイプによって切り替える
    sb.chenge_manip_type()
    sb.change_selection_display()
    #sel = cmds.ls(sl=True)
    #cmds.select(cl=True)
    #cmds.select(sel, r=True)
    #コンテキストを切り替えてリアルタイム検出を有効にする。
    target_tool_list = ['scaleSuperContext', 'RotateSuperContext', 'moveSuperContext', 'selectSuperContext']
    global current_mode
    global pre_mode
    current_mode = cmds.selectMode(q=True, o=True)
    current_tool = cmds.currentCtx()
    #print 'current tool ;',  current_tool
    #エッジループ、フェースアイランド選択を利用出来るように、オブジェクトモードとコンポーネントモード切替時のみコンテキスト変更を行う
    if current_mode or pre_mode:
        if current_tool in target_tool_list:
            #print 'chanege context', current_tool
            cmds.setToolTo('selectSuperContext')
            cmds.setToolTo(current_tool)
    pre_mode = current_mode
    #cmds.undo()
    #get_matrix()
    #sb.check_option_parm()
    #オブジェクト変更があった場合はセンターをベイクして再度センターモードに入りなおす
    #print 'check center mode in culc :', center_mode
    if cmds.selectMode(q=True, o=True):
        if center_mode:
            #cmds.undoInfo(cn='cng_center', ock=True)
            sb.toggle_center_mode(mode=False, change=True)
            sb.toggle_center_mode(mode=True, change=True)
            #qt.Callback(sb.transform_center()
            sb.transform_center()
            #cmds.undoInfo(cn='cng_center', cck=True)
            return

def get_matrix():
    global sb
    from . import sisidebar_main as sb
    #print '-------------get Matrix---------------- :'
    #print 'select obj :', cmds.ls(sl=True)
    #current_tool = cmds.currentCtx()
    #print 'current tool ;',  current_tool
    #cmds.setToolTo('selectSuperContext')
    #cmds.setToolTo(current_tool)
        
    #一旦スケールX値をリセットしてメインウィンドウクラスに変更をお知らせする
    #sb.set_temp_text('change')
    sb.set_active_mute()
    scale = ['', '', '']
    rot = ['', '', '']
    trans = ['', '', '']
    if cmds.selectMode(q=True, o=True):
        selection = cmds.ls(sl=True, type='transform')
        if selection:
            s_list, r_list, t_list = get_srt(selection)
            #print 'get matrix :', s_list, r_list, t_list
            for i in range(3):
                if not all(s[i] == s_list[0][i] for s in s_list):
                    #print 'not same'
                    scale[i] = ''
                else:
                    #print 'same'
                    scale[i] = str(round(s_list[0][i], 3))
                if not all(r[i] == r_list[0][i] for r in r_list):
                    rot[i] = ''
                else:
                    rot[i] = str(round(r_list[0][i], 3))
                if not all(t[i] == t_list[0][i] for t in t_list):
                    trans[i] = ''
                else:
                    trans[i] = str(round(t_list[0][i], 3))
        sb.check_key_anim()
        sb.view_np_time(culc_time='- Select Culculation Mode -')
    #オブジェクトモードでもコンポーネント選択がある場合は強制的にモード変更する
    selection = cmds.ls(sl=True, type='float3')
    if selection:
        cmds.selectMode(co=True)
        components = cmds.polyListComponentConversion(selection, tv=True)
        s_list, r_list, t_list = get_srt(components, mode='component')
        start = dt.datetime.now()
        if np_flag:
            #print 'culc in numpy'
            s_list = np.reshape(s_list, (len(s_list)/3,3))
            scale = np.average(s_list, axis=0).tolist()
            r_list = np.reshape(r_list, (len(r_list)/3,3))
            rot = np.average(r_list, axis=0).tolist()
            t_list = np.reshape(t_list, (len(t_list)/3,3))
            trans = np.average(t_list, axis=0).tolist()
        else:
            #print 'culc in math'
            srt_list = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            for i in range(0, len(s_list), 3):
                srt_list[0] += s_list[i+0]
                srt_list[1] += s_list[i+1]
                srt_list[2] += s_list[i+2]
            for i in range(0, len(r_list), 3):
                srt_list[3] += r_list[i+0]
                srt_list[4] += r_list[i+1]
                srt_list[5] += r_list[i+2]
            for i in range(0, len(t_list), 3):
                srt_list[6] += t_list[i+0]
                srt_list[7] += t_list[i+1]
                srt_list[8] += t_list[i+2]
            scale = map(lambda a: a/(len(s_list)/3), srt_list[0:3])
            rot = map(lambda a: a/(len(r_list)/3), srt_list[3:6])
            trans = map(lambda a: a/(len(t_list)/3), srt_list[6:9])
        end = dt.datetime.now()
        culc_time = end - start
        sb.view_np_time(culc_time='Culc Time '+str(culc_time))
        scale = map(lambda a: round(a, 3), scale)
        rot = map(lambda a: round(a, 3),  rot)
        trans = map(lambda a: round(a, 3),  trans)
        
    sb.set_pre_transform(trans, rot, scale)
    sb.set_srt_text(scale, rot, trans)
    
def get_srt(selection, mode='object'):
    local_sids = [1, 2, 3, 5]
    s_list = []
    r_list = []
    t_list = []
    sid = sb.space_group.checkedId()
    for sel in selection:
        try:
            parent = cmds.listRelatives(sel, p=True)
            if sid == 0 or sid == 4:
                scale = cmds.xform(sel, q=True, s=True, ws=True)
                rot = cmds.xform(sel, q=True, ro=True, ws=True)
                trans = cmds.xform(sel, q=True, t=True, ws=True)
            else:
                axis_attr_list = ['X', 'Y', 'Z']
                scale = cmds.xform(sel, q=True, s=True, os=True, r=True)
                rot = cmds.xform(sel, q=True, ro=True, os=True)
                if sid in local_sids:#ローカルスペースとビューの時の処理
                    if cmds.selectMode(q=True, o=True):
                        trans = [cmds.getAttr(sel+'.translate'+a)for a in axis_attr_list]
                    else:
                        trans = cmds.xform(sel, q=True, t=True, os=True)
                else:
                    trans = cmds.xform(sel, q=True, t=True, os=True)
                    
            if mode == 'object':
                s_list.append(scale)
                r_list.append(rot)
                t_list.append(trans)
            else:
                s_list += scale
                r_list += rot
                t_list += trans
        except:
            pass
    return s_list, r_list, t_list
    
#センターベイク中かどうかを設定
global bake_mode
bake_mode = False
def set_bake_flag(mode):
    global bake_mode
    bake_mode=mode
    
#センターモードかどうかを設定しておく
global center_mode
center_mode = False
def set_center_flag(mode):
    global center_mode
    center_mode=mode
    
#マッチトランスフォームオブジェクト情報を格納しておく
def set_maching(nodes=None, mode='', pre_sel=None):
    global matching_obj
    global matching_mode
    global matching_pre_sel
    matching_obj = nodes
    matching_mode = mode
    matching_pre_sel = pre_sel
    
def trs_matching():
    global matching_obj
    global matching_mode
    mode = matching_mode
    mached_obj = cmds.ls(sl=True, l=True, type='transform')
    if not mached_obj:
        cmds.select(matching_obj, r=True)
        sb.match_transform(mode=mode)
        return
    else:
        mached_obj = mached_obj[0]
    scl = cmds.xform(mached_obj, q=True, s=True, ws=True)
    rot = cmds.xform(mached_obj, q=True, ro=True, ws=True)
    pos = cmds.xform(mached_obj, q=True, t=True, ws=True)
    for obj in matching_obj:
        if mode == 'scale' or mode == 'all':
            cmds.scale(1.0, 1.0, 1.0, obj, pcp=True)
            ws_scl = cmds.xform(obj, q=True, s=True, ws=True)
            cmds.scale(scl[0]/ws_scl[0], scl[1]/ws_scl[1], scl[2]/ws_scl[2], obj, pcp=True)
        if mode == 'rot' or mode == 'all':
            cmds.rotate(rot[0], rot[1], rot[2], obj, ws=True, pcp=True)
        if mode == 'trans' or mode == 'all':
            cmds.move(pos[0], pos[1], pos[2], obj, ws=True, pcp=True)
        cmds.select(matching_pre_sel, r=True)
        
def pre_pro_reference(sel=None):
    global pre_ref_mode, pre_sel, ctx_mode, pre_obj_list
    if cmds.selectMode(q=True, o=True):
        pre_ref_mode = 'object'
    else:
        if cmds.selectType(q=True, pv=True):
            pre_ref_mode = 'vertex'
        if cmds.selectType(q=True, pe=True):
            pre_ref_mode = 'edge'
        if cmds.selectType(q=True, pf=True):
            pre_ref_mode = 'face'
    pre_sel = sel
    if cmds.selectMode(q=True, co=True):
        cmds.selectMode(o=True)
        pre_obj_list = cmds.ls(sl=True, l=True)
        #print 'comp obj list', pre_obj_list
        cmds.selectMode(co=True)
    #print 'pre_mode :', pre_mode
    #print 'pre_sel :', pre_sel
    return pre_ref_mode
    
def set_reference(mode=''):
    c_ctx = cmds.currentCtx(q=True)
    print c_ctx
    sel = cmds.ls(sl=True, l=True)
    #print 'set reference :', mode, sel
    current_ctx = cmds.currentCtx()
    if mode == 'object':
        #print 'set reference object mode :'
        cmds.selectMode(o=True)
        rot = cmds.xform(sel, q=True, ro=True, ws=True)
        rx = rot[0]/180*math.pi
        ry = rot[1]/180*math.pi
        rz = rot[2]/180*math.pi
        if current_ctx == 'selectSuperContext':
            return
        if current_ctx == 'scaleSuperContext':
            #mel.eval('manipScaleOrient 1;')
            cmds.manipScaleContext('Scale', e=True, orientAxes=(rx, ry, rz))
        if current_ctx == 'RotateSuperContext':
            #mel.eval('manipRotateOrient 1;')
            cmds.manipRotateContext('Rotate', e=True, orientAxes=(rx, ry, rz))
        if current_ctx == 'moveSuperContext':
            #mel.eval('manipMoveOrient 1;')
            cmds.manipMoveContext('Move', e=True, orientAxes=(rx, ry, rz))
    else:
        if mode == 'vertex':
            manip_type = 'PointHandleTowards'
            comp = cmds.polyListComponentConversion(sel, tv=True)
            comp = cmds.filterExpand(comp, sm=31)
            sel_node = '" , "'.join(pre_sel)
            #print 'vertex ref :', sel_node, comp[0]
        if mode == 'edge':
            manip_type = 'AlignHandleWith'
            comp = cmds.polyListComponentConversion(sel, te=True)
            comp = cmds.filterExpand(comp, sm=32)
            sel_node = comp[0]
        if mode == 'face':
            manip_type = 'AlignHandleWith'
            comp = cmds.polyListComponentConversion(sel, tf=True)
            comp = cmds.filterExpand(comp, sm=34)
            sel_node = comp[0]
        if comp:
            if current_ctx == 'selectSuperContext':
                return
            if current_ctx == 'scaleSuperContext':
                mel.eval('manipScaleOrient 5;')
                mel.eval('{  string $Selection1[]; $Selection1[0] = "'+comp[0]+'"; manipScale'+manip_type+'($Selection1[0], {"'+sel_node+'"}, {}, "", 0);;  };')
            if current_ctx == 'RotateSuperContext':
                mel.eval('manipRotateOrient 5;')
                mel.eval('{  string $Selection1[]; $Selection1[0] = "'+comp[0]+'"; manipRotate'+manip_type+'($Selection1[0], {"'+sel_node+'"}, {}, "", 0);;  };')
            if current_ctx == 'moveSuperContext':
                mel.eval('manipMoveOrient 5;')
                mel.eval('{  string $Selection1[]; $Selection1[0] = "'+comp[0]+'"; manipMove'+manip_type+'($Selection1[0], {"'+sel_node+'"}, {}, "", 0);;  };')
        cmds.selectMode(co=True)
        if pre_ref_mode == 'vertex':
            cmds.selectType(pv=1, smu=0, smp=1, pf=0, pe=0, smf=0, sme=0, puv=0)
        if pre_ref_mode == 'edge':
            cmds.selectType(pv=0, smu=0, smp=0, pf=0, pe=1, smf=0, sme=1, puv=0)
        if pre_ref_mode == 'face':
            cmds.selectType(pv=0, smu=0, smp=0, pf=1, pe=0, smf=0, sme=1, puv=0)
        #sel_obj = []
        #obj_list = list(set([vtx.split('.')[0] for vtx in pre_sel]))
        #if obj_list:
            #sel_obj = [cmds.listRelatives(s, p=True)[0] if cmds.nodeType(s)=='mesh' else s for s in obj_list]
            #print obj_list, pre_sel
            #cmds.hilite(obj_list, r=True)
            #cmds.hilite(pre_sel, r=True)
            
    #print 'set to pre mode :', pre_ref_mode
    #print 'set to mode pre :', pre_ref_mode
    if pre_ref_mode == 'object':
        cmds.selectMode(o=True)
    else:
        cmds.selectMode(co=True)
        if pre_obj_list:
            cmds.hilite(pre_obj_list, r=True)
    if pre_sel:
        cmds.select(pre_sel, r=True)
    else:
        cmds.select(cl=True)
    sb.after_pick_context(ctx=c_ctx)
    
    
def volume_scaling(mode):
        #print 'volume_mode :', mode
        undo_scale = cmds.undoInfo(q=True, un=True)
        #print '1st undo info :', undo_scale
        scale_list = map(float, undo_scale.split(' ')[-4:-1])
        scale_com = undo_scale.split(' ')[:-4]
        #print 'scale list :', scale_list
        #print 'scale command :', scale_com
        s1_count = scale_list.count(1.0)
        #print 'scale 1.0 count :', s1_count
        if s1_count == 0:
            return
        if mode == 5:
            scale_num = reduce(lambda a, b : a*b, scale_list)
            #print 'all scale multiply :', scale_num
            if s1_count == 2:
                div_scale = math.sqrt(scale_num)
            elif s1_count == 1:
                div_scale = scale_num
            else:
                return
            #print 'div scale :', div_scale
            for i, s in enumerate(scale_list[:]):
                if s == 1.0:
                    scale_list[i] = s/div_scale
                else:
                    scale_list[i] = 1.0
        if mode == 2:
            for s in scale_list:
                if s != 1.0:
                    soro_scale = s
                    break
            else:
                return
            for i, s in enumerate(scale_list[:]):
                if s == 1.0:
                    scale_list[i] = soro_scale
                else:
                    scale_list[i] = 1.0
        #print 'post scale list :', scale_list
        post_scale_cmd = ' '.join(scale_com+map(str, scale_list))
        #print 'post command :', post_scale_cmd
        mel.eval(post_scale_cmd)
        get_matrix()
            
def out_focus():
    #print '/*/*/*/*/*/run focus job'
    sb.out_focus()
    sb.clear_focus_job()
    
def group_selection():
    #print '*-*-*-**-*-* run group_selection *-*-*-*-*-*-*-*'
    if cmds.selectMode(q=True, o=True):
        sel = cmds.ls(sl=True, l=True)
        all_sets = cmds.ls(type='objectSet')
        select_sets = []
        select_members = []
        #print 'all_set :', all_sets
        for node in all_sets:
            members = cmds.ls(cmds.sets(node, int=node), l=True)
            for s in sel:
                if s in members:
                    select_sets.append(node)
                    select_members += members
        #print 'get select set :', select_sets
        select_sets = list(set(select_sets))
        select_members = list(set(select_members))
        if select_sets:
            cmds.select(select_sets+select_members+sel, r=True, ne=True)
    if cmds.selectMode(q=True, co=True):
        sel_comp = cmds.ls(sl=True, type='float3')
        #print 'sel comp', sel_comp        
        if not sel_comp:
            sel_comp = cmds.ls(sl=True, tr=True)
        #print 'sel comp', sel_comp
        
        if not sel_comp:
            return
        #現在のモードを取っておく
        if cmds.selectType(q=True, pv=True):
            sel_comp = cmds.polyListComponentConversion(sel_comp, tv=True)
            mode = 31
        if cmds.selectType(q=True, pe=True):
            sel_comp = cmds.polyListComponentConversion(sel_comp, te=True)
            mode = 32
        if cmds.selectType(q=True, pf=True):
            sel_comp = cmds.polyListComponentConversion(sel_comp, tf=True)
            mode = 34
        if not sel_comp:
            return
        sel_comp = cmds.filterExpand(sel_comp, sm=mode)
        
        #cmds.selectMode(o=True)
        #object = cmds.ls(sl=True, l=True)
        #all_clusters = cmds.ls(type='clusterHandle')
        all_sets = cmds.ls(set=True)
        sel_sets = []
        sel_members = []
        sel_clusters = []
        #セットの処理
        for set_node in all_sets:
            if 'tweakSet' in set_node:
                continue
            if not cmds.nodeType(set_node) == 'objectSet':
                continue
            members = cmds.sets(set_node, int=set_node)
            members = cmds.filterExpand(members, sm=mode)
            if members is None:
                continue
            #print 'get members :', set_node, members
            for comp in sel_comp:
                if comp in members:
                    #print 'get comp menber :', comp, set_node, members
                    sel_sets.append(set_node)
                    set_hists = cmds.listHistory(set_node)
                    #print set_node, 'get set hist :', set_hists
                    cls_nodes = cmds.ls(set_hists, type='cluster')
                    #print 'get cls :', cls_nodes
                    if cls_nodes:
                        for cls in cls_nodes:
                            cls_hist = cmds.listHistory(cls, lv=1)
                            #print 'cls hist :', cls_hist
                            cls_handle = cmds.ls(cls_hist, type='transform')
                            cls_parent = cmds.listRelatives(cls_hist)
                            #cls_handle = cmds.listRelatives(cls_hist, pa=True)
                            #print 'history :', cls_handle
                            #print 'parent :', cls_parent
                            sel_clusters += cls_handle
                    sel_members+=members
                    break
        #print 'all cls :', all_clusters
        #print 'all sets :', all_sets
        #cmds.selectMode(co=True)
        #print 'sel sets :',sel_sets
        #print 'sel comp :', sel_members
        cmds.select(cl=True)
        cmds.select(sel_sets, sel_members, sel_clusters, ne=True)
        
        
        
        
        