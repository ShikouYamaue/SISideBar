# -*- coding: utf-8 -*- 
#SI Side Bar
from maya import cmds
from maya import mel
import pymel.core as pm
import os
import json
import copy
import re
from . import qt
from . import common
from . import lang
from . import modeling
from . import transform
from . import freeze
from . import sets
from . import setup
import math
import datetime as dt
import random
import copy
import time
#PySide2、PySide両対応
import imp
try:
    imp.find_module('PySide2')
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except ImportError:
    from PySide.QtGui import *
    from PySide.QtCore import *
try:
    import numpy as np
    np_flag = True
    np_exist = True
except:
    np_flag = False
    np_exist = False
    
    
maya_ver = int(cmds.about(v=True)[:4])
maya_api_ver = int(cmds.about(api=True))
print 'Init SI Side Ber : Maya Ver :', maya_ver
print 'Init SI Side Ber : Maya API Ver :', maya_api_ver

if maya_ver <= 2015:
    image_path = os.path.join(os.path.dirname(__file__), 'icon2015/')
else:
    image_path = os.path.join(os.path.dirname(__file__), 'icon/')
#-------------------------------------------------------------
pre_sel_group_but = False
version = ' - SI Side Bar / ver_2.1.8 -'
window_name = 'SiSideBar'
window_width = 183
top_hover = False#トップレベルボタンがホバーするかどうか
top_h = 20#トップレベルボタンの高さ
si_w = 80
maya_w = 77
#フロートウィンドウのオフセット量をまとめて管理
#dy, fy, px, mx
if maya_ver >= 2017:
    transform_offset = [-40, -40, 385, -180]
elif  maya_ver >= 2016:
    transform_offset = [-40, -40, 340, -180]
else:
    transform_offset = [-40, -40, 355, -180]
if maya_ver >= 2016:
    prop_offset = [-55, -55, 315, -175]
    sym_offset = [-55, -55, 300, -175]
else:
    prop_offset = [-55, -55, 315, -180]
    sym_offset = [-55, -55, 320, -180]
filter_offset = [-100, -100, 215, -180]
global uni_vol_dict
#Uni/Volボタン仕様変更のため
uni_vol_dict = {'Uni/Vol':-1, 'Uni':2, 'Vol':5,  'Normal':-1, 'View':-1}
destroy_flag =False
destroy_name = 'Destroy'
evolution_flag = False
cp_abs_flag = False
ommit_manip_link = False
#-------------------------------------------------------------

#フラットボタンを作って返す
global all_flat_buttons
all_flat_buttons = []
global all_flat_button_palams
all_flat_button_palams = []
def make_flat_btton(icon=None, name='', text=95, bg=200, checkable=True, w_max=None, w_min=None, 
                                h_max=22, h_min=20, policy=None, icon_size=None, tip=None, flat=True, hover=True):
    global all_flat_buttons
    global all_flat_button_palams
    button = RightClickButton()
    button.setText(name)
    if checkable:
        button.setCheckable(True)#チェックボタンに
    if icon:
        button.setIcon(QIcon(icon))
    if flat:
        button.setFlat(True)#ボタンをフラットに
        qt.change_button_color(button, textColor=text, bgColor=ui_color, hiColor=bg, mode='button', hover=hover, destroy=destroy_flag, dsColor=border_col)
        button.toggled.connect(lambda : qt.change_button_color(button, textColor=text, bgColor=ui_color, hiColor=bg, mode='button', toggle=True, hover=hover, destroy=destroy_flag, dsColor=border_col))
    else:
        button.setFlat(False)
        qt.change_button_color(button, textColor=text, bgColor=bg, hiColor=push_col, mode='button', hover=hover, destroy=destroy_flag, dsColor=border_col)
    if w_max:
        button.setMaximumWidth(w_max)
    if w_min:
        button.setMinimumWidth(w_min)
    if h_max:
        button.setMaximumHeight(h_max)
    if h_min:
        button.setMinimumHeight(h_min)
    if icon_size:
        button.setIconSize(QSize(*icon_size))
    if policy:#拡大縮小するようにポリシー設定
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
    if tip:
        button.setToolTip(tip)
    all_flat_buttons.append(button)
    if flat:
        all_flat_button_palams.append([text, ui_color, bg, 'button', hover, destroy_flag, border_col])
    else:
        all_flat_button_palams.append([text, bg, push_col, 'button', hover, destroy_flag, border_col])
    return button
    
#右クリックボタンクラスの作成
class RightClickButton(QPushButton):
    rightClicked = Signal()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.rightClicked.emit()
        else:
            super(RightClickButton, self).mouseReleaseEvent(e)
class RightClickToolButton(QToolButton):
    rightClicked = Signal()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.rightClicked.emit()
        else:
            super(RightClickToolButton, self).mouseReleaseEvent(e)
            
#セーブファイルを読み込んで返す　   
def read_save_file(init_pos=False):
    #セーブデータが無いかエラーした場合はデフォファイルを作成
    def_data = {}
    def_data['display'] = False#起動時に表示するかどうか
    def_data['dockable'] = True
    def_data['floating'] = True
    def_data['area'] = None
    def_data['pw'] = 200
    def_data['ph'] = 200
    def_data['sw'] = 170
    def_data['sh'] = 800
    def_data['ui_col'] = 0
    def_data['vol_obj'] = -1
    def_data['vol_cmp'] = -1
    def_data['destroy'] = False
    if init_pos:
        print 'SI Side Bar : Init Window Position'
        return def_data
    #読み込み処理
    temp = __name__.split('.')
    dir_path = os.path.join(
        os.getenv('MAYA_APP_dir'),
        'Scripting_Files')
    w_file = dir_path+'/'+temp[-1]+'_window_'+str(maya_ver)+'.json'
    if os.path.exists(w_file):#保存ファイルが存在したら
        try:
            with open(w_file, 'r') as f:
                save_data = json.load(f)
        except Exception as e:
            save_data = def_data
    else:
        save_data = def_data
    return save_data

global trs_window_flag
trs_window_flag = False
#フローティングメニュー作成
class FloatingWindow(qt.SubWindow):
    def __init__(self, parent = None, menus=[], offset=None):
        global trs_window_flag 
        trs_window_flag = True
        super(FloatingWindow, self).__init__(parent)
        self.wrapper = QWidget()
        self.setCentralWidget(self.wrapper)
        #self.mainLayout = QHBoxLayout()
        self.menus = menus
        self.f_layout = QVBoxLayout()
        self.wrapper.setLayout(self.f_layout)
        self.f_layout.addWidget(self.menus)
        qt.change_button_color(self, textColor=menu_text, bgColor=menu_bg, hiText=menu_high_text, hiBg=menu_high_bg, mode='window')
        self.show()#Showしてから移動しないとほしい位置が取れない
        move_to_best_pos(object=self, offset=offset)
    def re_init_window(self, mode='transform_top'):
        #桁数の変更があったらUIを丸ごと描画しなおす
        #UIのテキスト再描画のみができなかったので苦肉の策
        if not trs_window_flag:
            #print 'reinit flag false'
            return
        if mode == 'transform_top':
            self.f_layout.removeWidget(self.menus)
            self.wrapper = QWidget()
            self.setCentralWidget(self.wrapper)
            self.f_layout = QVBoxLayout()
            self.wrapper.setLayout(self.f_layout)
            self.menus = window.create_trans_menu(add_float=False)
            self.f_layout.addWidget(self.menus)
            self.show()
    def closeEvent(self, e):
        global trs_window_flag 
        #print 'window close', e
        trs_window_flag = False
            #print 're_init'
        del self
        
#フローティングで出した窓をベストな位置に移動する
def move_to_best_pos(object=None, offset=None):
        w_size = object.size()
        dy = offset[0]
        fy = offset[1]
        #右移動の場合はウィンドウサイズから算出
        px = w_size.width()+15
        mx = offset[3]
        #print w_size
        #デフォルト出現位置とカーソル位置から最適な位置を算出して移動
        dock_dtrl = window.parent()
        if maya_ver >= 2015:
            win_pos = dock_dtrl.mapToGlobal(QPoint(0, 0))
        else:
            win_pos = window.pos()
            
        cur_pos = QCursor.pos()
        if maya_ver >= 2017:
            float_flag = cmds.workspaceControl(u'SiSideBarWorkspaceControl',q=True, fl=True)
        else:
            if maya_ver >= 2015:
                float_flag = window.isFloating()
            else:
                float_flag = True
            
        cur_y = cur_pos.y()
        if float_flag:
            cur_y += fy
        else:
            cur_y += dy
        def_pos = object.pos()
        def_x = def_pos.x()
        win_x = win_pos.x()
        sub_x = win_x - def_x
        if sub_x > 0:
            move_x = def_x+sub_x-px
        else:
            move_x = def_x+sub_x-mx
        #print move_x, cur_y
        object.move(move_x, cur_y)

#2016以下は通常起動
class Option():
    def __init__(self, init_pos=False):
        #print 'init in Option'
        #循環参照回避のため関数内で呼び出し
        global sisidebar_sub
        from . import sisidebar_sub as sisidebar_sub
        #開いてたら一旦閉じる
        try:
            try:
                window.dockCloseEventTriggered()
            except:
                pass
            window.close()
        except:
            pass
        global window
        window = SiSideBarWeight(init_pos=init_pos)
        save_data = window.load(init_pos=init_pos)
        if save_data['floating'] is False and save_data['area'] is not None:
            window.show(
                dockable=True,
                area=save_data['area'],
                floating=save_data['floating'],
                width=save_data['sw'],
                height=save_data['sh']
            )
        else:
            if maya_ver >= 2015:
                window.show(dockable=True)
            else:
                window.show()
                
        #アクティブウィンドウにする
        window.activateWindow()
        window.raise_()

    
global script_job
#script_job = None#二個目を許可するときは一時的に開放すべし
class SiSideBarWeight(qt.DockWindow):
    def __init__(self, parent = None, init_pos=False):
        super(SiSideBarWeight, self).__init__(parent)
        global sisidebar_sub
        from . import sisidebar_sub as sisidebar_sub
        #ウィンドウサイズのポリシー、.fixedにすると固定される
        #print '/*/*/**/*/*/*/*/*/*/* init_SiSideBar /*/*/*/*/*/*/*/*/'
        load_transform_setting()#トランスフォーム設定桁数設定を読み込んでおく
        self.display = True#ウィンドウスタートアップフラグを立てる
        self.get_init_space()
        self.init_save()
        self.load(init_pos=init_pos)
        self.get_pre_about()
        self.setAcceptDrops(True)#ドラッグドロップを許可
        
        self.reload.connect(self.reload_srt)
        #アプリケーション終了時に実行する関数をQtGui.qAppにコネクトしておく
        qApp.aboutToQuit.connect(lambda : self.save(display=self.display))
        
        
        self.setMinimumHeight(1)#ウィンドウの最小サイズ
        self.setMinimumWidth(window_width)#ウィンドウの最小サイズ
        self.setMaximumWidth(window_width)#ウィンドウの最大サイズ
        self.setObjectName(window_name)
        self.setWindowTitle(window_name)
        self.setWindowTitle(window_name)
        self._initUI()
        self.chane_context_space()
        self.attribute_lock_state(mode=3, check_only=True)
        self.set_up_manip()
        
        
    def dropEvent(self,event):
        #ドラッグされたオブジェクトの、ドロップ許可がおりた場合の処理
        setup.open_scene(mime_data=event.mimeData())
        
    def dragEnterEvent(self,event):
        #ドラッグされたオブジェクトを許可するかどうかを決める
        #ドラッグされたオブジェクトが、ファイルなら許可する
        mime = event.mimeData()
        
        if mime.hasUrls() == True:
            event.accept()
        else:
            event.ignore()
        
    #起動時のスペースを取得して反映
    def get_init_space(self):
        global pre_context_space
        pre_context_space = cmds.currentCtx()
        ini_scale_mode = cmds.manipScaleContext('Scale', q=True, mode=True)
        ini_rot_mode = cmds.manipRotateContext('Rotate', q=True, mode=True)
        ini_trans_mode = cmds.manipMoveContext('Move', q=True, mode=True)
        '''
        print ini_scale_mode
        print ini_rot_mode
        print ini_trans_mode
        '''
        scale_obj_list = [3, 1, 0, 1, 1, 1, 1, None, None, 5, 5]
        scale_cmp_list = [3, 1, 0, 1, 1, 1, 4, None, None, 5, 5]
        rot_list = [1, 0, 3, 4, None, None, None, None, None, 5, 5]
        trans_list = [3, 1, 0, 2, 1, 1, 4, None, None, 5, 5]
        
        self.scl_obj_space = scale_obj_list[ini_scale_mode]
        self.scl_cmp_space = scale_cmp_list[ini_scale_mode]
        self.rot_space = rot_list[ini_rot_mode] 
        self.trans_space = trans_list[ini_trans_mode]
        
        
    #スペース設定を変更したらMayaのコンテキストにも反映する
    def chane_context_space(self):
        if select_scale.isChecked():
            if cmds.selectMode(q=True, o=True):
                if maya_ver >= 2018:
                    context_id = [2, 1, 1, 0, 6, 10]
                else:
                    context_id = [2, 1, 1, 0, 6, 9]
            if cmds.selectMode(q=True, co=True):
                if maya_ver >= 2018:
                    context_id = [2, 1, 1, 0, 6, 10]
                else:
                    context_id = [2, 1, 1, 0, 6, 9]
            id = context_id[space_group.checkedId()]
            cmds.manipScaleContext('Scale', e=True, mode=id)
        if select_rot.isChecked():
            if maya_ver >= 2018:
                context_id = [1, 0, 0, 2, 3, 10]
            else:
                context_id = [1, 0, 0, 2, 3, 9]
                
            id = context_id[space_group.checkedId()]
            cmds.manipRotateContext('Rotate', e=True, mode=id)
        if select_trans.isChecked():
            #2018からコンポーネントモードが10番になったようなので差し替え
            if maya_ver >= 2018:
                context_id = [2, 1, 3, 0, 6, 10]
            else:
                context_id = [2, 1, 3, 0, 6, 9]
            id = context_id[space_group.checkedId()]
            cmds.manipMoveContext('Move', e=True, mode=id)
            
    #起動時にMayaの選択コンテキストからUIのSRT選択状態を設定する
    def select_from_current_context(self):
        current_tool = cmds.currentCtx()
        tools_list = ['scaleSuperContext', 'RotateSuperContext', 'moveSuperContext', 'selectSuperContext']
        try:
            mode = tools_list.index(current_tool)
        except:
            mode = 3
            #return
        #COGの有効無効を切り替え
        if mode == 3:
            #self.cog_but.setDisabled(True)
            #qt.change_button_color(self.cog_but, textColor=120, bgColor=ui_color, mode='button')
            return
        self.all_srt_but_list[mode][3].setChecked(True)
        for i, srt_list in enumerate(self.all_srt_but_list):
            if i != mode:
                for but in srt_list:
                    but.setChecked(False)
        self.load_pre_selection(mode, select_ctx=False)
        set_active_mute(mode=mode)
        select_but.setChecked(False)
            
        #ホットキーからのマニプ変更時にハンドル選択を反映する
        self.select_manip_handle(mode=mode)
        
    #オンオフアイコンを切り替える
    def toggle_xyz_icon(self, but=None, axis=0):
        icon_list = [[self.x_on, self.x_off], [self.y_on, self.y_off], [self.z_on, self.z_off]]
        if but.isChecked():
            but.setIcon(QIcon(image_path+icon_list[axis][0]))
        else:
            but.setIcon(QIcon(image_path+icon_list[axis][1]))
            
    #マニピュレータの選択状態が変更されたらサイドバーへも反映する
    def select_xyz_from_manip(self, handle_id=0, keep=True):
        current_tool = cmds.currentCtx()
        tools_list = ['scaleSuperContext', 'RotateSuperContext', 'moveSuperContext']
        try:
            mode = tools_list.index(current_tool)
        except:
            return
        #print 'change manip handle from maya', mode
        scl_move_active_list = [[True, False, False],
                                    [False, True, False],
                                    [False, False, True],
                                    [True, True, True],
                                    [True, True, False],
                                    [False, True, True],
                                    [True, False, True]]
        rot_active_list = [[True, False, False],
                                    [False, True, False],
                                    [False, False, True],
                                    [True, True, True],
                                    [True, True, True]]
        if mode == 0:
            if maya_ver >= 2015:
                handle_id = cmds.manipScaleContext('Scale', q=True, cah=True)
            active_list = scl_move_active_list
        if mode == 1:
            if maya_ver >= 2015:
                handle_id = cmds.manipRotateContext('Rotate', q=True, cah=True)
            active_list = rot_active_list
        if mode == 2:
            if maya_ver >= 2015:
                handle_id = cmds.manipMoveContext('Move', q=True, cah=True)
            active_list = scl_move_active_list
        #print 'handle id :', handle_id
        for i, but in enumerate(self.all_axis_but_list[mode][0:3]):
            if ommit_manip_link:
                continue
            #print i, mode, handle_id
            #print 'check xyz but active :', active_list[handle_id][i]
            but.setChecked(active_list[handle_id][i])
        if keep:
            self.keep_srt_select(mode=mode)
            
    #マニピュレータコンテキストを初期化
    def set_up_manip(self):
        #print 'set_up_manip'
        if cmds.selectMode(q=True, o=True):
            sel  = cmds.ls(sl=True, l=True, type = 'transform')
            if sel:
                type = cmds.nodeType(sel[0])
            else:
                type = 'transform'
                #print 'edit manip cod : object'
            #print type
            if maya_ver >=2015:
                scale_manip = cmds.manipScaleContext('Scale', e=True,
                                                                            prd=(lambda : set_child_comp(mode=True), type),#ドラッグ前に実行
                                                                            pod=(self.editing_manip, type),#ドラッグ後に実行
                                                                            prc=(self.select_from_current_context))#ツールを開始したときに実行
                rot_manip = cmds.manipRotateContext('Rotate', e=True, 
                                                                            prd=(lambda : set_child_comp(mode=True), type),#ドラッグ前に実行
                                                                            pod=(self.editing_manip, type),#ドラッグ後に実行
                                                                            prc=(self.select_from_current_context))#ツールを開始したときに実行
                move_manip = cmds.manipMoveContext('Move', e=True, 
                                                                            prd=(lambda : set_child_comp(mode=True), type),#ドラッグ前に実行
                                                                            pod=(self.editing_manip, type),#ドラッグ後に実行
                                                                            prc=(self.select_from_current_context))#ツールを開始したときに実行
            else:
                scale_manip = cmds.manipScaleContext('Scale', e=True,
                                                                            prd=(lambda : set_child_comp(mode=True), type),#ドラッグ前に実行
                                                                            pod=(self.editing_manip, type))#ドラッグ後に実行
                rot_manip = cmds.manipRotateContext('Rotate', e=True, 
                                                                            prd=(lambda : set_child_comp(mode=True), type),#ドラッグ前に実行
                                                                            pod=(self.editing_manip, type))#ドラッグ後に実行
                move_manip = cmds.manipMoveContext('Move', e=True, 
                                                                            prd=(lambda : set_child_comp(mode=True), type),#ドラッグ前に実行
                                                                            pod=(self.editing_manip, type))#ドラッグ後に実行
        if cmds.selectMode(q=True, co=True):
            sel  = cmds.ls(sl=True, l=True)
            if sel:
                #複数のコンポーネントタイプに対応Podはリストの最後のタイプでないとだめみたい
                type = cmds.nodeType(sel[-1])
            else:
                type = 'mesh'
            if maya_ver >=2015:
                scale_manip = cmds.manipScaleContext('Scale', e=True, 
                                                                                pod=(self.editing_manip, type),
                                                                                prc=(self.select_from_current_context))
                rot_manip = cmds.manipRotateContext('Rotate', e=True, 
                                                                                pod=(self.editing_manip, type),
                                                                                prc=(self.select_from_current_context))
                move_manip = cmds.manipMoveContext('Move', e=True, 
                                                                                pod=(self.editing_manip, type),
                                                                                prc=(self.select_from_current_context))
            else:
                scale_manip = cmds.manipScaleContext('Scale', e=True, 
                                                                                pod=(self.editing_manip, type))
                rot_manip = cmds.manipRotateContext('Rotate', e=True, 
                                                                                pod=(self.editing_manip, type))
                move_manip = cmds.manipMoveContext('Move', e=True, 
                                                                                pod=(self.editing_manip, type))
    #直接podから実行すると落ちるのでシグナル経由で更新関数実行
    def reload_srt(self):
        sisidebar_sub.get_matrix()
    
    #メッシュ編集後に値を反映するシグナル
    reload = Signal()
    #スロット,postDragCommand(pod)と接続
    def editing_manip(self):
        #print 'editing manip'
        if uni_vol_dict[view_but.text()] != -1 and select_scale.isChecked():
            #print 'volmode'
            mode = uni_vol_dict[view_but.text()]
            #print mode
            sisidebar_sub.set_vol_mode(mode)
            self.pre_vol_id = uni_vol_dict[view_but.text()]
            #sisidebar_sub.volume_scaling(mode)
            vol_job = cmds.scriptJob(ro=True, e=("idle", sisidebar_sub.volume_scaling), protected=True)
        if maya_ver >= 2015:
            self.select_xyz_from_manip()
        else:
            #2014以前はアンドゥインフォから強引に軸を取得する
            handle_job = cmds.scriptJob(ro=True, e=("idle", sisidebar_sub.current_handle_getter), protected=True)
        self.reload.emit()
        #
        if ommit_manip_link:
            current_tool = cmds.currentCtx()
            tools_list = ['scaleSuperContext', 'RotateSuperContext', 'moveSuperContext']
            try:
                #print 'Froce select handle'
                mode = tools_list.index(current_tool)
                self.select_manip_handle(mode=mode)
            except Exception as e:
                print e.message
                pass
        #センター一致を実行する→culcのget_matrix時に実行するように変更
        
    def init_save(self):
        temp = __name__.split('.')
        self.dir_path = os.path.join(
            os.getenv('MAYA_APP_dir'),
            'Scripting_Files')
        self.w_file = self.dir_path+'/'+temp[-1]+'_window_'+str(maya_ver)+'.json'
        
    def load(self, init_pos=False):
        #print 'load data'
        save_data = read_save_file(init_pos=init_pos)
        if maya_ver >= 2015:
            offset_w = -8
            offset_h = -31
        else:
            offset_w = 0
            offset_h = 0
        self.pw = save_data['pw'] + offset_w#誤差補正
        self.ph = save_data['ph'] + offset_h#誤差補正
        self.sw = save_data['sw']
        self.sh = save_data['sh']
        self.move(self.pw, self.ph)
        self.resize(self.sw, self.sh)
        self.dockable=True,
        self.area=save_data['area'],
        self.floating=save_data['floating'],
        self.width=save_data['sw'],
        self.height=save_data['sh']
        try:
            self.ui_col = save_data['ui_col']
        except:
            self.ui_col = 0
        try:
            self.uni_obj_mode = save_data['vol_obj']
            self.uni_cmp_mode = save_data['vol_cmp']
        except:
            self.uni_obj_mode = -1
            self.uni_cmp_mode = -1
        global destroy_flag
        try:
            destroy_flag = save_data['destroy']
        except:
            destroy_flag = False
        global evolution_flag
        try:
            evolution_flag = save_data['evolution']
            if evolution_flag:
                global destroy_name
                destroy_name = 'Evolution'
        except:
            evolution_flag = False
        #print destroy_flag
        
        return save_data
        
    def save(self, display=True):
        #print 'save'
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        save_data = {}
        
        save_data['display'] = display
        if maya_ver >= 2015:
            save_data['dockable'] = self.isDockable()
        else:
            save_data['dockable'] = False
        global maya_ver
        if maya_ver >= 2017:
            save_data['floating'] = cmds.workspaceControl(u'SiSideBarWorkspaceControl',q=True, fl=True)
        elif maya_ver >= 2015:
            save_data['floating'] = self.isFloating()
        else:
            save_data['floating'] = True
            
        if maya_ver >= 2015:
            save_data['area'] = self.dockArea()
        else:
            save_data['area'] = None
        #print 'dock area', self.dockArea()
        if save_data['dockable'] is True:
            dock_dtrl = self.parent()
            pos = dock_dtrl.mapToGlobal(QPoint(0, 0))
        else:
            pos = self.pos()
        size = self.size()
        save_data['pw'] = pos.x()
        save_data['ph'] = pos.y()
        save_data['sw'] = size.width()
        save_data['sh'] = size.height()
        #print 'save ui col :', self.ui_col
        save_data['ui_col'] = self.ui_col
        save_data['vol_obj'] = self.uni_obj_mode
        save_data['vol_cmp'] = self.uni_cmp_mode
        #print 'save data :', save_data
        global destroy_flag
        save_data['destroy'] = destroy_flag
        global evolution_flag
        save_data['evolution'] = evolution_flag
        #print destroy_flag
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        with open(self.w_file, 'w') as f:
            json.dump(save_data, f)
        return save_data
        
    #ウィンドウ閉じた時にジョブ削除ドックイベントはトリガーが通常と異なるので注意
    global center_mode
    center_mode = None
    def dockCloseEventTriggered(self):
        print 'SI Side Bar : Close Event : Dock Window Closed'
        self.remove_job()
        self.display = False#ウィンドウスタートアップフラグを下げる
        self.save(display=False)
        #センターモードに入っていたら解除する
        if center_mode:
            toggle_center_mode(mode=False)
        #COGモードなら解除する
        if self.cog_but.isChecked():
            self.cog_but.setChecked(False)
            self.setup_object_center()
        option_window_list = ['prop_option', 'filter_window', 'sym_window', 'trs_setting_window', 'transform_manu_window']
        for op_window in option_window_list:
            try:
                exec(op_window+'.close()')
                exec('del '+op_window)
            except:
                pass
        if destroy_flag:
            print 'timer stop'
            self.timer.stop()
            
    #タブ隠すだけで無効になるので使用中止
    #def hideEvent(self, e):
        #if maya_ver >= 2017:
            #self.dockCloseEventTriggered()
        
    #Maya2014用
    def closeEvent(self, e):
        if maya_ver <= 2014:
            self.dockCloseEventTriggered()
                
    #スクリプトジョブ作成
    def create_job(self):
        global script_job
        global context_job
        global timeline_job
        global undo_job
        global redo_job
        global workspace_job
        if 'script_job' in globals():
            if script_job:
                return
        script_job = cmds.scriptJob(cu=True, e=("SelectionChanged", sisidebar_sub.change_selection))
        timeline_job = cmds.scriptJob(cu=True, e=("timeChanged", sisidebar_sub.change_selection))
        undo_job = cmds.scriptJob(cu=True, e=("Undo", sisidebar_sub.change_selection))
        redo_job = cmds.scriptJob(cu=True, e=("Redo", sisidebar_sub.change_selection))
        context_job = cmds.scriptJob(cu=True, e=("ToolChanged", sisidebar_sub.change_context))
        workspace_job = cmds.scriptJob(e=("SceneOpened", setup.check_open), kws=False)
        #print 'check job for create :', script_job
        
    #スクリプトジョブ削除
    def remove_job(self):
        global script_job
        global context_job
        global timeline_job
        global undo_job
        global redo_job
        global workspace_job
        if script_job is not None:
            cmds.scriptJob(k=script_job)
            cmds.scriptJob(k=timeline_job)
            cmds.scriptJob(k=context_job)
            cmds.scriptJob(k=redo_job)
            cmds.scriptJob(k=undo_job)
            cmds.scriptJob(k=workspace_job)
            script_job = None
    pre_vol_id = -1
    pre_obj_vol = -1
    pre_cmp_vol = -1
    
    #以前の設定からUni/Volボタン状態を復旧する
    def rebuild_uni_vol(self, mode):
        #print 'rebuild_uni_vol', mode
        if mode == 2:
            view_but.setText('Uni')
            view_but.setChecked(True)
        elif mode == 5:
            #print 'Vol'
            view_but.setText('Vol')
            view_but.setChecked(True)
        else:
            view_but.setText('Uni/Vol')
            view_but.setChecked(False)
            self.unselect_vol_but()
        #self.rebuild_uni_vol(mode=self.uni_obj_mode)
        #self.rebuild_uni_vol(mode=self.uni_cmp_mode)
        
    
    def toggle_uni_vol(self, num):
        if view_but.text() == ('Uni/Vol'):
            view_but.setText('Uni')
            view_but.setChecked(True)
        elif view_but.text() == ('Uni'):
            view_but.setText('Vol')
            view_but.setChecked(True)
        else:
            view_but.setText('Uni/Vol')
            view_but.setChecked(False)
            self.unselect_vol_but()
        #モード保存を一元化するためにボタン押されたタイミングで保存
        if cmds.selectMode(q=True, o=True):
            self.uni_obj_mode = uni_vol_dict[view_but.text()]
            #print self.uni_obj_mode
        if cmds.selectMode(q=True, co=True):
            self.uni_cmp_mode = uni_vol_dict[view_but.text()]
            #print self.uni_cmp_mode
    
    #選択解除のためにボタンを差し替える
    def unselect_vol_but(self):
        #print 'unselect uni vol but :'
        #return
        scl_vol_group.removeButton(view_but)
        #scl_vol_group.removeButton(plane_but)
        view_but.setChecked(False)
        #plane_but.setChecked(False)
        scl_vol_group.addButton(view_but, 2)
        #scl_vol_group.addButton(plane_but, 5)
    
    #以前の選択状態を保存しておく
    keep_srt_select_list = []
    def keep_srt_select(self, mode=0):
        #print 'keep pre srt selection :', mode
        if mode == 3:
            if select_scale.isChecked():
                mode = 0
            elif select_rot.isChecked():
                mode = 1
            elif select_trans.isChecked():
                mode = 2
            else:
                self.select_space = space_group.checkedId()
        if mode == 0:
            if any([self.but_scale_x.isChecked(), self.but_scale_y.isChecked(), self.but_scale_z.isChecked(), self.but_scale_all.isChecked()]):
                #print 'seve any value', self.sel_sx, self.sel_sy, self.sel_sz, self.sel_s_all
                self.sel_sx = self.but_scale_x.isChecked()
                self.sel_sy = self.but_scale_y.isChecked()
                self.sel_sz = self.but_scale_z.isChecked()
                self.sel_s_all = self.but_scale_all.isChecked()
                #print 'keep_pre_select_value :', self.sel_sx, self.sel_sy, self.sel_sz, self.sel_s_all
                if cmds.selectMode(q=True, o=True):
                    #print 'load scl object space'
                    self.scl_obj_space = space_group.checkedId()
                    #self.uni_obj_mode = scl_vol_group.checkedId()
                    #print 'save uni_obj_mode :', self.uni_obj_mode
                    #print 'get space id :', self.scl_obj_space
                if cmds.selectMode(q=True, co=True):
                    #print 'load scl component space'
                    self.scl_cmp_space = space_group.checkedId()
                    #self.uni_cmp_mode = scl_vol_group.checkedId()
                    #print 'save uni_cmp_mode :', self.uni_obj_mode
                    #print 'get space id :', self.scl_cmp_space
            #print self.sel_sx, self.sel_sy, self.sel_sz, self.sel_s_all, self.scl_obj_space
        if mode == 1:
            if any([self.but_rot_x.isChecked(), self.but_rot_y.isChecked(), self.but_rot_z.isChecked(), self.but_rot_all.isChecked()]):
                self.sel_rx = self.but_rot_x.isChecked()
                self.sel_ry = self.but_rot_y.isChecked()
                self.sel_rz = self.but_rot_z.isChecked()
                self.sel_r_all = self.but_rot_all.isChecked()
                self.rot_space = space_group.checkedId()
                #print 'get space id :', self.rot_space 
        if mode == 2:
            if any([self.but_trans_x.isChecked(), self.but_trans_y.isChecked(), self.but_trans_z.isChecked(), self.but_rot_all.isChecked()]):
                self.sel_tx = self.but_trans_x.isChecked()
                self.sel_ty = self.but_trans_y.isChecked()
                self.sel_tz = self.but_trans_z.isChecked()
                self.sel_t_all = self.but_trans_all.isChecked()
                self.trans_space = space_group.checkedId()
                #print 'get space id :', self.trans_space
                
    #以前の状態の復元
    uni_obj_mode = -1
    uni_cmp_mode = -1
    sel_sx = True
    sel_sy = True
    sel_sz = True
    sel_s_all = True
    sel_rx = True
    sel_ry = True
    sel_rz = True
    sel_r_all = True
    sel_tx = True
    sel_ty = True
    sel_tz = True
    sel_t_all = True
    def load_pre_selection(self, mode, select_ctx=True):
        #print 'init load mode', mode, select_ctx
        #print 'uni obj mode', self.uni_obj_mode, self.uni_cmp_mode
        if 'window' in globals():
            window.change_button_group()#Uni_Volモードのグループ分けを実行
        #print '*+*+*+load pre selection+*+*+*+*'
        #何も選択されていない場合は抜ける
        if not select_scale.isChecked() and not select_rot.isChecked() and not select_trans.isChecked():
            #mel.eval('dR_selectPress;')
            #mel.eval('dR_selectRelease;')
            cmds.setToolTo('selectSuperContext')
            return
        #print 'load pre srt selection :', mode
        #print self.sel_sx, self.sel_sy, self.sel_sz, self.sel_s_all, self.scl_obj_space
        try:
            if mode == 0:
                if select_ctx:
                    cmds.setToolTo('scaleSuperContext')
                try:
                    xyz_list = [self.sel_sx, self.sel_sy, self.sel_sz]
                    if any(xyz_list):
                        self.but_scale_x.setChecked(self.sel_sx)
                        self.but_scale_y.setChecked(self.sel_sy)
                        self.but_scale_z.setChecked(self.sel_sz)
                        self.but_scale_all.setChecked(self.sel_s_all)
                        if cmds.selectMode(q=True, o=True):
                            if self.scl_obj_space == 0:
                                self.scl_obj_space = 1
                            #print 'pre scl object space :', self.scl_cmp_space
                            space_group.button(self.scl_obj_space).setChecked(True)
                            if self.uni_obj_mode != -1:
                                self.rebuild_uni_vol(mode=self.uni_obj_mode)
                                #if not scl_vol_group.button(self.uni_obj_mode).isChecked():
                                    #scl_vol_group.button(self.uni_obj_mode).setChecked(True)
                            else:
                                self.unselect_vol_but()
                                pass
                        if cmds.selectMode(q=True, co=True):
                            #print 'pre scl component space :', self.scl_cmp_space
                            space_group.button(self.scl_cmp_space).setChecked(True)
                            if self.uni_cmp_mode != -1:
                                self.rebuild_uni_vol(mode=self.uni_obj_mode)
                                #if not scl_vol_group.button(self.uni_cmp_mode).isChecked():
                                    #scl_vol_group.button(self.uni_cmp_mode).setChecked(True)
                            else:
                                self.unselect_vol_but()
                                pass
                        return
                except Exception as e:
                    print 'load pre selection scale error'
                    print e.message
                    pass
                self.but_scale_x.setChecked(True)
                self.but_scale_y.setChecked(True)
                self.but_scale_z.setChecked(True)
                self.but_scale_all.setChecked(True)
                if cmds.selectMode(q=True, o=True):
                    #print 'pre scl object space :', self.scl_cmp_space
                    try:
                        space_group.button(self.scl_obj_space).setChecked(True)
                    except Exception as e:#たまにエラー吐くので例外処理
                        print e.message
                        space_group.button(3).setChecked(True)
                    if self.uni_obj_mode != -1:
                        self.rebuild_uni_vol(mode=self.uni_obj_mode)
                        #if not scl_vol_group.button(self.uni_obj_mode).isChecked():
                            #scl_vol_group.button(self.uni_obj_mode).setChecked(True)
                    else:
                        self.unselect_vol_but()
                        pass
                if cmds.selectMode(q=True, co=True):
                    #print 'pre scl component space :', self.scl_cmp_space
                    space_group.button(self.scl_cmp_space).setChecked(True)
                    if self.uni_cmp_mode != -1:
                        self.rebuild_uni_vol(mode=self.uni_cmp_mode)
                        #if not scl_vol_group.button(self.uni_cmp_mode).isChecked():
                            #scl_vol_group.button(self.uni_cmp_mode).setChecked(True)
                    else:
                        self.unselect_vol_but()
                        pass
            if mode == 1:
                if select_ctx:
                    cmds.setToolTo('RotateSuperContext')
                try:
                    xyz_list = [self.sel_rx, self.sel_ry, self.sel_rz]
                    if any(xyz_list):
                        self.but_rot_x.setChecked(self.sel_rx)
                        self.but_rot_y.setChecked(self.sel_ry)
                        self.but_rot_z.setChecked(self.sel_rz)
                        self.but_rot_all.setChecked(self.sel_r_all)
                        space_group.button(self.rot_space).setChecked(True)
                        return
                except Exception as e:
                    print 'load pre selection rot error'
                    print e.message
                    pass
                self.but_rot_x.setChecked(True)
                self.but_rot_y.setChecked(True)
                self.but_rot_z.setChecked(True)
                self.but_rot_all.setChecked(True)
                space_group.button(1).setChecked(True)
                space_group.button(self.rot_space).setChecked(True)
            if mode == 2:
                if select_ctx:
                    cmds.setToolTo('moveSuperContext')
                try:
                    xyz_list = [self.sel_tx, self.sel_ty, self.sel_tz]
                    if any(xyz_list):
                        self.but_trans_x.setChecked(self.sel_tx)
                        self.but_trans_y.setChecked(self.sel_ty)
                        self.but_trans_z.setChecked(self.sel_tz)
                        self.but_trans_all.setChecked(self.sel_t_all)
                        space_group.button(self.trans_space).setChecked(True)
                        return
                except Exception as e:
                    print 'load pre selection trans error'
                    print e.message
                    pass
                self.but_trans_x.setChecked(True)
                self.but_trans_y.setChecked(True)
                self.but_trans_z.setChecked(True)
                self.but_trans_all.setChecked(True)
                space_group.button(self.trans_space).setChecked(True)
            if mode == 3:
                if select_scale.isChecked():
                    if cmds.selectMode(q=True, o=True):
                        if self.scl_obj_space == 0:
                            self.scl_obj_space = 1
                        #print 'pre scl object space :', self.scl_cmp_space
                        space_group.button(self.scl_obj_space).setChecked(True)
                        self.rebuild_uni_vol(mode=self.uni_obj_mode)
                        #if not scl_vol_group.button(self.uni_obj_mode).isChecked():
                            #scl_vol_group.button(self.uni_obj_mode).setChecked(True)
                    if cmds.selectMode(q=True, co=True):
                        #print 'pre scl component space :', self.scl_cmp_space
                        space_group.button(self.scl_cmp_space).setChecked(True)
                        self.rebuild_uni_vol(mode=self.uni_cmp_mode)
                        #if not scl_vol_group.button(self.uni_cmp_mode).isChecked()
                            #scl_vol_group.button(self.uni_cmp_mode).setChecked(True)
                if select_rot.isChecked():
                    space_group.button(self.rot_space).setChecked(True)
                if select_trans.isChecked():
                    space_group.button(self.trans_space).setChecked(True)
            if mode == 4:
                if select_scale.isChecked():
                    if cmds.selectMode(q=True, o=True):
                        if self.scl_obj_space == 0:
                            self.scl_obj_space = 1
                        #print 'pre scl object space :', self.scl_cmp_space
                        space_group.button(self.scl_obj_space).setChecked(True)
                        if self.uni_obj_mode != -1:
                            self.rebuild_uni_vol(mode=self.uni_obj_mode)
                            #if not scl_vol_group.button(self.uni_obj_mode).isChecked():
                                #scl_vol_group.button(self.uni_obj_mode).setChecked(True)
                    if cmds.selectMode(q=True, co=True):
                        #print 'pre scl component space :', self.scl_cmp_space
                        space_group.button(self.scl_cmp_space).setChecked(True)
                        if self.uni_cmp_mode != -1:
                            self.rebuild_uni_vol(mode=self.uni_cmp_mode)
                            #if not scl_vol_group.button(self.uni_cmp_mode).isChecked():
                                #scl_vol_group.button(self.uni_cmp_mode).setChecked(True)
            if mode == 5:
                if select_rot.isChecked():
                    space_group.button(self.rot_space).setChecked(True)
            if mode == 6:
                #print 'set trans group :', mode, self.trans_space
                #print space_group.buttons ()
                if select_trans.isChecked():
                    space_group.button(self.trans_space).setChecked(True)
            if mode == 7:
                if select_but.isChecked():
                    #print 'mode 7'
                    #print space_group.checkedId()
                    id =  space_group.checkedId()
                    if id == 3:
                        id = 1
                    elif id == 4:
                        id = 0
                    elif id == 5:
                        id = 2
                    self.pre_select_group = id
                    space_group.button(id).setChecked(True)
        except Exception as e:
            print 'load pre selection error', mode, select_ctx
            print e.message
          
    #全軸有効になっている場合はAll選択ボタンをハイライトする
    def check_xyz(self, mode=0):
        #print 'check xyz :', mode
        if mode == 0:
            if self.but_scale_x.isChecked() and self.but_scale_y.isChecked() and self.but_scale_z.isChecked():
                self.but_scale_all.setChecked(True)
            else:
                self.but_scale_all.setChecked(False)
        if mode == 1:
            if self.but_rot_x.isChecked() and self.but_rot_y.isChecked() and self.but_rot_z.isChecked():
                self.but_rot_all.setChecked(True)
            else:
                self.but_rot_all.setChecked(False)
                self.but_rot_all.setChecked(False)
        if mode == 2:
            if self.but_trans_x.isChecked() and self.but_trans_y.isChecked() and self.but_trans_z.isChecked():
                self.but_trans_all.setChecked(True)
            else:
                self.but_trans_all.setChecked(False)
                
    #全選択ボタンを押したときは全軸有効/無効にする
    def toggle_enable(self, mode=0, axis=0):
        if axis == 3:
            m = self.srt_list[mode]
            a = self.axis_list[axis]
            exec('on_off = self.but_'+m+a+'.isChecked()')
            #print 'all_change :', m+a, on_off
            for i, b_list in enumerate(self.all_srt_but_list):
                if i != mode:
                    continue
                for but in b_list:
                    #print 'disable but :', mode, but.text()
                    but.setChecked(on_off)
            
    #選択したXYZのSRTモードボタンを有効にし、他のSRTをすべて無効にする。SRT自身での押下は無効。
    def set_disable(self, mode=0, but_id=0):
        #print '*+*+*+*+*+* set_disable func *+*+*+*+*+*'
        #print mode
        target_tool_list = ['scaleSuperContext', 'RotateSuperContext', 'moveSuperContext', 'selectSuperContext']
        #print 'change mode :', mode, 'but_id :', but_id
        #print maya_ver
        for i, b_list in enumerate(self.all_srt_but_list):
            if i == mode:
                #print 'skip disable :', mode
                #if but_id != 3::
                    #b_list[3].setChecked(True)
                continue
            for but in b_list:
                #print 'disable but :', mode, but.text()
                but.setChecked(False)
        #セレクトボタンが押された時の処理
        if mode is not None:
            #2015以下では引数がないのでシングルセレクトのみ、平面ハンドルつかめない。
            #ローテーションはそもそも2軸回転できない。
            if maya_ver <= 2015 or mode==1:
                self.single_axis_selection(mode=mode, but_id=but_id)
            #コンテキスト変更に伴いXYZ全部選ばれないように事前に現在の状態を保存
            self.keep_srt_select(mode=mode)
            #コンテキスト変更
            cmds.setToolTo(target_tool_list[mode])
            select_but.setChecked(False)
            select_but.setIcon(QIcon(image_path+self.sel_off_icon))
            self.select_manip_handle(mode=mode)
        else:
            #セレクトオンになったときはセレクトツールに変更してアイコン変更
            cmds.setToolTo(target_tool_list[3])
            select_but.setIcon(QIcon(image_path+self.sel_on_icon))
            
    #Maya2015以下の場合平面ハンドルがつかめないので一軸選択に限定する。
    def single_axis_selection(self, mode=0, but_id=0):
        #print 'single axis sel for maya 2015', mode, but_id
        if but_id == 4:
            return
        for i, b_list in enumerate(self.all_srt_but_list):
            if i == mode:
                if not b_list[but_id].isChecked():
                    b_list[but_id].setChecked(True)
                for j, but in enumerate(b_list[0:3]):
                    #print 'disable but :', mode, but.text()
                    if j != but_id:
                        but.setChecked(False)
                        
    def select_manip_handle(self, mode):
        b_list = self.all_srt_but_list[mode][0:3]
        active_list = map(lambda a:a.isChecked(), b_list)
        #print active_list
        if all(active_list):
            handle_id = 3
        else:
            if active_list.count(True) == 1:
                handle_id = active_list.index(True)
            else:
                if active_list.index(False) == 2:
                    handle_id = 4
                if active_list.index(False) == 0:
                    handle_id = 5
                if active_list.index(False) == 1:
                    handle_id = 6
        if mode == 0:
            #print 'set manip scale handle', handle_id
            if maya_ver >= 2015:
                cmds.manipScaleContext('Scale', e=True, cah=handle_id, ah=handle_id)
            else:
                cmds.manipScaleContext('Scale', e=True, ah=handle_id)
        if mode == 1:
            #print 'set manip scale handle', handle_id
            if handle_id == 3:
                handle_id = 4
            if maya_ver >= 2015:
                cmds.manipRotateContext('Rotate', e=True, cah=handle_id, ah=handle_id)
            else:
                cmds.manipRotateContext('Rotate', e=True, ah=handle_id)
        if mode == 2:
            #print 'set manip scale handle', handle_id
            if maya_ver >= 2015:
                cmds.manipMoveContext('Move', e=True, cah=handle_id, ah=handle_id)
            else:
                cmds.manipMoveContext('Move', e=True, ah=handle_id)
        
    #マルチライン選択の一括入力を実行する
    def check_multi_selection(self, text='', current=(0, 0)):
        #フォーカス外れても実行マルチラインになかったら実行しない
        if self.multi_focus_list[current[0]][current[1]]:
            #print u'フォーカス外れ暴発防止 :', current
            return
        #含まれていても現在フォーカスがないなら実行しない
        focus_check = self.all_xyz_list[current[0]][current[1]].hasFocus()
        if not focus_check:
            #print u'フォーカスの有無をチェック', focus_check
            return
        #前々回入力と一致する場合は実行しない
        if self.pre_pre_lines_text[current[0]][current[1]] == text:
            #print 'pre pre check : skip mulit line edit, line not changed :', text, current
            return
        #if self.pre_lines_text[current[0]][current[1]] == text:
            #print 'pre check : skip mulit line edit, line not changed :', text, current
            #return
        #print 'check_multi_selection', text, current
        current_flag = self.all_multi_list[current[0]][current[1]]
        if not current_flag:
            return
        for m, each_lines in enumerate(self.all_multi_list):
            for a, line_value in enumerate(each_lines):
                if line_value:
                    #現在のラインだけフォーカス外すモードで実行する
                    if (m, a) == current:
                        focus = True
                    else:
                        focus = False
                    #print 'get multi line', m, a, text
                    if m == 0:
                        self.scaling(text=text, axis=a, focus=focus)
                    if m == 1:
                        self.rotation(text=text, axis=a, focus=focus)
                    if m == 2:
                        self.translation(text=text, axis=a, focus=focus)
                    button = self.all_xyz_list[m][a]
                    #qt.change_button_color(button, textColor=string_col, bgColor=bg_col)
                    self.all_multi_list[m][a] = False
                    
    def keep_focused_text(self, text):
        #print 'keep_focus', text
        self.focus_text = text
                    
    #同じ文字列でも入力されたかどうかを判定するため、1つ前の文字入力を比較して状態保存
    def keep_pre_line_text(self, text='', current=(0, 0)):
        pre_text = self.pre_lines_text[current[0]][current[1]]
        #print 'keep_pre_line_text :', pre_text, 'imput new text :', text, current
        if pre_text != text:
            self.pre_pre_lines_text[current[0]][current[1]] = pre_text
            self.pre_lines_text[current[0]][current[1]] = text
            #print 'edited', text, self.pre_lines_text[current[0]][current[1]]
                
    #SIのマルチライン一括入力機能を再現
    def select_xyz_line(self, mode=0, axis=0):
        global current_line
        for m, each_lines in enumerate(self.all_xyz_list):
            for a, line in enumerate(each_lines):
                self.pre_lines_text[m][a] = line.text()
        #print 'chash pre line text', self.pre_lines_text
        #print 'toggle select lines :', mode, axis
        lines_list = self.all_xyz_list[mode]
        multi_list = self.all_multi_list[mode]
        #print 'get_current_list :', multi_list, mode, axis
        #全軸変換の時の処理、1つでもマルチラインがあれば全トグル
        if axis == 4:
            #print 'select all liens :', mode
            if any(multi_list):
                #print 'disable multi line selection'
                bg_color = bg_col
                st_color = string_col
                self.all_multi_list[mode] = [False]*3
                self.multi_focus_list[mode] = [True]*3#暴発無視リスト
            else:
                #print 'enable multi line selection'
                bg_color = multi_sel_col
                st_color = string_col
                self.all_multi_list[mode] = [True]*3
                self.multi_focus_list[mode] = [False]*3#暴発無視リスト
            multi_list = self.all_multi_list[mode]
            #print 'set_current_list :', multi_list, mode, axis
            for i, line in enumerate(lines_list):
                    if i == 0 and self.all_multi_list[mode][0]:
                        #print 'select all line', line.text()
                        self.set_active_line(line)
                    if i == 0 and not self.all_multi_list[mode][0]:
                        num = len(line.text())
                        line.setSelection(0, 0)
                        self.reselect_current_line()#一番上のラインを再選択
                    if not self.all_multi_list[mode][i]:
                        if self.attr_lock_flag_list[mode][i] is True:
                            bg_color = locked_bg_col
                            st_color = locked_text_col
                        elif self.attr_lock_flag_list[mode][i]== 'multi':
                            bg_color = multi_lock_bg
                            st_color = locked_text_col
                        else:
                            bg_color = bg_col
                            st_color = string_col
                    qt.change_button_color(line, textColor=st_color, bgColor=bg_color)
        #一行づつトグルする
        else:
            current_flag = self.all_multi_list[mode][axis]
            line = lines_list[axis]
            #print 'toggle one line :', current_flag
            if current_flag:
                self.all_multi_list[mode][axis] = False
                self.multi_focus_list[mode][axis] = True#暴発無視リスト
                self.reselect_current_line()#一番上のラインを再選択
                if self.attr_lock_flag_list[mode][axis] is True:
                    bg_color = locked_bg_col
                    st_color = locked_text_col
                elif self.attr_lock_flag_list[mode][axis] == 'multi':
                    bg_color = multi_lock_bg
                    st_color = locked_text_col
                else:
                    bg_color = bg_col
                    st_color = string_col
                qt.change_button_color(line, textColor=st_color, bgColor=bg_color)
            else:
                self.all_multi_list[mode][axis] = True
                self.multi_focus_list[mode][axis] = False#暴発無視リスト
                #print 'select part line', line.text()
                self.set_active_line(line)
                qt.change_button_color(line, textColor=string_col, bgColor=multi_sel_col)
        #for m_list in self.all_multi_list:
            #print m_list
                
    def set_active_line(self, line):
        line.setFocus()
        num = len(line.text())
        line.setSelection(0, num)
        
    #マルチ選択解除時に一番上のアクティブラインを再選択する
    def reselect_current_line(self):
        break_flag = False
        for j, m_line in enumerate(self.all_multi_list):
            for k, a_line in enumerate(m_line):
                if a_line:
                    focus_line = self.all_xyz_list[j][k]
                    focus_line.setFocus()
                    num = len(focus_line.text())
                    focus_line.setSelection(0, num)
                    break_flag = True
                    break
            if break_flag:
                break
            
    #ホイールで数値を増減
    def set_wheel_value(self, mode=0, axis=0):
        m = self.srt_list[mode]
        a = self.axis_list[axis]
        exec('t = '+m+a+'.text()')
        exec('v = self.'+m+a+'_wheel.value()')
        #print 'add Value', t
        if not t:
            exec('self.'+m+a+'_wheel.setValue(0.0)')
            return
        exec('v = float('+m+a+'.text())+v')
        #print 'add Value', v
        exec(m+a+'.setText(str(v))')
        exec('self.'+m+a+'_wheel.setValue(0.0)')
        
    #SRTモードをトグルした場合は選択、TRSモードを入れ替える
    def toggle_select_mode(self, mode=0):
        #print 'toggle srt sel mode'
        m = self.srt_list[mode]
        exec('pre_sel = select_'+m+'.isChecked()')
        #print 'pre select', m, pre_sel
        if not pre_sel:
            self.keep_srt_select(mode=mode)
            for but in self.all_srt_but_list[mode]:
                but.setChecked(False)
            
    #ラインエディットを作って返す
    def make_line_edit(self, text=200, bg=40):
        line = qt.LineEdit()
        line.setAcceptDrops(False)
        qt.change_button_color(line, textColor=text, bgColor=bg)
        return line
        
    def make_h_line(self, text=255, bg=128):
        global line_list
        line = qt.make_h_line()
        qt.change_button_color(line, textColor=text, bgColor=bg)
        line_list.appned(line)
        return line
        
    #ホイールを作る
    def make_wheel(self, text=255, bg=128):
        wheel = QDoubleSpinBox(self)#スピンボックス
        wheel.setRange(-10.0, 10.0)
        wheel.setValue(0.00)#値を設定
        wheel.setDecimals(1)#小数点桁数設定
        wheel.setMaximumWidth(25)
        wheel.setSingleStep(0.1)
        wheel.setDisabled(True)
        wheel.setButtonSymbols(QAbstractSpinBox.NoButtons)#上下ボタンなしにする
        qt.change_button_color(wheel, textColor=text, bgColor=bg)
        return wheel
        
    def init_si_color(self):
        pass
    def init_maya_color(self):
        pass
                
    #UI構築
    def _initUI(self):
        self.ds_line_list=[]
        global line_list
        line_list = []
        self.init_flag = True#起動時かどうかを判定するフラグを立てておく
        global all_flat_buttons
        all_flat_buttons = []
        global all_flat_button_palams
        all_flat_button_palams = []
        
        global text_col
        global mute_text
        global hilite
        global string_col
        global multi_sel_col
        global bg_col
        global menu_text
        global menu_bg
        global menu_high_bg
        global menu_high_text
        global base_col
        global ui_color
        global mid_color
        global radio_base_col
        global gray_text
        global push_col
        global line_col
        global border_col
        global locked_bg_col
        global locked_text_col
        global multi_lock_bg
        self.ui_preset = 'maya'
        
        if self.ui_col == 0:
            multi_sel_col = [0, 64, 128]
            ui_color = [170, 167, 164]
            hilite = 200
            mid_color = [142, 140, 138]
            bg_col = [54, 51, 51]
            text_col = [44, 43, 42]
            red = [250, 70, 70]
            green = [70, 250, 133]
            blue = [47, 103, 252]
            string_col = 235
            immed = [189, 138, 138]
            menu_high_text=255
            menu_high_bg=[0, 120, 215]
            mute_text = 120
            menu_text = 0
            menu_bg=224
            base_col = 224
            radio_base_col = [192, 189, 188]
            locked_bg_col = [92, 104, 116]
            locked_text_col = 0
            multi_lock_bg = [128,128,192]
            if evolution_flag:
                line_col = [90, 240, 190]
                border_col = [90, 210, 170]
            else:
                line_col = [220, 130, 130]
                border_col = [200, 110, 110]
            gray_text = 160
            push_col = [132, 130, 128]
            
            all_axis_icon = 'All_Axis.png'
            self.sel_on_icon = 'Select_On.png'
            self.sel_off_icon = 'Select_Off.png'
            self.x_on = 'x_on_si.png'
            self.x_off = 'x_off_si.png'
            self.y_on = 'y_on_si.png'
            self.y_off = 'y_off_si.png'
            self.z_on = 'z_on_si.png'
            self.z_off = 'z_off_si.png'
            self.s = 's_si.png'
            self.r = 'r_si.png'
            self.t = 't_si.png'
            self.l = 'l_si.png'
            self.check_icon = 'check_si'
            
        elif self.ui_col == 1:
            multi_sel_col = [0, 64, 128]
            hilite = 100
            ui_color = 68
            text_col = 200
            mid_color = 100
            menu_text = 200
            menu_bg=70
            menu_high_bg=[97, 132, 167]
            menu_high_text=255
            base_col = 42
            radio_base_col = 42
            bg_col = [54, 51, 51]
            red = [250, 70, 70]
            green = [40, 200, 100]
            blue = [47, 103, 252]
            string_col = 235
            immed = [189, 138, 138]
            mute_text = 120
            line_col = [230, 190, 70]
            border_col = [180, 140, 30]
            gray_text = 160
            push_col = 120
            locked_bg_col = [92, 104, 116]
            locked_text_col = 0
            multi_lock_bg = [128,128,192]
            
            all_axis_icon = 'All_Axis_Maya.png'
            self.sel_on_icon = 'Select_On_Maya.png'
            self.sel_off_icon = 'Select_Off_Maya.png'
            self.x_on = 'x_on_maya.png'
            self.x_off = 'x_off_maya.png'
            self.y_on = 'y_on_maya.png'
            self.y_off = 'y_off_maya.png'
            self.z_on = 'z_on_maya.png'
            self.z_off = 'z_off_maya.png'
            self.s = 's_maya.png'
            self.r = 'r_maya.png'
            self.t = 't_maya.png'
            self.l = 'l_maya.png'
            self.check_icon = 'check_maya'
        
        sq_widget = QScrollArea(self)
        sq_widget.setWidgetResizable(True)#リサイズに中身が追従するかどうか
        sq_widget.setFocusPolicy(Qt.NoFocus)#スクロールエリアをフォーカスできるかどうか
        sq_widget.setMinimumHeight(1)#ウィンドウの最小サイズ
        qt.change_widget_color(sq_widget, bgColor=ui_color)
        self.setCentralWidget(sq_widget)
        
        wrapper = QWidget()
        
        sq_widget.setWidget(wrapper)
        self.main_layout = QGridLayout()
        self.main_layout.setSpacing(2)#ウェジェットどうしの間隔を設定する
        wrapper.setLayout(self.main_layout)
        #--------------------------------------------------------------------------------
        vn = 0
        #--------------------------------------------------------------------------------
        #ラベルを挿入
        label = QLabel(version)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label, vn, 0, 1 ,11)
        #オプションボタン--------------------------------------------------------------------------------
        #self.bar_option = make_flat_btton(name = 'Option', text=text_col, bg=hilite, h_max=10, w_min=si_w, w_max=si_w)
        #self.main_layout.addWidget(self.bar_option, vn, 6, 1 ,5)
        vn+=1
        #カラー変更ボタン--------------------------------------------------------------------------------
        self.ui_si = make_flat_btton(icon=image_path+'SI_Icon.png',name = ' S_Color ', text=text_col, bg=hilite, h_max=22, w_min=si_w, w_max=si_w)
        self.main_layout.addWidget(self.ui_si, vn, 0, 1 ,6)
        self.ui_maya = make_flat_btton(icon=image_path+'Maya_Icon.png', name = 'M_Color ', text=text_col, bg=hilite, h_max=22, w_min=maya_w, w_max=maya_w)
        self.main_layout.addWidget(self.ui_maya, vn, 6, 1 ,5)
        self.ui_group = QButtonGroup(self)#ボタンをまとめる変数を定義
        self.ui_group.addButton(self.ui_si, 0)
        self.ui_group.addButton(self.ui_maya, 1)
        self.ui_group.button(self.ui_col).setChecked(True)
        self.ui_group.buttonClicked.connect(lambda : self.change_ui_color(mode=self.ui_group.checkedId()))
        vn+=1
        self.main_layout.addWidget(make_h_line(text=line_col, bg=line_col), vn, 0, 1 ,11)
        #--------------------------------------------------------------------------------
        vn+=1
        self.select_top = make_flat_btton(name='Select', checkable=False, flat=False, text=text_col, h_min=top_h, bg=mid_color, hover=top_hover)
        self.main_layout.addWidget(self.select_top, vn, 0, 1 ,11)
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #選択モードボタン--------------------------------------------------------------------------------
        #select_but = QPushButton(QIcon(image_path+'Select_On.png'), '', self)
        global select_but
        select_but = make_flat_btton(name = '', text=text_col, bg=ui_color, icon_size=(44, 44), policy=True, h_max=None, hover=False)
        self.pre_context = cmds.currentCtx() 
        if self.pre_context == 'selectSuperContext':
            select_but.setIcon(QIcon(image_path+self.sel_on_icon))
            select_but.setChecked(True)
        else:
            select_but.setIcon(QIcon(image_path+self.sel_off_icon))
            select_but.setChecked(False)
        select_but.toggled.connect(lambda : self.load_pre_selection(mode=7))
        select_but.toggled.connect(self.set_select_context)
        select_but.toggled.connect(set_active_mute)
        self.main_layout.addWidget(select_but, vn, 0, 2 ,6)
        self.main_layout.setRowStretch(vn,0)
        self.main_layout.setRowStretch(vn,1)
        self.main_layout.setRowStretch(vn+1,0)
        
        
        global select_group_but
        select_group_but = make_flat_btton(name='Group', text=text_col, bg=hilite)
        global pre_sel_group_but
        select_group_but.setChecked(pre_sel_group_but)
        select_group_but.toggled.connect(lambda : sisidebar_sub.change_group_mode(select_group_but.isChecked()))
        select_group_but.toggled.connect(lambda : self.set_pre_sel_group_but(select_group_but.isChecked()))
        select_group_but.clicked.connect(lambda : select_but.setChecked(True))
        #self.select_group_but.setDisabled(True)
        self.main_layout.addWidget(select_group_but, vn, 6, 1 ,5)
        global center_mode_but
        center_mode_but = make_flat_btton(name='Center', text=text_col, bg=hilite)
        center_mode_but.toggled.connect(lambda : toggle_center_mode(init='init', mode=center_mode_but.isChecked()))
        #center_mode_but.setDisabled(True)
        self.main_layout.addWidget(center_mode_but, vn+1, 6, 1 ,5)
        vn+=2
        #セレクションフィルター--------------------------------------------------------------------------------
        filter_w = 22
        filter_h = 22
        self.select_line_a = make_h_line()
        self.main_layout.addWidget(self.select_line_a, vn, 0, 1 ,11)
        vn+=1
        self.select_all_but = make_flat_btton(icon=':/iconSuper.png', name='', text=text_col, bg=hilite, w_max=filter_w, h_max=filter_h, tip='All Filters')
        self.main_layout.addWidget(self.select_all_but, vn, 0, 1 ,2)
        self.select_Marker_but = make_flat_btton(icon=':/pickHandlesObj.png', name='', text=text_col, bg=hilite, w_max=filter_w, h_max=filter_h, tip='Handel')
        self.main_layout.addWidget(self.select_Marker_but, vn, 2, 1 ,2)
        self.select_joint_but = make_flat_btton(icon=':/pickJointObj.png', name='', text=text_col, bg=hilite, w_max=filter_w, h_max=filter_h, tip='Joint')
        self.main_layout.addWidget(self.select_joint_but, vn, 4, 1 ,2)
        self.select_surface_but = make_flat_btton(icon=':/pickGeometryObj.png', name='', text=text_col, bg=hilite, w_max=filter_w, h_max=filter_h, tip='Geometry')
        self.main_layout.addWidget(self.select_surface_but, vn, 6, 1 ,2)
        self.select_curve_but = make_flat_btton(icon=':/pickCurveObj.png', name='', text=text_col, bg=hilite, w_max=filter_w, h_max=filter_h, tip='Curve')
        self.main_layout.addWidget(self.select_curve_but, vn, 8, 1 ,2)
        self.select_deform_but = make_flat_btton(icon=':/pickDeformerObj.png', name='', text=text_col, bg=hilite, w_max=filter_w, h_max=filter_h, tip='Deformer')
        self.main_layout.addWidget(self.select_deform_but, vn, 10, 1 ,1)
        self.filter_group = QButtonGroup(self)#ボタンをまとめる変数を定義
        self.filter_group.addButton(self.select_all_but, 0)
        self.filter_group.addButton(self.select_Marker_but, 1)
        self.filter_group.addButton(self.select_joint_but, 2)
        self.filter_group.addButton(self.select_surface_but, 3)
        self.filter_group.addButton(self.select_curve_but, 4)
        self.filter_group.addButton(self.select_deform_but, 5)
        self.filter_group.button(0).setChecked(True)
        self.filter_group.buttonClicked.connect(lambda : self.select_filter_mode(mode=self.filter_group .checkedId()))
        self.select_filter_mode(mode=self.filter_group .checkedId())#フィルターを初期化しておく
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #選択入力ラインエディット--------------------------------------------------------------------------------
        #フィルターセットしているときにウインドウ触るとフォーカスとって暴発することがあるのを防ぐためのダミーライン
        self.dummy_line = self.make_line_edit(text=string_col, bg=bg_col)
        self.dummy_line.setVisible(False)
        self.main_layout.addWidget(self.dummy_line, vn, 0, 1, 11)
        vn+=1
        self.selection_line = self.make_line_edit(text=string_col, bg=bg_col)
        self.main_layout.addWidget(self.selection_line, vn, 0, 1, 11)
        self.selection_line.textChanged.connect(self.keep_pre_search_line)
        self.selection_line.editingFinished.connect(self.search_node)
        vn+=1
        #厳密に位置調整
        ud_w = 39
        ud_h = 6
        lr_w = 13
        lr_h = 16
        lr_min = 18
        self.index_line = self.make_line_edit(text=string_col, bg=bg_col)
        self.index_line.editingFinished.connect(self.search_component)
        self.main_layout.addWidget(self.index_line, vn, 0, 2, 8)
        self.pick_up = make_flat_btton(icon=':/arrowUp', name='', text=text_col, bg=ui_color, checkable=False, w_max=ud_w, h_max=ud_h ,h_min=None)
        self.pick_up.clicked.connect(lambda : self.pick_walk(mode='up'))
        self.main_layout.addWidget(self.pick_up, vn, 8, 1, 3)
        self.pick_down = make_flat_btton(icon=':/arrowDown', name='', text=text_col, bg=ui_color, checkable=False, w_max=ud_w, h_max=ud_h ,h_min=None)
        self.pick_down.clicked.connect(lambda : self.pick_walk(mode='down'))
        self.main_layout.addWidget(self.pick_down, vn+1, 8, 1, 3)
        self.pick_left = make_flat_btton(icon=':/arrowLeft', name='', text=text_col, bg=ui_color, checkable=False, w_max=lr_w, h_max=lr_h ,h_min=lr_min)
        self.pick_left.clicked.connect(lambda : self.pick_walk(mode='left'))
        self.main_layout.addWidget(self.pick_left, vn, 8, 2, 1)
        self.pick_right = make_flat_btton(icon=':/arrowRight', name='', text=text_col, bg=ui_color, checkable=False, w_max=lr_w, h_max=lr_h ,h_min=lr_min)
        self.pick_right.clicked.connect(lambda : self.pick_walk(mode='right'))
        self.main_layout.addWidget(self.pick_right, vn, 10, 2, 1)
        vn+=2
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #検索タイプフィルタリング
        vh = 0
        hw = 2
        fw = 23
        fh =18
        self.all_filter = make_flat_btton(name='All', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from all node types')
        self.all_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.all_filter.text()))
        self.all_filter.setChecked(True)
        self.main_layout.addWidget(self.all_filter, vn, vh, 1, hw)
        vh += hw
        self.transform_filter = make_flat_btton(name='Trs', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Transform node')
        self.transform_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.transform_filter.text()))
        self.main_layout.addWidget(self.transform_filter, vn, vh, 1, hw)
        vh += hw
        self.joint_filter = make_flat_btton(name='Jot', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Joint')
        self.joint_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.joint_filter.text()))
        self.main_layout.addWidget(self.joint_filter, vn, vh, 1, hw)
        vh += hw
        self.shape_filter = make_flat_btton(name='Sap', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Shape node')
        self.shape_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.shape_filter.text()))
        self.main_layout.addWidget(self.shape_filter, vn, vh, 1, hw)
        vh += hw
        self.dummy_but_a = make_flat_btton(name='Nan', text=mute_text, bg=hilite, checkable=False, w_max=fw, h_max=fh, tip='Future filters will be added')
        self.main_layout.addWidget(self.dummy_but_a , vn, vh, 1, hw)
        vh += hw
        self.dummy_but_b = make_flat_btton(name='Nan', text=mute_text, bg=hilite, checkable=False, w_max=fw, h_max=fh, tip='Future filters will be added')
        self.main_layout.addWidget(self.dummy_but_b , vn, vh, 1, hw)
        vh += hw
        vn+=1
        vh = 0#ボタンの開始地点
        self.parent_cons_filter = make_flat_btton(name='Pac', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Parent Constraint')
        self.parent_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.parent_cons_filter.text()))
        self.main_layout.addWidget(self.parent_cons_filter, vn, vh, 1, hw)
        vh += hw
        self.point_cons_filter = make_flat_btton(name='Poc', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Point Constraint')
        self.point_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.point_cons_filter.text()))
        self.main_layout.addWidget(self.point_cons_filter, vn, vh, 1, hw)
        vh += hw
        self.orient_cons_filter = make_flat_btton(name='Orc', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Orient Constraint')
        self.orient_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.orient_cons_filter.text()))
        self.main_layout.addWidget(self.orient_cons_filter, vn, vh, 1, hw)
        vh += hw
        self.scale_cons_filter = make_flat_btton(name='Slc', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Scale Constraint')
        self.scale_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.scale_cons_filter.text()))
        self.main_layout.addWidget(self.scale_cons_filter, vn, vh, 1, hw)
        vh += hw
        self.aim_cons_filter = make_flat_btton(name='Aic', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Aim Constraint')
        self.aim_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.aim_cons_filter.text()))
        self.main_layout.addWidget(self.aim_cons_filter, vn, vh, 1, hw)
        vh += hw
        self.select_line_c = make_h_line()
        self.dummy_but_c = make_flat_btton(name='Nan', text=mute_text, bg=hilite, checkable=False, w_max=fw, h_max=fh, tip='Future filters will be added')
        self.main_layout.addWidget(self.dummy_but_c , vn, vh, 1, 1)
        vh += hw
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #self.main_layout.addWidget(self.select_line_c, vn, 0, 1 ,11)
        #vn+=1
        #一括操作ようにリストにしておく
        self.all_select_but_list = [select_but, select_group_but, center_mode_but]
        self.all_filter_but_list = [self.select_all_but, self.select_Marker_but, self.select_joint_but, 
                                            self.select_curve_but, self.select_surface_but, self.select_deform_but]
        self.all_search_widgets = [self.selection_line, self.index_line, self.pick_down, self.pick_left, self.pick_up, self.pick_right] 

        self.filter_but_list = [self.all_filter, self.transform_filter, 
                                    self.joint_filter,self.shape_filter, 
                                    self.dummy_but_a, self.dummy_but_b, 
                                    self.parent_cons_filter, self.point_cons_filter, 
                                    self.orient_cons_filter, self.scale_cons_filter, 
                                    self.aim_cons_filter, self.dummy_but_c]
                                    
        self.select_lines = [self.select_line_a] 
                                    #self.select_line_b, 
                                    #self.select_line_c]
        for but in self.filter_but_list:
            but.rightClicked.connect(lambda : self.pop_option_window(mode='filter'))
        self.select_section_but = self.all_select_but_list+self.all_filter_but_list+self.all_search_widgets+self.filter_but_list+self.select_lines
        #高さを保存
        self.select_section_height = [but.height() for but in self.select_section_but]
        self.select_top.rightClicked.connect(lambda : self.toggle_ui(buttons=self.select_section_but,  heights=self.select_section_height))
        #--------------------------------------------------------------------------------
        #トランスフォームエリア
        #action.triggered.connect()
        self.transfrom_top = make_flat_btton(name='Transform', checkable=False, flat=False, text=text_col, h_min=top_h, bg=mid_color, hover=top_hover)
        top_menus = self.create_trans_menu()
        self.transfrom_top.setMenu(top_menus)
        #qt.change_button_color(self.transfrom_top, textColor=text_col, bgColor=mid_color)
        #検索、セレクション表示窓--------------------------------------------------------------------------------
        self.main_layout.addWidget(self.transfrom_top, vn, 0, 1 ,11)
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #スケール
        global scale_x
        global scale_y
        global scale_z
        global select_scale
        global key_scale_x 
        global key_scale_y
        global key_scale_z 
        
        line_min_size = 55
        wheel_max_size = 26
        
        axis_size = (24, 20)#xyzアイコンの大きさ
        axis_w = 24#軸ボタンの幅
        axis_h = 20#軸ボタンの高さ
        sel_w = 22#SRT選択ボタンの幅
        sel_h = 22#SRT選択ボタンの幅
        
        anim_b = 2#ボタンの幅
        text_b = 6#ラインの幅
        axis_b = 2#軸ボタンの幅
        sel_b = 1#選択ボタンの幅
        
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_scale_x = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_scale_x.clicked.connect(lambda : set_key_frame(mode=0, axis=0))
        key_scale_x.rightClicked.connect(lambda : set_key_frame(mode=0, axis=3))
        self.main_layout.addWidget(key_scale_x, vn, tw, 1, anim_b)
        tw += anim_b
        
        scale_x = self.make_line_edit(text=string_col, bg=bg_col)
        scale_x.setMinimumWidth(line_min_size)
        scale_x.editingFinished.connect(lambda : self.check_multi_selection(text=scale_x.text(), current=(0, 0)))
        scale_x.textChanged.connect(lambda : self.keep_pre_line_text(text=scale_x.text(), current=(0, 0)))#入力変更が成されたかどうかを判定するように即時保存を実行
        scale_x.editingFinished.connect(lambda : self.scaling(text=scale_x.text(), axis=0))
        self.main_layout.addWidget(scale_x, vn, tw, 1, text_b)
        tw += text_b
        
        self.but_scale_x = make_flat_btton(icon=image_path+self.x_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        self.main_layout.addWidget(self.but_scale_x, vn, tw, 1 ,axis_b)
        tw += axis_b
        #切り替え
        select_scale = make_flat_btton(icon=image_path+self.s, icon_size=(20, 20), 
                                                            name = '', text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        select_scale.clicked.connect(lambda : self.toggle_select_mode(mode=0))
        self.main_layout.addWidget(select_scale, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_scale_y = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_scale_y.clicked.connect(lambda : set_key_frame(mode=0, axis=1))
        key_scale_y.rightClicked.connect(lambda : set_key_frame(mode=0, axis=3))
        self.main_layout.addWidget(key_scale_y, vn, tw, 1, anim_b)
        tw += anim_b
        scale_y = self.make_line_edit(text=string_col, bg=bg_col)
        scale_y.editingFinished.connect(lambda : self.check_multi_selection(text=scale_y.text(), current=(0, 1)))#マルチラインは先にコネクト
        scale_y.textChanged.connect(lambda : self.keep_pre_line_text(text=scale_y.text(), current=(0, 1)))#入力変更が成されたかどうかを判定するように即時保存を実行
        scale_y.editingFinished.connect(lambda : self.scaling(text=scale_y.text(), axis=1))
        self.main_layout.addWidget(scale_y, vn, tw, 1 ,text_b)
        tw += text_b
        
        self.but_scale_y = make_flat_btton(icon=image_path+self.y_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        self.main_layout.addWidget(self.but_scale_y, vn, tw, 1 ,axis_b)
        tw += axis_b
        #ロック状態切り替え
        self.lock_attribute_scale = make_flat_btton(icon=image_path+self.l, icon_size=(20, 20), 
                                                            name = '', checkable=False, text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        self.lock_attribute_scale.clicked.connect(lambda : self.attribute_lock_state(mode=0))
        self.main_layout.addWidget(self.lock_attribute_scale, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_scale_z = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_scale_z.clicked.connect(lambda : set_key_frame(mode=0, axis=2))
        key_scale_z.rightClicked.connect(lambda : set_key_frame(mode=0, axis=3))
        self.main_layout.addWidget(key_scale_z, vn, tw, 1, anim_b)
        tw += anim_b
        scale_z = self.make_line_edit(text=string_col, bg=bg_col)
        scale_z.editingFinished.connect(lambda : self.check_multi_selection(text=scale_z.text(), current=(0, 2)))
        scale_z.textChanged.connect(lambda : self.keep_pre_line_text(text=scale_z.text(), current=(0, 2)))#入力変更が成されたかどうかを判定するように即時保存を実行
        scale_z.editingFinished.connect(lambda : self.scaling(text=scale_z.text(), axis=2))
        self.main_layout.addWidget(scale_z, vn, tw, 1 ,text_b)
        tw += text_b
        
        self.but_scale_z = make_flat_btton(icon=image_path+self.z_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        self.main_layout.addWidget(self.but_scale_z, vn, tw, 1 ,axis_b)
        tw += axis_b
        
        #XYZ全部ボタン
        self.but_scale_all = make_flat_btton(icon=image_path+all_axis_icon, name='', text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        self.main_layout.addWidget(self.but_scale_all, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        self.trs_line_a = make_h_line()
        self.main_layout.addWidget(self.trs_line_a, vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        #ローテーション
        global rot_x
        global rot_y
        global rot_z
        global key_rot_x 
        global key_rot_y
        global key_rot_z 
        global select_rot
        
        key_rot_x = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_rot_x.clicked.connect(lambda : set_key_frame(mode=1, axis=0))
        key_rot_x.rightClicked.connect(lambda : set_key_frame(mode=1, axis=3))
        self.main_layout.addWidget(key_rot_x, vn, tw, 1, anim_b)
        tw += anim_b
        rot_x = self.make_line_edit(text=string_col, bg=bg_col)
        rot_x.editingFinished.connect(lambda : self.check_multi_selection(text=rot_x.text(), current=(1, 0)))
        rot_x.textChanged.connect(lambda : self.keep_pre_line_text(text=rot_x.text(), current=(1, 0)))#入力変更が成されたかどうかを判定するように即時保存を実行
        rot_x.editingFinished.connect(qt.Callback(lambda : self.rotation(text=rot_x.text(), axis=0)))
        self.main_layout.addWidget(rot_x, vn, tw, 1 ,text_b)
        tw += text_b
        
        self.but_rot_x = make_flat_btton(icon=image_path+self.x_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        #qt.change_button_color(self.but_rot_x, textColor=text_col, bgColor=red)
        self.main_layout.addWidget(self.but_rot_x, vn, tw, 1 ,axis_b)
        tw += axis_b
        
        #切り替え
        select_rot = make_flat_btton(icon=image_path+self.r, icon_size=(20, 20), 
                                                            name = '', text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        select_rot.clicked.connect(lambda : self.toggle_select_mode(mode=1))
        self.main_layout.addWidget(select_rot, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_rot_y = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_rot_y.clicked.connect(lambda : set_key_frame(mode=1, axis=1))
        key_rot_y.rightClicked.connect(lambda : set_key_frame(mode=1, axis=3))
        self.main_layout.addWidget(key_rot_y, vn, tw, 1, anim_b)
        tw += anim_b
        rot_y = self.make_line_edit(text=string_col, bg=bg_col)
        rot_y.editingFinished.connect(lambda : self.check_multi_selection(text=rot_y.text(), current=(1, 1)))
        rot_y.textChanged.connect(lambda : self.keep_pre_line_text(text=rot_y.text(), current=(1, 1)))#入力変更が成されたかどうかを判定するように即時保存を実行
        rot_y.editingFinished.connect(qt.Callback(lambda : self.rotation(text=rot_y.text(), axis=1)))
        self.main_layout.addWidget(rot_y, vn, tw, 1 ,text_b)
        tw += text_b
        
        self.but_rot_y = make_flat_btton(icon=image_path+self.y_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        self.main_layout.addWidget(self.but_rot_y, vn, tw, 1 ,axis_b)
        tw += axis_b
        #ロック状態切り替え
        self.lock_attribute_rot = make_flat_btton(icon=image_path+self.l, icon_size=(20, 20), 
                                                            name = '', checkable=False, text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        self.lock_attribute_rot.clicked.connect(lambda : self.attribute_lock_state(mode=1))
        self.main_layout.addWidget(self.lock_attribute_rot, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_rot_z = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_rot_z.clicked.connect(lambda : set_key_frame(mode=1, axis=2))
        key_rot_z.rightClicked.connect(lambda : set_key_frame(mode=1, axis=3))
        self.main_layout.addWidget(key_rot_z, vn, tw, 1, anim_b)
        tw += anim_b
        rot_z = self.make_line_edit(text=string_col, bg=bg_col)
        self.main_layout.addWidget(rot_z, vn, tw, 1 ,text_b)
        tw += text_b
        self.but_rot_z = make_flat_btton(icon=image_path+self.z_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        
        rot_z.editingFinished.connect(lambda : self.check_multi_selection(text=rot_z.text(), current=(1, 2)))
        rot_z.textChanged.connect(lambda : self.keep_pre_line_text(text=rot_z.text(), current=(1, 2)))#入力変更が成されたかどうかを判定するように即時保存を実行
        rot_z.editingFinished.connect(qt.Callback(lambda : self.rotation(text=rot_z.text(), axis=2)))
        self.main_layout.addWidget(self.but_rot_z, vn, tw, 1 ,axis_b)
        tw += axis_b
        #XYZ全部ボタン
        self.but_rot_all = make_flat_btton(icon=image_path+all_axis_icon, name='', text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        self.main_layout.addWidget(self.but_rot_all, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        self.trs_line_b = make_h_line()
        self.main_layout.addWidget(self.trs_line_b, vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #トランス
        global trans_x
        global trans_y
        global trans_z
        global key_trans_x 
        global key_trans_y
        global key_trans_z 
        global select_trans
        
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        key_trans_x = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_trans_x.clicked.connect(lambda : set_key_frame(mode=2, axis=0))
        key_trans_x.rightClicked.connect(lambda : set_key_frame(mode=2, axis=3))
        self.main_layout.addWidget(key_trans_x, vn, tw, 1, anim_b)
        tw += anim_b
        trans_x = self.make_line_edit(text=string_col, bg=bg_col)
        trans_x.editingFinished.connect(lambda : self.check_multi_selection(text=trans_x.text(), current=(2, 0)))
        trans_x.textChanged.connect(lambda : self.keep_pre_line_text(text=trans_x.text(), current=(2, 0)))#入力変更が成されたかどうかを判定するように即時保存を実行
        trans_x.editingFinished.connect(qt.Callback(lambda : self.translation(text=trans_x.text(), axis=0)))
        trans_x.textChanged.connect(self.set_up_manip)
        self.main_layout.addWidget(trans_x, vn, tw, 1 ,text_b)
        tw += text_b
        
        self.but_trans_x = make_flat_btton(icon=image_path+self.x_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        #qt.change_button_color(self.but_trans_x, textColor=text_col, bgColor=red)
        self.main_layout.addWidget(self.but_trans_x, vn, tw, 1 ,axis_b)
        tw += axis_b
        #切り替え
        select_trans = make_flat_btton(icon=image_path+self.t, icon_size=(20, 20), 
                                                            name = '', text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        select_trans.clicked.connect(lambda : self.toggle_select_mode(mode=2))
        self.main_layout.addWidget(select_trans, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_trans_y = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_trans_y.clicked.connect(lambda : set_key_frame(mode=2, axis=1))
        key_trans_y.rightClicked.connect(lambda : set_key_frame(mode=2, axis=3))
        self.main_layout.addWidget(key_trans_y, vn, tw, 1, anim_b)
        tw += anim_b
        trans_y = self.make_line_edit(text=string_col, bg=bg_col)
        trans_y.editingFinished.connect(lambda : self.check_multi_selection(text=trans_y.text(), current=(2, 1)))
        trans_y.textChanged.connect(lambda : self.keep_pre_line_text(text=trans_y.text(), current=(2, 1)))#入力変更が成されたかどうかを判定するように即時保存を実行
        trans_y.editingFinished.connect(qt.Callback(lambda : self.translation(text=trans_y.text(), axis=1)))
        self.main_layout.addWidget(trans_y, vn, tw, 1 ,text_b)
        tw += text_b
        self.but_trans_y = make_flat_btton(icon=image_path+self.y_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        self.main_layout.addWidget(self.but_trans_y, vn, tw, 1 ,axis_b)
        tw += axis_b
        #ロック状態切り替え
        self.lock_attribute_trans = make_flat_btton(icon=image_path+self.l, icon_size=(20, 20), 
                                                            name = '', checkable=False, text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        self.lock_attribute_trans.clicked.connect(lambda : self.attribute_lock_state(mode=2))
        self.main_layout.addWidget(self.lock_attribute_trans, vn, tw, 1 ,sel_b)
        vn+=1
        #--------------------------------------------------------------------------------
        tw = 0#配置場所
        
        key_trans_z = make_flat_btton(icon=image_path+'Key_N.png', name = '', 
                                                                text=text_col, bg=hilite, checkable=False, w_max=24)
        key_trans_z.clicked.connect(lambda : set_key_frame(mode=2, axis=2))
        key_trans_z.rightClicked.connect(lambda : set_key_frame(mode=2, axis=3))
        self.main_layout.addWidget(key_trans_z, vn, tw, 1, anim_b)
        tw += anim_b
        trans_z = self.make_line_edit(text=string_col, bg=bg_col)
        trans_z.editingFinished.connect(lambda : self.check_multi_selection(text=trans_z.text(), current=(2, 2)))
        trans_z.textChanged.connect(lambda : self.keep_pre_line_text(text=trans_z.text(), current=(2, 2)))#入力変更が成されたかどうかを判定するように即時保存を実行
        trans_z.editingFinished.connect(qt.Callback(lambda : self.translation(text=trans_z.text(), axis=2)))
        self.main_layout.addWidget(trans_z, vn, tw, 1 , text_b)
        tw += text_b
        self.but_trans_z = make_flat_btton(icon=image_path+self.z_off, icon_size=axis_size, 
                                                            name = '', text=text_col, bg=hilite, w_max=axis_w, h_max=axis_h)
        self.main_layout.addWidget(self.but_trans_z, vn, tw, 1 , axis_b)
        tw += axis_b
        #XYZ全部ボタン
        self.but_trans_all = make_flat_btton(icon=image_path+all_axis_icon, name='', text=text_col, bg=hilite, w_max=sel_w, h_max=sel_h)
        self.main_layout.addWidget(self.but_trans_all, vn, tw, 1 ,sel_b)
        vn+=1
        #アイコン変更をまとめてコネクト, オンオフアイコンを切り替える
        self.but_scale_x.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_scale_x, axis=0))
        self.but_scale_y.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_scale_y, axis=1))
        self.but_scale_z.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_scale_z, axis=2))
        self.but_rot_x.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_rot_x, axis=0))
        self.but_rot_y.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_rot_y, axis=1))
        self.but_rot_z.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_rot_z, axis=2))
        self.but_trans_x.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_trans_x, axis=0))
        self.but_trans_y.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_trans_y, axis=1))
        self.but_trans_z.toggled.connect(lambda : self.toggle_xyz_icon(but=self.but_trans_z, axis=2))
        #--------------------------------------------------------------------------------
        self.trs_line_c = make_h_line()
        self.main_layout.addWidget(self.trs_line_c, vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #変換スペース指定
        global global_but
        global local_but
        global view_but
        global add_but
        global ref_but
        global plane_but
        global space_but_list
        #UniとVolを作成
        global_but = make_flat_btton(name = 'Global', text=text_col, bg=hilite)
        self.main_layout.addWidget(global_but, vn, 0, 1 ,4)
        local_but = make_flat_btton(name = 'Local ', text=text_col, bg=hilite)
        self.main_layout.addWidget(local_but, vn, 4, 1 ,4)
        view_but = make_flat_btton(name = ' View ', text=text_col, bg=hilite)
        self.main_layout.addWidget(view_but, vn, 8, 1 ,3)
        vn+=1
        add_but = make_flat_btton(name = 'Add', text=text_col, bg=hilite)
        self.main_layout.addWidget(add_but, vn, 0, 1 ,4)
        ref_but = make_flat_btton(name = 'Ref', text=text_col, bg=hilite)
        ref_but.rightClicked.connect(self.show_ref_menu)#右クリックの挙動
        #ref_but.setDisabled(True)#今のところ無効
        self.main_layout.addWidget(ref_but, vn, 4, 1 ,4)
        plane_but = make_flat_btton(name = '*Plane*', text=text_col, bg=hilite)
        #vol_but = make_flat_btton(name = 'Vol', text=text_col, bg=hilite)
        #plane_but.setDisabled(True)#今のところ無効
        self.main_layout.addWidget(plane_but, vn, 8, 1 ,3)
        space_but_list = [global_but, local_but, view_but,
                                add_but, ref_but, plane_but]
        global space_group
        space_group = QButtonGroup(self)#ボタンをまとめる変数を定義
        space_group.addButton(global_but, 0)
        space_group.addButton(local_but, 1)
        space_group.addButton(view_but, 2)
        space_group.addButton(add_but, 3)
        space_group.addButton(ref_but, 4)
        space_group.addButton(plane_but, 5)
        space_group.button(2).setChecked(True)
        space_group.buttonClicked.connect(lambda : self.keep_srt_select(mode=3))
        space_group.buttonClicked.connect(self.chane_context_space)
        space_group.buttonClicked.connect(sisidebar_sub.get_matrix)
        global scl_vol_group
        scl_vol_group = QButtonGroup(self)#ボタンをまとめる変数を定義
        scl_vol_group.buttonClicked.connect(lambda : self.keep_srt_select(mode=3))
        scl_vol_group.buttonClicked[int].connect(self.toggle_uni_vol)
        vn+=1
        #--------------------------------------------------------------------------------
        #編集モード
        self.cog_but = make_flat_btton(name = 'COG', text=text_col, bg=hilite)
        self.cog_but.clicked.connect(qt.Callback(self.setup_object_center))
        self.main_layout.addWidget(self.cog_but, vn, 0, 1 ,4)
        prop = cmds.softSelect(q=True, softSelectEnabled=True)
        self.prop_but = make_flat_btton(name = '/Prop', text=text_col, bg=hilite)
        self.prop_but.setChecked(prop)
        self.prop_but.clicked.connect(self.toggle_prop)
        self.prop_but.rightClicked.connect(lambda : self.pop_option_window(mode='prop'))
        #self.prop_but.setDisabled(True)#今のところ無効
        self.main_layout.addWidget(self.prop_but, vn, 4, 1 ,4)
        sym = cmds.symmetricModelling(q=True, symmetry=True)
        if maya_ver >= 2015:
            topo = cmds.symmetricModelling(q=True, topoSymmetry=True) 
        else:
            topo = False
        if not sym and not topo:
            sym = False
        else:
            sym = True
        self.sym_but = make_flat_btton(name = '/Sym', text=text_col, bg=hilite)
        self.sym_but.setChecked(sym)
        self.sym_but.clicked.connect(self.toggle_sym)
        self.sym_but.rightClicked.connect(lambda : self.pop_option_window(mode='sym'))
        #self.sym_but.setDisabled(True)#今のところ無効
        self.main_layout.addWidget(self.sym_but, vn, 8, 1 ,3)
        vn+=1
        #--------------------------------------------------------------------------------
        #self.trs_line_d = make_h_line()
        #self.main_layout.addWidget(self.trs_line_d, vn, 0, 1 ,11)
        #vn+=1
        #SRTボタンをまとめてリスト化
        self.scale_but_list = [self.but_scale_x, self.but_scale_y, self.but_scale_z, select_scale, self.but_scale_all, self.lock_attribute_scale]
        self.rot_but_list = [self.but_rot_x, self.but_rot_y, self.but_rot_z, select_rot, self.but_rot_all, self.lock_attribute_rot]
        self.trans_but_list = [self.but_trans_x, self.but_trans_y, self.but_trans_z, select_trans, self.but_trans_all, self.lock_attribute_trans]
        self.all_axis_but_list = [self.scale_but_list, self.rot_but_list, self.trans_but_list]
        self.key_buts = [key_scale_x, key_scale_y, key_scale_z, key_rot_x, key_rot_y, key_rot_z, key_trans_x, key_trans_y, key_trans_z]
        self.trs_option_but = [self.cog_but, self.prop_but, self.sym_but]
        self.trs_lines = [self.trs_line_a, self.trs_line_b, self.trs_line_c]
        self.s_xyz_list = [scale_x, scale_y, scale_z]
        self.r_xyz_list = [rot_x, rot_y, rot_z]
        self.t_xyz_list = [trans_x, trans_y, trans_z]
        self.all_xyz_list = [self.s_xyz_list, self.r_xyz_list, self.t_xyz_list]
        self.trs_section_widgets = self.s_xyz_list+self.r_xyz_list+self.t_xyz_list+\
                                            self.scale_but_list+self.rot_but_list+self.trans_but_list +\
                                            self.key_buts+space_but_list+self.trs_option_but+self.trs_lines
        #開閉コネクト
        self.trs_section_height = [but.height() for but in self.trs_section_widgets]
        self.transfrom_top.rightClicked.connect(lambda : self.toggle_ui(buttons=self.trs_section_widgets,  heights=self.trs_section_height))
        
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #スナップエリア
        self.snap_top = make_flat_btton(name='Snap', checkable=False, flat=False, text=text_col, h_min=top_h, bg=mid_color, hover=top_hover)
        #qt.change_button_color(self.snap_top, textColor=text_col, bgColor=mid_color)
        self.main_layout.addWidget(self.snap_top, vn, 0, 1 ,11)
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        snap_mode = cmds.snapMode(q=True, grid=True)
        snap_w = 22
        snap_h = 22
        #print snap_mode         
        tip = lang.Lang(
        en='Snap to grids\n\nMoves the selected item to the nearest grid intersection point.\n',
        ja=u'グリッドスナップ\n\n選択した項目を最も近いグリッド交点に移動します。\n')
        self.snap_glid_but = make_flat_btton(icon=':/snapGrid.png', name='', text=text_col, bg=hilite, checkable=True, w_max=snap_w, h_max=snap_h, tip=tip.output())
        self.snap_glid_but.setChecked(snap_mode)
        self.snap_glid_but.clicked.connect(lambda : cmds.snapMode(grid=self.snap_glid_but.isChecked()))
        self.main_layout.addWidget(self.snap_glid_but, vn, 0, 1 ,2)
        
        tip = lang.Lang(
        en='Snap to curves\n\nMoves the selected item to the nearest curve.\n',
        ja=u'カーブスナップ\n\n選択した項目を最も近いカーブに移動します。\n')
        snap_mode = cmds.snapMode(q=True, curve=True)
        self.snap_segment_but = make_flat_btton(icon=':/snapCurve.png', name='', text=text_col, bg=hilite, checkable=True, w_max=snap_w, h_max=snap_h, tip=tip.output())
        self.snap_segment_but.setChecked(snap_mode)
        self.snap_segment_but.clicked.connect(lambda : cmds.snapMode(curve=self.snap_segment_but.isChecked()))
        self.main_layout.addWidget(self.snap_segment_but, vn, 2, 1 ,2)
        
        tip = lang.Lang(
        en='Snap to points\n\nMoves the selected item to the nearest control vertex or pivot.\n',
        ja=u'ポイントスナップ\n\n選択した項目を最も近いコントロール頂点(CV)または\nピボットポイントに移動します。\n')
        snap_mode = cmds.snapMode(q=True, point=True)
        self.snap_point_but = make_flat_btton(icon=':/snapPoint.png', name='', text=text_col, bg=hilite, checkable=True, w_max=snap_w, h_max=snap_h, tip=tip.output())
        self.snap_point_but.setChecked(snap_mode)
        self.snap_point_but.clicked.connect(lambda : cmds.snapMode(point=self.snap_point_but.isChecked()))
        self.main_layout.addWidget(self.snap_point_but, vn, 4, 1 ,2)
        
        tip = lang.Lang(
        en='Snap to Projected Center\n\nMoves to the center of the selected object.\n',
        ja=u'投影された中心にスナップ\n\n選択したオブジェクトの中心にスナップします。\n')
        snap_mode = cmds.snapMode(q=True, meshCenter=True)
        self.snap_pcenter_but = make_flat_btton(icon=':/snapMeshCenter.png', name='', text=text_col, bg=hilite, checkable=True, w_max=snap_w, h_max=snap_h, tip=tip.output())
        self.snap_pcenter_but.setChecked(snap_mode)
        self.snap_pcenter_but.clicked.connect(lambda : cmds.snapMode(meshCenter=self.snap_pcenter_but.isChecked()))
        self.main_layout.addWidget(self.snap_pcenter_but, vn, 6, 1 ,2)
        
        tip = lang.Lang(
        en='Snap to view planes\n\nMoves the selected item to the nearest view plane.\n',
        ja=u'ビュープレーンスナップ\n\n選択した項目を最も近いビュープレーンに移動します。\n')
        snap_mode = cmds.snapMode(q=True, viewPlane=True)
        self.snap_plane_but = make_flat_btton(icon=':/snapPlane.png', name='', text=text_col, bg=hilite, checkable=True, w_max=snap_w, h_max=snap_h, tip=tip.output())
        self.snap_plane_but.setChecked(snap_mode)
        self.snap_plane_but.clicked.connect(lambda : cmds.snapMode(viewPlane=self.snap_plane_but.isChecked()))
        self.main_layout.addWidget(self.snap_plane_but, vn, 8, 1 ,2)
        
        tip = lang.Lang(
        en='Make the selected object live\n\nConverts the selected surface to a live surface (RMB to select\nfrom previous live surface).\n',
        ja=u'選択したオブジェクトをライブにします\n\n選択したサーフェイスをライブサーフェイスに変換します\n')
        self.snap_live_but = make_flat_btton(icon=':/makeLiveIcon.png', name='', text=text_col, bg=hilite, checkable=False, w_max=snap_w, h_max=snap_h, tip=tip.output())
        self.snap_live_but.clicked.connect(self.make_live_snap)
        #self.snap_on_but.clicked.connect(self.parent_node)
        self.main_layout.addWidget(self.snap_live_but, vn, 10, 1 ,1)
        vn+=1
        #--------------------------------------------------------------------------------\
        #self.snap_line_a = make_h_line()
        #self.main_layout.addWidget(self.snap_line_a, vn, 0, 1 ,11)
        #vn+=1
        
        #一括操作のためにボタンをリスト化
        self.snap_section_but = [self.snap_glid_but, self.snap_segment_but, self.snap_point_but, self.snap_pcenter_but, 
                                                self.snap_plane_but, self.snap_live_but]
        self.snap_section_height = [but.height() for but in self.snap_section_but]
        self.snap_top.rightClicked.connect(lambda : self.toggle_ui(buttons=self.snap_section_but,  heights=self.snap_section_height))
        
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #コンストレインエリア
        self.constrain_top = make_flat_btton(name='Costrain', checkable=False, flat=False, text=text_col, h_min=top_h, bg=mid_color, hover=top_hover)
        #qt.change_button_color(self.constrain_top, textColor=text_col, bgColor=mid_color)
        self.main_layout.addWidget(self.constrain_top, vn, 0, 1 ,11)
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #parent
        self.parent_but = make_flat_btton(name = 'Parent', text=text_col, bg=hilite, checkable=False)
        self.parent_but.clicked.connect(self.parent_node)
        self.main_layout.addWidget(self.parent_but, vn, 0, 1 ,6)
        #cut
        self.cut_but = make_flat_btton(name = 'Cut', text=text_col, bg=hilite, checkable=False)
        self.main_layout.addWidget(self.cut_but, vn, 6, 1 ,5)
        self.cut_but.clicked.connect(self.cut_node)
        vn+=1
        #conscomp
        #self.cns_comp_but = make_flat_btton(name = 'CnsComp', text=mute_text, bg=immed)
        #self.main_layout.addWidget(self.cns_comp_but, vn, 0, 1 ,6)
        #self.cns_comp_but.setDisabled(True)#今のところ無効
        
        #--------------------------------------------------------------------------------
        #デストロイモードボタンを挿入
        self.destroy_but = make_flat_btton(name=destroy_name, text=text_col, bg=hilite)
        self.main_layout.addWidget(self.destroy_but, vn, 0, 1 ,6)
        self.destroy_but.clicked.connect(self.destroy_mode)
        #vn+=1
        #qt.change_button_color(self.cns_comp_but, textColor=120, bgColor=red, destroy=destroy_flag, dsColor=border_col)#今のところ無効
        #childcomp
        #設定はシーンのこのトランスフォームの維持を引き継ぐ
        child_comp = cmds.manipMoveContext('Move', q=True, pcp=True)
        self.child_comp_but = make_flat_btton(name = 'ChldComp', text=text_col, bg=hilite)
        self.child_comp_but.setChecked(child_comp)
        self.child_comp_but.clicked.connect(self.toggle_child_comp)
        self.main_layout.addWidget(self.child_comp_but, vn, 6, 1 ,5)
        vn+=1
        #--------------------------------------------------------------------------------
        #self.const_line_a = make_h_line()
        #self.main_layout.addWidget(self.const_line_a, vn, 0, 1 ,11)
        #vn+=1
        #一括操作のためにボタンをリスト化
        self.const_section_but = [self.parent_but, self.cut_but, self.destroy_but, self.child_comp_but]
        self.const_section_height = [but.height() for but in self.const_section_but]
        self.constrain_top.rightClicked.connect(lambda : self.toggle_ui(buttons=self.const_section_but,  heights=self.const_section_height))
        #--------------------------------------------------------------------------------
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #エディットエリア
        self.edit_top = make_flat_btton(name='Edit', checkable=False, flat=False, text=text_col, h_min=top_h, bg=mid_color, hover=top_hover)
        #qt.change_button_color(self.edit_top, textColor=text_col, bgColor=mid_color)
        self.main_layout.addWidget(self.edit_top, vn, 0, 1 ,11)
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        #Freeze
        self.freeze_but = make_flat_btton(name = 'Freeze', text=text_col, bg=hilite, checkable=False)
        self.freeze_but.clicked.connect(qt.Callback(self.freeze))
        self.main_layout.addWidget(self.freeze_but, vn, 0, 2 ,5)
        #Set作成
        self.group_but = make_flat_btton(name = 'Group', text=text_col, bg=hilite, checkable=False)
        self.group_but.clicked.connect(self.create_set)
        self.main_layout.addWidget(self.group_but, vn, 5, 2 ,5)
        self.plus_but = make_flat_btton(name = '+', text=text_col, bg=hilite, checkable=False, h_max=13, w_max=15, h_min=None)
        self.plus_but.clicked.connect(self.add_to_set)
        self.main_layout.addWidget(self.plus_but, vn, 10, 1 ,2)
        self.minus_but = make_flat_btton(name = '-', text=text_col, bg=hilite, checkable=False, h_max=13, w_max=15, h_min=None)
        self.minus_but.clicked.connect(self.remove_from_set)
        self.main_layout.addWidget(self.minus_but, vn+1, 10, 1 ,2)
        vn+=2
        #freeze
        self.freeze_m_but = make_flat_btton(name = 'FreezeM', text=text_col, bg=hilite, checkable=False)
        self.freeze_m_but.clicked.connect(qt.Callback(self.freeze_m))
        self.main_layout.addWidget(self.freeze_m_but, vn, 0, 1 ,5)
        #イミディエイトモード
        #設定はシーンのコンストラクションヒストリモードを引き継ぐ
        immed_mode = cmds.constructionHistory(q=True, toggle=True)
        if immed_mode:
            immed_mode = False
        else:
            immed_mode = True
        self.immed_but = make_flat_btton(name = 'Immed', text=text_col, bg=immed)
        self.immed_but.setChecked(immed_mode)
        self.immed_but.clicked.connect(self.toggle_immed)
        self.main_layout.addWidget(self.immed_but, vn, 5, 1 ,5)
        vn+=1
        #--------------------------------------------------------------------------------
        #self.edit_line_a = make_h_line()
        #self.main_layout.addWidget(self.edit_line_a, vn, 0, 1 ,11)
        #--------------------------------------------------------------------------------
        #vn+=1
        #一括操作のためにボタンをリスト化
        self.edit_section_but = [self.freeze_but, self.group_but, self.plus_but, self.minus_but, self.freeze_m_but, self.immed_but]
        self.edit_section_height = [but.height() for but in self.edit_section_but]
        self.edit_top.rightClicked.connect(lambda : self.toggle_ui(buttons=self.edit_section_but,  heights=self.edit_section_height))
        #Numpyモードデバッグ用
        #--------------------------------------------------------------------------------
        self.edit_line_a = make_h_line()
        self.main_layout.addWidget(self.edit_line_a, vn, 0, 1 ,11)
        vn+=1
        #計算時間--------------------------------------------------------------------------------
        self.culc_time_line = QLabel('- Select Culculation Mode -')
        qt.change_button_color(self.culc_time_line, textColor=menu_text, bgColor= ui_color)
        #self.culc_time_line = self.make_line_edit(text=string_col, bg=bg_col)
        self.main_layout.addWidget(self.culc_time_line, vn, 0, 1, 11)
        #self.culc_time_line.setText('Calculation time')
        #self.culc_time_line.setReadOnly(True)
        vn+=1
        self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        vn+=1
        #--------------------------------------------------------------------------------
        self.numpy = make_flat_btton(name='Numpy', text=text_col, bg=hilite, h_max=12, w_min=si_w, w_max=si_w)
        self.main_layout.addWidget(self.numpy, vn, 0, 1 ,6)
        self.standard = make_flat_btton(name = 'Standard', text=text_col, bg=hilite, h_max=12, w_min=maya_w, w_max=maya_w)
        self.main_layout.addWidget(self.standard, vn, 6, 1 ,5)
        self.np_group = QButtonGroup(self)
        self.np_group.addButton(self.numpy, 0)
        self.np_group.addButton(self.standard,  1)
        if np_flag:
            self.np_group.button(0).setChecked(True)
        else:
            self.np_group.button(1).setChecked(True)
        self.np_group.buttonClicked.connect(self.change_np_mode)
        vn+=1
        #self.main_layout.addWidget(self.make_ds_line(), vn, 0, 1 ,11)
        #vn+=1
        
        #ボタンをまとめて切り替えられるようにリストに
        #全部まとめてコネクトしておく※一括全ループだとidをかえられなかったので個別に
        #一括選択ボタンの挙動
        self.but_scale_all.clicked.connect(lambda:self.toggle_enable(mode=0, axis=3))
        self.but_scale_all.rightClicked.connect(lambda : self.select_xyz_line(mode=0, axis=4))#右クリックの挙動
        self.but_rot_all.clicked.connect(lambda:self.toggle_enable(mode=1, axis=3))
        self.but_rot_all.rightClicked.connect(lambda : self.select_xyz_line(mode=1, axis=4))#右クリックの挙動
        self.but_trans_all.clicked.connect(lambda:self.toggle_enable(mode=2, axis=3))
        self.but_trans_all.rightClicked.connect(lambda : self.select_xyz_line(mode=2, axis=4))#右クリックの挙動
        #右クリックをまとめてコネクト
        self.but_scale_x.rightClicked.connect(lambda : self.select_xyz_line(mode=0, axis=0))
        self.but_scale_y.rightClicked.connect(lambda : self.select_xyz_line(mode=0, axis=1))
        self.but_scale_z.rightClicked.connect(lambda : self.select_xyz_line(mode=0, axis=2))
        self.but_rot_x.rightClicked.connect(lambda : self.select_xyz_line(mode=1, axis=0))
        self.but_rot_y.rightClicked.connect(lambda : self.select_xyz_line(mode=1, axis=1))
        self.but_rot_z.rightClicked.connect(lambda : self.select_xyz_line(mode=1, axis=2))
        self.but_trans_x.rightClicked.connect(lambda : self.select_xyz_line(mode=2, axis=0))
        self.but_trans_y.rightClicked.connect(lambda : self.select_xyz_line(mode=2, axis=1))
        self.but_trans_z.rightClicked.connect(lambda : self.select_xyz_line(mode=2, axis=2))
        
        #self.but_scale_x.clicked.connect(lambda : self.keep_srt_select(mode=0))
        self.but_scale_all.clicked.connect(lambda : self.load_pre_selection(mode=4))
        #self.but_scale_x.clicked.connect(lambda : self.load_pre_selection(mode=4))
        self.but_rot_all.clicked.connect(lambda : self.load_pre_selection(mode=5))
        self.but_trans_all.clicked.connect(lambda : self.load_pre_selection(mode=6))
        select_scale.clicked.connect(lambda : self.load_pre_selection(mode=0))
        select_rot.clicked.connect(lambda : self.load_pre_selection(mode=1))
        select_trans.clicked.connect(lambda : self.load_pre_selection(mode=2))
        #スケールXYZボタンをコネクト
        self.but_scale_x.clicked.connect(lambda : self.set_disable(mode=0, but_id=0))
        self.but_scale_y.clicked.connect(lambda : self.set_disable(mode=0, but_id=1))
        self.but_scale_z.clicked.connect(lambda : self.set_disable(mode=0, but_id=2))
        select_scale.clicked.connect(lambda : self.set_disable(mode=0, but_id=3))
        self.but_scale_all.clicked.connect(lambda : self.set_disable(mode=0, but_id=4))
        for i, but in enumerate(self.scale_but_list):
            but.clicked.connect(lambda : set_active_mute(mode=0))
            but.clicked.connect(lambda : self.check_xyz(mode=0))
            if i == 3:
                continue
            but.clicked.connect(lambda : self.keep_srt_select(mode=0))
        #回転XYZボタンをコネクト
        self.but_rot_x.clicked.connect(lambda : self.set_disable(mode=1, but_id=0))
        self.but_rot_y.clicked.connect(lambda : self.set_disable(mode=1, but_id=1))
        self.but_rot_z.clicked.connect(lambda : self.set_disable(mode=1, but_id=2))
        select_rot.clicked.connect(lambda : self.set_disable(mode=1, but_id=3))
        self.but_rot_all.clicked.connect(lambda : self.set_disable(mode=1, but_id=4))
        for i, but in enumerate(self.rot_but_list):
            but.clicked.connect(lambda : set_active_mute(mode=1))
            but.clicked.connect(lambda : self.check_xyz(mode=1))
            if i == 3:
                continue
            but.clicked.connect(lambda : self.keep_srt_select(mode=1))
        #移動XYZボタンをコネクト
        self.but_trans_x.clicked.connect(lambda : self.set_disable(mode=2, but_id=0))
        self.but_trans_y.clicked.connect(lambda : self.set_disable(mode=2, but_id=1))
        self.but_trans_z.clicked.connect(lambda : self.set_disable(mode=2, but_id=2))
        select_trans.clicked.connect(lambda : self.set_disable(mode=2, but_id=3))
        self.but_trans_all.clicked.connect(lambda : self.set_disable(mode=2, but_id=4))
        for i, but in enumerate(self.trans_but_list):
            but.clicked.connect(lambda : set_active_mute(mode=2))
            but.clicked.connect(lambda : self.check_xyz(mode=2))
            if i == 3:
                continue
            but.clicked.connect(lambda : self.keep_srt_select(mode=2))
        self.all_srt_but_list = [self.scale_but_list, self.rot_but_list, self.trans_but_list]
        
        #マルチ選択フラグを設定
        self.multi_s_list = [False]*3
        self.multi_r_list = [False]*3
        self.multi_t_list = [False]*3
        self.all_multi_list = [self.multi_s_list, self.multi_r_list, self.multi_t_list]
        #マルチライン選択でフォーカス外れた時に暴発しないように予防線を張る
        self.multi_focus_list = copy.deepcopy(self.all_multi_list)
        self.pre_lines_text = [[[]]*3, [[]]*3, [[]]*3]
        self.pre_pre_lines_text = [[[]]*3, [[]]*3, [[]]*3]
        #print self.pre_lines_text
        
        self.create_job()
        sisidebar_sub.get_matrix()
        
        self.axis_list = ['_x', '_y', '_z', '_all']
        self.axis_attr_list = ['X', 'Y', 'Z']
        self.space_list = [', ws=True', ', ls=True', ', ls=True', ', os=True', ', ws=True', ', ls=True']
        self.srt_list = ['scale', 'rot', 'trans']
        global local_sids
        local_sids =[1, 2, 3, 5]
        
        self.select_from_current_context()
        #self.select_xyz_from_manip()
        
        scale_x.installEventFilter(self)
        scale_y.installEventFilter(self)
        scale_z.installEventFilter(self)
        rot_x.installEventFilter(self)
        rot_y.installEventFilter(self)
        rot_z.installEventFilter(self)
        trans_x.installEventFilter(self)
        trans_y.installEventFilter(self)
        trans_z.installEventFilter(self)
        
        self.load_filter_but()
        self.display_selection()
        self.change_button_group()
        
        for n in range(vn):
            self.main_layout.setRowStretch(n, 0)
        #一番下のラインが伸びるようにしてUIを上につめる
        self.main_layout.setRowStretch(vn, 1)
        
        if destroy_flag:
            self.destroy_but.setChecked(True)
            self.view_ds_line()
            self.destroy_mode(init_ui=False)
            #self.destroy_mode(init_ui=False)
    #デストロイモード用のラインを隠した状態で作っておく
    ds_line_list=[]
    def make_ds_line(self):
        ds_line = make_h_line(text=line_col, bg=line_col)
        self.ds_line_list.append(ds_line)
        ds_line.setVisible(False)
        return ds_line
    #デストロイモードに変形する
    def destroy_mode(self, init_ui=True):
        global destroy_flag
        global destroy_name
        global evolution_flag
        
        if self.destroy_but.isChecked():
            #print 'ds'
            evolution_flag = False
            destroy_name = 'Destroy'
            change_col = line_col
            destroy_flag = True
            msg = 'SI Side Bar : Activate Destroy mode'
        else:
            if self.ui_col == 0 and self.destroy_but.text() == 'Destroy':
                #print 'uc'
                evolution_flag = True
                destroy_name = 'Evolution'
                change_col = line_col
                destroy_flag = True
                msg = 'SI Side Bar : Activate Evolution mode'
            else:
                #print 'nm'
                evolution_flag = False
                destroy_name = 'Destroy'
                change_col = 128
                destroy_flag = False
                msg = 'SI Side Bar : Deactivate Destroy mode'
        if init_ui:
            self._initUI()
        self.destroy_but.setChecked(destroy_flag)
        #print evolution_flag
        self.change_ds_line()
        #print msg
        cmds.inViewMessage(amg=msg, pos='midCenterTop', fade=True, ta=0.75, a=0.5)
        #print 'destroy flag :', destroy_flag
        if destroy_flag:
            self.blinking_times = 0
            self.timer = QTimer()
            self.timer.start(20)
            self.timer.timeout.connect(self.destroy_blinking)
            self.bk_line_col = line_col
            self.bk_border_col = border_col
        else:
            try:
                self.timer.stop()
            except:
                pass
    blinking_times = 0
    add_flag = True
    def destroy_blinking(self):
        global all_flat_buttons
        global all_flat_button_palams
        if self.blinking_times > 80:
            self.add_flag = False
        if self.blinking_times < -30:
            self.add_flag = True
        if self.add_flag:
            self.bk_line_col = map(lambda a:a+1, self.bk_line_col )
            self.bk_border_col = map(lambda a:a+1, self.bk_border_col)
            self.blinking_times += 1
        else:
            self.bk_line_col = map(lambda a:a-1, self.bk_line_col )
            self.bk_border_col = map(lambda a:a-1, self.bk_border_col)
            self.blinking_times -= 1
        #print self.bk_line_col
        bk_col = map(lambda a:a if a < 255 else 255, self.bk_line_col )
        bk_col = map(lambda a:a if a > 100 else 100, bk_col )
        bk_bd_col = map(lambda a:a if a < 255 else 255, self.bk_border_col )
        bk_bd_col = map(lambda a:a if a > 100 else 100, bk_bd_col )
        for line in  line_list:
            qt.change_button_color(line, textColor=bk_col,  bgColor=bk_col)
        for but, pt in zip(all_flat_buttons, all_flat_button_palams):
            qt.change_button_color(but, textColor=pt[0], bgColor=pt[1], hiColor=pt[2], mode=pt[3], hover=pt[4], destroy=pt[5], dsColor=bk_bd_col)
        #print 'test'
            
        #qt.change_border_style(self.numpy)
    #既存のラインをデストロイカラーにする
    def change_ds_line(self):
        for line in line_list[1:]:
            if self.destroy_but.isChecked() or self.destroy_but.text()=='Evolution':
                change_col = line_col
            else:
                change_col = 128
            qt.change_button_color(line, textColor=change_col, bgColor=change_col)
            #sisidebar_sub.move_window()
        
    #隠されたデストロイラインを表示する
    def view_ds_line(self):
        if self.destroy_but.isChecked() or self.destroy_but.text()=='Evolution':
            visible=True
        else:
            visible=False
        return
        for ds_line in self.ds_line_list:
            ds_line.setVisible(visible)
    #オブジェクトのピボット位置を中心にそろえる
    pre_sel_for_cog = []
    spiv_list = []
    rpiv_list = []
    def setup_object_center(self):
        #以前のピボット位置に戻す
        for s, sp, rp in zip(self.pre_sel_for_cog, self.spiv_list, self.rpiv_list):
            if pm.nodeType(s) == 'joint':
                continue
            pm.xform(s+'.scalePivot', t=sp, os=True)
            pm.xform(s+'.rotatePivot', t=rp, os=True)
            
        if self.cog_but.isChecked():
            sel_obj = pm.ls(sl=True, l=True, type='transform')
            #pos_list = [pm.xform(s, q=True, t=True, ws=True) for s in sel_obj]
            self.pre_sel_for_cog = sel_obj
            self.spiv_list = [pm.xform(s+'.scalePivot', q=True, t=True, os=True) for s in sel_obj]
            self.rpiv_list = [pm.xform(s+'.rotatePivot', q=True, t=True, os=True) for s in sel_obj]
            if not sel_obj:
                return
            '''
            global np_flag
            #print 'np_flag', np_flag
            if np_flag:
                #print 'center in numpy'
                avr_pos = np.average(pos_list, axis=0).tolist()
            else:
                #print 'center in math'
                pos_sum = [0.0, 0.0, 0.0]
                for pos in pos_list:
                    pos_sum[0] += pos[0]
                    pos_sum[1] += pos[1]
                    pos_sum[2] += pos[2]
                avr_pos = map(lambda a: a/len(pos_list), pos_sum)
            '''
            #バウンディングボックスの中心に修正
            bBox = pm.exactWorldBoundingBox(sel_obj, ignoreInvisible=False)
            avr_pos = [(bBox[i]+bBox[i+3])/2 for i in range(3)]
            #print pos_list
            #print avr_pos
            #print 'set up center'
            for s in sel_obj:
                if pm.nodeType(s) == 'joint':
                    continue
                pm.xform(s+'.scalePivot', t=avr_pos, ws=True)
                pm.xform(s+'.rotatePivot', t=avr_pos, ws=True)
        
    #Numpy使うかどうかを変更
    def change_np_mode(self):
        global np_flag
        if self.np_group.checkedId() == 0:
            if not np_exist:
                print 'SI Side Bar : Numpy module does not exist'
                print 'SI Side Bar : Please install Numpy'
                cmds.inViewMessage(amg='<hl>Numpy module does not exist.</hl>\nPlease install Numpy.', pos='midCenterTop', fade=True, ta=0.75, a=0.5)
                self.np_group.button(1).setChecked(True)
                return
            print 'SI Side Bar : Set to Numpy Mode'
            np_flag = True
            sisidebar_sub.change_np_mode(mode=True)
        if self.np_group.checkedId() == 1:
            print 'SI Side Bar : Set to Standard Mode'
            np_flag = False
            sisidebar_sub.change_np_mode(mode=False)
    
    def toggle_ui(self, buttons=None, heights=None):
        #self.filter_but_list
        #i = 0
        if buttons[0].isVisible():
        #if buttons[0].height() != 0:
            for but in buttons:
                #i+=1
                #print i
                #but.setMaximumHeight(0)
                but.setVisible(False)
                
                #self.main_layout.removeWidget(but)
        else:
            for but, h in zip(buttons, heights):
                #i+=1
                #print i
                but.setVisible(True)
                #but.setMaximumHeight(h)
                #self.main_layout.addWidget(but)
        
    #セレクションフィルター状態をロード
    def load_filter_but(self):
        save_file = self.dir_path+'\\sisidebar_selection_filter_'+str(maya_ver)+'.json'
        if os.path.exists(save_file):#保存ファイルが存在したら
            with open(save_file, 'r') as f:
                save_data = json.load(f)
            all_flags = save_data['all_flags']
            for flag, but in zip(all_flags, self.filter_but_list):
                but.setChecked(flag)
            
    #テキスト検索タイプを全部かそれ以外で切り替える
    def set_filter_but(self, filter_type=''):
        #print 'set filter type :', filter_type
        if filter_type == 'All':
            if self.all_filter.isChecked():
                for filter_but in self.filter_but_list[1:]:
                    filter_but.setChecked(False)
            else:
                self.all_filter.setChecked(True)
        else:
            self.all_filter.setChecked(False)
        #全部オフならAllにチェックを入れる
        all_flags = [but.isChecked() for but in self.filter_but_list]
        if not any(all_flags):
            self.all_filter.setChecked(True)
            all_flags[0]=True
        #ボタンの状態を保存しておく
        save_file = self.dir_path+'\\sisidebar_selection_filter_'+str(maya_ver)+'.json'
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        with open(save_file, 'w') as f:
            json.dump({'all_flags':all_flags}, f)
            
    #矢印ボタンでピックウォークを実行
    def pick_walk(self, mode=''):
        #print 'pick_walk :', mode
        cmds.pickWalk(d=mode)
    #入力からコンポーネントを検索して選択
    def search_component(self):
        if self.init_flag:
            #print 'skip init search'
            self.init_flag = False#起動時判定フラグをさげるf
            return
        #print 'search_component'
        index_text = self.index_line.text()
        #print 'get index text :', index_text
        if index_text == '':
            #cmds.select(cl=True)
            self.index_line.clearFocus()
            return
        if not cmds.selectMode(q=True, co=True):
            cmds.select(cl=True)
            self.index_line.setText('')
            self.index_line.clearFocus()
            return
        index_list = index_text.split(' ')
        #print 'get index list', index_list
        #現在のモードを取っておく
        if cmds.selectType(q=True, pv=True):
            #sel_comp = cmds.polyListComponentConversion(sel_comp, tv=True)
            mode = 'vtx'
        elif cmds.selectType(q=True, pe=True):
            #sel_comp = cmds.polyListComponentConversion(sel_comp, te=True)
            mode = 'e'
        elif cmds.selectType(q=True, pf=True):
            #sel_comp = cmds.polyListComponentConversion(sel_comp, tf=True)
            mode = 'f'
        elif cmds.selectType(q=True, puv=True):
            #sel_comp = cmds.polyListComponentConversion(sel_comp, tf=True)
            mode = 'map'
        else:#マルチ選択モードの時は判断つかないのでとりあえずバーテックス
            mode = 'vtx'
        cmds.selectMode(o=True)
        sel_obj = cmds.ls(sl=True, tr=True)
        cmds.selectMode(co=True)
        selection_comp = []
        cmds.select(cl=True)
        for obj in sel_obj:
            for index in index_list:
                try:
                    cmds.select(obj+'.'+mode+'['+index+']', add=True)
                except:
                    pass
        self.index_line.clearFocus()
    #フィルタータイプ一覧
    select_type_list =  ['all', 'transform',  'joint', 'shape', None, None, 
                                'parentConstraint', 'pointConstraint', 'orientConstraint', 'scaleConstraint', 'aimConstraint', None]
                                
    #フローティング状態の時の検索窓の挙動を修正
    #検索窓がフォーカスとったとき暴発しないように以前の状態を保存
    pre_sel_text = None
    pre_pre_sel_text = None
    def keep_pre_search_line(self):
        if self.selection_line.text() == '':
            return
        if self.selection_line.text() != self.pre_pre_sel_text:
            self.pre_pre_sel_text = self.pre_sel_text
            self.pre_sel_text = self.selection_line.text()
        #print self.pre_pre_sel_text, self.pre_sel_text
            
    #入力からオブジェクトを検索して選択
    def search_node(self):
        #ダミーラインにフォーカス取らせて暴発防止
        self.dummy_line.setFocus()
        #print 'init flag', self.init_flag
        if self.init_flag:
            #print 'skip init search'
            self.init_flag = False#起動時判定フラグをさげる
            return
        search_text = self.selection_line.text()
        if self.pre_pre_sel_text == search_text:
            #print 'same text not search'
            return
        if not search_text or search_text.startswith('MULTI('):
            self.selection_line.clearFocus()
            return
        #print 'seach node form input :', self.selection_line.text()
        search_list = search_text.split(' ')
        #print 'multi search list :', search_list
        all_flags = [but.isChecked() for but in self.filter_but_list]
        if all_flags[0] == True:
            selection_node = cmds.ls(search_list, l=True)
        else:
            selection_node = []
            for filter_type, flag in zip(self.select_type_list[1:], all_flags[1:]):
                if not flag:
                    continue
                #print filter_type
                selection_node += cmds.ls(search_list, l=True, type=filter_type)
        #print 'get selection node :', selection_node
        #オブジェクトモードの時は新規選択、コンポーネントの場合は追加選択する
        if selection_node:
            if cmds.selectMode(q=True, o=True):
                cmds.select(selection_node, r=True)
            else:
                cmds.selectMode(o=True)
                pre_selection = cmds.ls(sl=True, l=True)
                cmds.selectMode(co=True)
                for node in selection_node:
                    if not node in pre_selection:
                        cmds.select(node, add=True)
        else:
            cmds.select(cl=True)
        self.selection_line.setText('')
        self.selection_line.clearFocus()
        self.display_selection()
    #選択オブジェクト情報を表示
    def display_selection(self):
        if cmds.selectMode(q=True, o=True):
            obj_list = cmds.ls(sl=True)
            comp_text = ''
            qt.change_button_color(self.selection_line, textColor=string_col, bgColor=bg_col)
            qt.change_button_color(self.index_line, textColor=gray_text, bgColor=bg_col)
        if cmds.selectMode(q=True, co=True):
            comp_list = cmds.ls(sl=True)
            obj_list = list(set([comp.split('.')[0] for comp in comp_list]))
            qt.change_button_color(self.selection_line, textColor=gray_text, bgColor=bg_col)
            qt.change_button_color(self.index_line, textColor=string_col, bgColor=bg_col)
        if not obj_list:
            disp_text = ''
        elif len(obj_list) > 1:
            disp_text = 'MULTI('+str(len(obj_list))+')'
        else:
            disp_text = obj_list[0].split('|')[-1]
        self.selection_line.setText(disp_text)
        if not cmds.selectMode(q=True, co=True):
            comp_text = ''
        elif not obj_list:
            comp_text = ''
        elif len(obj_list) > 1:
            comp_text = disp_text
        else:
            comp_text=[]
            for comp in comp_list:
                st = comp.find('[')+1
                ed = comp.find(']')
                comp_text.append(comp[st:ed])
            comp_text = ' '.join(comp_text)
        self.index_line.setText(comp_text)
        
    #グループセレクションボタンの状態を維持する
    def set_pre_sel_group_but(self, mode):
        global pre_sel_group_but
        pre_sel_group_but = mode
        
    global key_mod
    key_mod = None#1刻み
    mouse_flag = False
    def eventFilter(self, obj, event):
        global key_mod
        try:
            value = obj.text()
        except:
            return
        #print 'move event', obj, event
        #print 'obj :', obj, obj.text()
        #print 'ev type :', event.type()
        if event.type() == QEvent.MouseButtonPress:
            #print 'mouse clicked'
            self.first_move_flag = True
            self.pre_pos = map(float, [QCursor.pos().x(), QCursor.pos().y()*-1])
            self.pre_vec = [0, 1]
            self.count = 0
            self.mouse_flag = True
        if event.type() == QEvent.MouseButtonRelease:
            #print 'mouse released'
            self.mouse_flag = False
        if self.mouse_flag:
            if event.type() == QEvent.MouseMove:
                mod = event.modifiers()
                #print 'ev mod', mod
                if mod == Qt.ControlModifier:
                    key_mod = 'ctrl'#10刻み
                elif mod == Qt.ShiftModifier:
                    key_mod = 'shift'#0.1きざみ
                delta = self.mouse_vector()
                if value =='':
                    value = '0.0'
                #print 'mouse move delta :', delta
                if delta is not None:
                    self.save_pre_value()
                    self.culc_input_event(obj=obj, delta=delta, mod=key_mod, value=value)
        if event.type() == QEvent.FocusIn:
            self.keep_focused_text(text=obj.text())
        if event.type() == QEvent.KeyPress:
            key = event.key()
            #print 'ev key :', key
            mod = event.modifiers()
            #print 'ev mod', mod
            if mod == Qt.ControlModifier:
                key_mod = 'ctrl'#10刻み
            elif mod == Qt.ShiftModifier:
                key_mod = 'shift'#0.1きざみ
            #[]入力に対応
            if key == 91 or key ==93:
                if value =='':
                    value = '0.0'
                delta = key-92
                self.culc_input_event(obj=obj, delta=delta, mod=key_mod, value=value, mode='key')
            if key == 123 or key ==125:
                if value =='':
                    value = '0.0'
                delta = key-124
                self.culc_input_event(obj=obj, delta=delta, mod=key_mod, value=value, mode='key')
        if event.type() == QEvent.KeyRelease:
            key_mod = None#1刻み
        if event.type() == QEvent.Wheel:
            if value =='':
                value = '0.0'
            self.save_pre_value()
            delta = event.delta()
            delta /= abs(delta)
            #print 'wheel event :', event.delta()
            self.culc_input_event(obj=obj, delta=delta, mod=key_mod, value=value)
        return False
            
    #マウスの座標計算してぐるぐる入力を実現
    def mouse_vector(self):
        #一定間隔ごとに計算
        if self.first_move_flag:
            threshold = 40
        #print threshold
        else:
            threshold = mouse_count_ratio
        if self.count <=  threshold:
            self.count += 1
            return None
        else:
            self.count = 0
            self.cur_pos = map(float, [QCursor.pos().x(), QCursor.pos().y()*-1])
            
            if self.cur_pos != self.pre_pos:
                #print 'get mouse pos :', self.pre_pos, 'to', self.cur_pos
                #現在のベクトルを求める
                self.cur_vec = [self.cur_pos[0]-self.pre_pos[0], self.cur_pos[1]-self.pre_pos[1]]
                #print 'pre_vec', self.pre_vec, 'get_vec :', self.cur_vec
                #動き出しの符号を決定する
                if self.first_move_flag:
                    self.first_move_flag = False
                    self.operator = self.get_first_operator(self.cur_vec)
                #正規化して内積をとる
                self.angle = self.culc_angle(self.cur_vec, self.pre_vec)
                if self.angle >= 120:
                    #print 'reverse operator :', self.operator
                    self.operator *= -1
                #print 'get line operation :', self.operator
                self.pre_pos = self.cur_pos
                self.pre_vec = self.cur_vec
                delta = self.operator*mouse_gesture_ratio
                #print delta
                return delta
        return None
            
    def get_first_operator(self, a):
        #print 'get first operator'
        #value = a[0]*a[1]
        #SIの対角で符号反転するのが使いづらいので左右で一意に決める
        value = a[0]
        if value > 0:
            return 1.0
        else:
            return -1.0
    #2つのベクトルの角度を算出
    def culc_angle(self, a, b):
        dot = self.dot_poduct(a, b, norm=True)
        try:
            rad = math.acos(dot)
        except Exception as e:
            print e.message
            print 'Arc cos error : dot ', dot
            dot = round(dot, 0)
            rad = math.acos(dot)
        #print u'ラジアン :', rad
        angle = rad*180/math.pi
        #print u'角度 :', angle
        return angle
    #内積とる
    def dot_poduct(self, a, b, norm=False):
        if norm:#正規化オプション
            a = self.normalize(a)
            b = self.normalize(b)
        dot = (a[0]*b[0])+(a[1]*b[1])
        #print u'内積 :', dot
        return dot
    #ベクトルを正規化して戻す
    def normalize(self, a):
        length = self.get_length(a)
        return [a[0]/length, a[1]/length]
    #長さを出す
    def get_length(self, a):
        return math.sqrt(a[0]**2+a[1]**2)
        
            
    #入力を計算して返す
    def culc_input_event(self,obj=None, delta=0, mod=None, value=0, mode='gesture'):
        #print value
        if obj is None:
            return
        try:
            if value == '':
                return
            if mod is None:
                add = 1.0 * delta
            if mod == 'ctrl':
                add = 10.0 * delta
            if mod == 'shift':
                add = 0.1 * delta
            value = str(float(value)+add)
        except Exception as e:
            print 'Input Event Culicurationo Errot:', e.message
            print 'value :', value, 'delta :', delta, 'mod :',mod
            value =  ''
        #print event.orient()
        #print value
        #ホイール時は強制的にフォーカス取ってキーイベントを有効にする
        
        #キー入力の場合は入力終了後にイベントを発生させるためジョブを作る
        if mode == 'key':
            input_job = cmds.scriptJob(ro=True, e=("idle", lambda : self.re_input_value(obj=obj, value=value)), protected=True)
        elif mode == 'gesture':
            self.re_input_value(obj=obj, value=value)
    
    #[]入力の場合はテキストがおかしくなるので入力後にジョブで実行
    def re_input_value(self, obj=None, value=None):
        obj.setFocus()#先にフォーカスとること！じゃないと入力反映が遅れる
        obj.setText(str(value))
        #print 'set_text :', value
        self.apply_wheel_value()
        
    global pre_text_value
    pre_text_value = [['', '', ''], ['', '', ''], ['', '', '']]
    #事前に入力値を取得しておく
    def save_pre_value(self):
        for i, m_line in enumerate(self.all_xyz_list):
            for j, a_line in enumerate(m_line):
                pre_text_value[i][j] = a_line.text()
        #print pre_text_value
    #ホイール入力を適用
    def apply_wheel_value(self):
        for i, m_line in enumerate(self.all_xyz_list):
            for j, a_line in enumerate(m_line):
                value = a_line.text()
                #print value, pre_text_value[i][j]
                #以前の入力と違っていたらフォーカス外さないモードでSRT実行
                #print 'compare pre_text :', pre_text_value[i][j], 'value :', value, 'mode', i
                if pre_text_value[i][j] != value:
                    if i == 0:
                        self.scaling(text=value, axis=j, focus=False)
                    if i == 1:
                        self.rotation(text=value, axis=j, focus=False)
                    if i == 2:
                        self.translation(text=value, axis=j, focus=False)
                    self.keep_focused_text(value)
                #self.keep_pre_line_text(text=value, current=(i,  j))
    #入力後の暴発を防ぐためにフォーカスを外す
    def out_focus(self):
        #print 'out_forcus', input_srt_id, input_line_id
        #タブ移動、マルチライン入力に対応するためフォーカス外すラインを限定する
        global input_srt_id#フォーカス外すラインを限定する
        global input_line_id#フォーカス外すラインを限定する
        
        for i, m_line in enumerate(self.all_xyz_list):
            if i != input_srt_id:
                continue
            for j, a_line in enumerate(m_line):
                #print a_line.text()
                #print a_line.hasFocus()
                if j != input_line_id:
                    continue
                if a_line.hasFocus():
                    a_line.clearFocus()
        #print 'focus out line edit'
        
    #コンテキスト側からの変更をUIにまとめて反映する
    def check_ui_button(self):
        snap_mode = cmds.snapMode(q=True, grid=True)
        self.snap_glid_but.setChecked(snap_mode)
        snap_mode = cmds.snapMode(q=True, curve=True)
        self.snap_segment_but.setChecked(snap_mode)
        snap_mode = cmds.snapMode(q=True, point=True)
        self.snap_point_but.setChecked(snap_mode)
        snap_mode = cmds.snapMode(q=True, meshCenter=True)
        self.snap_pcenter_but.setChecked(snap_mode)
        snap_mode = cmds.snapMode(q=True, viewPlane=True)
        self.snap_plane_but.setChecked(snap_mode)
        
        immed_mode = cmds.constructionHistory(q=True, toggle=True)
        if immed_mode:
            immed_mode = False
        else:
            immed_mode = True
        self.immed_but.setChecked(immed_mode)
        
        child_comp = cmds.manipMoveContext('Move', q=True, pcp=True)
        self.child_comp_but.setChecked(child_comp)
        
        prop = cmds.softSelect(q=True, softSelectEnabled=True)
        self.prop_but.setChecked(prop)
        #self.toggle_prop()
        
        sym = cmds.symmetricModelling(q=True, symmetry=True)
        if maya_ver >= 2015:
            topo = cmds.symmetricModelling(q=True, topoSymmetry=True) 
        else:
            topo = False
        if not sym and not topo:
            sym = False
        else:
            sym = True
        self.sym_but.setChecked(sym)
        #self.toggle_sym()
        target_tool_list = ['scaleSuperContext', 'RotateSuperContext', 'moveSuperContext', 'selectSuperContext']
        current_tool = cmds.currentCtx()
        if current_tool in target_tool_list:
            mode = current_tool.index(current_tool)
            self.get_init_space()
            if mode < 3:
                mode+=4
            self.load_pre_selection(mode=mode)
    
    def show_ref_menu(self):
        #print 'show ref menus'
        ref_menus = QMenu()
        qt.change_button_color(ref_menus, textColor=menu_text, bgColor=menu_bg, hiText=menu_high_text, hiBg=menu_high_bg, mode='window')
        action0 = ref_menus.addAction('Use Current Reference')
        action0.triggered.connect(lambda : space_group.button(4).setChecked(True))
        action1 = ref_menus.addAction('Pick New Reference')
        action1.triggered.connect(lambda : self.pick_reference(mode='current'))
        ref_menus.addSeparator()#分割線追加
        action2 = ref_menus.addAction('Pick Object Reference')
        action2.triggered.connect(lambda : self.pick_reference(mode='object'))
        action3 = ref_menus.addAction('Pick Point Reference')
        action3.triggered.connect(lambda : self.pick_reference(mode='vertex'))
        action4 = ref_menus.addAction('Pick Edge Reference')
        action4.triggered.connect(lambda : self.pick_reference(mode='edge'))
        action5 = ref_menus.addAction('Pick Polygon Reference')
        action5.triggered.connect(lambda : self.pick_reference(mode='face'))
        cursor = QCursor.pos()
        ref_menus.exec_(cursor)
        
    def pick_reference(self, mode=''):
        #cmds.inViewMessage( amg=u"<hl>ウェイトを取得したいポリゴン</hl>を選んでください.", pos='midCenterTop', fade=True )
        #グループ変更、状態保存、コンテキスト変更、再計算する
        space_group.button(4).setChecked(True)
        self.keep_srt_select(mode=3)
        self.chane_context_space()
        sisidebar_sub.get_matrix()
        #-----------------------------------------------
        self.keep_srt_select(mode=3)
        pre_sel = cmds.ls(sl=True, l=True)
        pre_mode = sisidebar_sub.pre_pro_reference(sel=pre_sel)
        if mode == 'current':
            mode = pre_mode
        if mode == 'object':
            cmds.selectMode(o=True)
        else:
            cmds.selectMode(o=True)
            cmds.selectMode(co=True)
            if mode == 'vertex':
                cmds.selectType(pv=1, smu=0, smp=1, pf=0, pe=0, smf=0, sme=0, puv=0)
            if mode == 'edge':
                cmds.selectType(pv=0, smu=0, smp=0, pf=0, pe=1, smf=0, sme=1, puv=0)
            if mode == 'face':
                cmds.selectType(pv=0, smu=0, smp=0, pf=1, pe=0, smf=0, sme=1, puv=0)
        cmds.select(cl=True)
        pick_ref_ctx = cmds.scriptCtx( title='Select Reference',
                            totalSelectionSets=3,
                            cumulativeLists=True,
                            expandSelectionList=True,
                            tct="edit",
                            setNoSelectionPrompt='Select reference object or component'
                            )
        cmds.setToolTo(pick_ref_ctx)
        ref_job = cmds.scriptJob(ro=True, ct=["SomethingSelected",lambda : sisidebar_sub.set_reference(mode=mode)], protected=True)
        
    def change_ui_color(self, mode=0):
        global destroy_flag
        #destroy_flag = False
        self.ui_col = mode
        #print mode
        self.dockCloseEventTriggered()
        self._initUI()
        #print destroy_flag
        if destroy_flag:
            self.destroy_but.setChecked(True)
            self.destroy_mode()
        #self.close()
        #Option()
    #コンテキストメニューとフローティングメニューを再帰的に作成する
    def create_f_trans_menu(self):#ウィンドウ切り離しの場合はインスタンスを別にして再作成
        top_f_menus = self.create_trans_menu(add_float=False)
        global transform_manu_window
        try:
            transform_manu_window.close()
        except:
            pass
        transform_manu_window = FloatingWindow(menus=top_f_menus, offset=transform_offset)
        
    def create_trans_menu(self, add_float=True):
        self.top_menus = QMenu(self.transfrom_top)
        qt.change_button_color(self.top_menus, textColor=menu_text, bgColor=menu_bg, hiText=menu_high_text, hiBg=menu_high_bg, mode='window')
        if add_float:#切り離しウィンドウメニュー
            action10 = self.top_menus.addAction(u'-----------------------------------------------------✂----')
            action10.triggered.connect(self.create_f_trans_menu)
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Transform Preference...',
                                ja=u'変換設定')
        action25 = QAction(mag.output(), self.top_menus, icon=QIcon(image_path+'setting'))
        action25.setToolTip('test')
        self.top_menus.addAction(action25)
        action25.triggered.connect(lambda : self.pop_option_window(mode='transform'))
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Reset Actor to Bind Pose',
                                ja=u'リセットアクター/バインドポーズに戻す')
        action12 = self.top_menus.addAction(mag.output())
        action12.triggered.connect(transform.reset_actor)
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Transfer Rotate to Joint Orient',
                                ja=u'回転をジョイントの方向に変換')
        action17 = self.top_menus.addAction(mag.output())
        action17.triggered.connect(qt.Callback(lambda : transform.set_joint_orient(reset=True)))
        mag = lang.Lang(en='Transfer Joint Orient to Rotate',
                                ja=u'ジョイントの方向を回転に変換')
        action18 = self.top_menus.addAction(mag.output())
        action18.triggered.connect(qt.Callback(lambda : transform.set_joint_orient(reset=False)))
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Reset All Transforms',
                                ja=u'すべての変換をリセット')
        action13 = self.top_menus.addAction(mag.output())
        action13.triggered.connect(qt.Callback(lambda : transform.reset_transform(mode='all')))
        mag = lang.Lang(en='Reset Scaling',
                                ja=u'スケーリングのリセット')
        action14 = self.top_menus.addAction(mag.output())
        action14.triggered.connect(qt.Callback(lambda : transform.reset_transform(mode='scale')))
        mag = lang.Lang(en='Reset Rotation',
                                ja=u'回転のリセット')
        action15 = self.top_menus.addAction(mag.output())
        action15.triggered.connect(qt.Callback(lambda : transform.reset_transform(mode='rot')))
        mag = lang.Lang(en='Reset Translation',
                                ja=u'移動のリセット')
        action16 = self.top_menus.addAction(mag.output())
        action16.triggered.connect(qt.Callback(lambda : transform.reset_transform(mode='trans')))
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Freeze All Transforms',
                                ja=u'すべての変換をフリーズ')
        action0 = self.top_menus.addAction(mag.output())
        action0.triggered.connect(qt.Callback(lambda : transform.freeze_transform(mode='all')))
        mag = lang.Lang(en='Freeze Scaling',
                                ja=u'スケーリングのフリーズ')
        action1 = self.top_menus.addAction(mag.output())
        action1.triggered.connect(qt.Callback(lambda : transform.freeze_transform(mode='scale')))
        mag = lang.Lang(en='Freeze Rotation',
                                ja=u'回転のフリーズ')
        action2 = self.top_menus.addAction(mag.output())
        action2.triggered.connect(qt.Callback(lambda : transform.freeze_transform(mode='rot')))
        mag = lang.Lang(en='Freeze Translation',
                                ja=u'移動のフリーズ')
        action3 = self.top_menus.addAction(mag.output())
        action3.triggered.connect(qt.Callback(lambda : transform.freeze_transform(mode='trans')))
        mag = lang.Lang(en='Freeze Joint Orientation',
                                ja=u'ジョイントの方向のフリーズ')
        action4 = self.top_menus.addAction(mag.output())
        action4.triggered.connect(qt.Callback(lambda : transform.freeze_transform(mode='joint')))
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Round All Transform / Decimal'+str(round_decimal_value),
                                ja=u'すべての変換を丸める / 桁数'+str(round_decimal_value))
        self.action20 = self.top_menus.addAction(mag.output())
        self.action20.triggered.connect(qt.Callback(lambda : transform.round_transform(mode='all', digit=round_decimal_value)))
        mag = lang.Lang(en='Round Scaling / Decimal'+str(round_decimal_value),
                                ja=u'スケーリングを丸める / 桁数'+str(round_decimal_value))
        self.action21 = self.top_menus.addAction(mag.output())
        self.action21.triggered.connect(qt.Callback(lambda : transform.round_transform(mode='scale', digit=round_decimal_value)))
        mag = lang.Lang(en='Round Rotation / Decimal'+str(round_decimal_value),
                                ja=u'回転を丸める / 桁数'+str(round_decimal_value))
        self.action22 = self.top_menus.addAction(mag.output())
        self.action22.triggered.connect(qt.Callback(lambda : transform.round_transform(mode='rotate', digit=round_decimal_value)))
        mag = lang.Lang(en='Round Translation / Decimal'+str(round_decimal_value),
                                ja=u'移動値を丸める / 桁数'+str(round_decimal_value))
        self.action23 = self.top_menus.addAction(mag.output())
        self.action23.triggered.connect(qt.Callback(lambda : transform.round_transform(mode='translate', digit=round_decimal_value)))
        mag = lang.Lang(en='Round Joint Orient / Decimal'+str(round_decimal_value),
                                ja=u'ジョイントの方向を丸める / 桁数'+str(round_decimal_value))
        self.action24 = self.top_menus.addAction(mag.output())
        self.action24.triggered.connect(qt.Callback(lambda : transform.round_transform(mode='jointOrient', digit=round_decimal_value)))
        self.round_action_list = [self.action20, self.action21, self.action22, self.action23, self.action24]
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Match All Transform',
                                ja=u'すべての変換の一致')
        action6 = self.top_menus.addAction(mag.output())
        action6.triggered.connect(qt.Callback(lambda : transform.match_transform(mode='all')))
        mag = lang.Lang(en='Match Scaling',
                                ja=u'スケーリングの一致')
        action7 = self.top_menus.addAction(mag.output())
        action7.triggered.connect(qt.Callback(lambda : transform.match_transform(mode='scale')))
        mag = lang.Lang(en='Match Rotation',
                                ja=u'回転の一致')
        action8 = self.top_menus.addAction(mag.output())
        action8.triggered.connect(qt.Callback(lambda : transform.match_transform(mode='rotate')))
        mag = lang.Lang(en='Match Translation',
                                ja=u'移動値の一致')
        action9 = self.top_menus.addAction(mag.output())
        action9.triggered.connect(qt.Callback(lambda : transform.match_transform(mode='translate')))
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        mag = lang.Lang(en='Move Center to Selection (All selection)',
                                ja=u'センターを選択に移動（すべての選択）')
        action5 = self.top_menus.addAction(mag.output())
        action5.triggered.connect(qt.Callback(transform.move_center2selection))
        mag = lang.Lang(en='Move Center to Selection (Each object)',
                                ja=u'センターを選択に移動（オブジェクトごと）')
        action11 = self.top_menus.addAction(mag.output())
        action11.triggered.connect(qt.Callback(transform.move_center_each_object))
        self.top_menus.addSeparator()#分割線追加
        #----------------------------------------------------------------------------------------------------
        self.trs_setting_path = self.dir_path+'\\sisidebar_trs_data_'+str(maya_ver)+'.json'
        #print self.trs_setting_path
        
        self.cp_mag = lang.Lang(en=u'Collapse Point For Snapping/Absolute Translation',
                                ja=u'スナップ移動/絶対移動でポイントを集約')
        if add_float:
            self.action19 = self.top_menus.addAction(self.cp_mag.output())
            if cp_abs_flag:
                self.action19.setIcon(QIcon(image_path+self.check_icon))
            else:
                self.action19.setIcon(QIcon(None))
            self.action19.triggered.connect(self.toggle_cp_absolute)
        else:
            self.f_action19 = self.top_menus.addAction(self.cp_mag.output())
            if cp_abs_flag:
                self.f_action19.setIcon(QIcon(image_path+self.check_icon))
            else:
                self.f_action19.setIcon(QIcon(None))
            self.f_action19.triggered.connect(self.toggle_cp_absolute)
        #Mayaのマニプハンドルを乗っ取る設定
        self.hl_mag = lang.Lang(en=u'Force Side Bar axis selection status',
                                ja=u'サイドバーの軸選択状態を優先する')
        if add_float:
            self.action20 = self.top_menus.addAction(self.hl_mag.output())
            if ommit_manip_link:
                self.action20.setIcon(QIcon(image_path+self.check_icon))
            else:
                self.action20.setIcon(QIcon(None))
            self.action20.triggered.connect(self.toggle_manip_priority)
        else:
            self.f_action20 = self.top_menus.addAction(self.hl_mag.output())
            if ommit_manip_link:
                self.f_action20.setIcon(QIcon(image_path+self.check_icon))
            else:
                self.f_action20.setIcon(QIcon(None))
            self.f_action20.triggered.connect(self.toggle_manip_priority)
        #self.top_menus.setTearOffEnabled(True)#ティアオフ可能にもできる
        return self.top_menus
        
    #マニプ優先設定を切り替える
    def toggle_manip_priority(self):
        global ommit_manip_link
        #print 'pre_cp_abs_flag', cp_abs_flag
        if ommit_manip_link:
            ommit_manip_link = False
        else:
            ommit_manip_link = True
        self.save_transform_setting()
        if ommit_manip_link:
            set_icon = QIcon(image_path+self.check_icon)
        else:
            set_icon = QIcon(None)
        try:
            self.f_action20.setIcon(set_icon)
        except Exception as e:
            pass
        top_menus = self.create_trans_menu()
        self.transfrom_top.setMenu(top_menus)
        
        
    #絶対値に移動を切り替える
    def toggle_cp_absolute(self):
        global cp_abs_flag
        #print 'pre_cp_abs_flag', cp_abs_flag
        if cp_abs_flag:
            cp_abs_flag = False
        else:
            cp_abs_flag = True
        self.save_transform_setting()
        if cp_abs_flag:
            set_icon = QIcon(image_path+self.check_icon)
        else:
            set_icon = QIcon(None)
        try:
            self.f_action19.setIcon(set_icon)
        except Exception as e:
            pass
        top_menus = self.create_trans_menu()
        self.transfrom_top.setMenu(top_menus)
        
    #絶対値に移動を切り替える
    def toggle_action_check(self, item_id, flags, flag_str):
        global cp_abs_flag
        global ommit_manip_link
        try:
            exec('f_item = self.f_action'+str(item_id))
        except Exception as e:
            print e.message
        exec('m_item = self.action'+str(item_id))
            
        #print 'pre_cp_abs_flag', cp_abs_flag
        #print flags
        if flags:
            exec(flag_str+' = False')
        else:
            exec(flag_str+' = True')
        exec('print '+flag_str)
        self.save_transform_setting()
        if flags:
            try:
                f_item.setIcon(QIcon(image_path+self.check_icon))
            except Exception as e:
                print e.message
                pass
            top_menus = self.create_trans_menu()
            self.transfrom_top.setMenu(top_menus)
        else:
            try:
                f_item.setIcon(QIcon(None))
            except Exception as e:
                print e.message
                pass
            top_menus = self.create_trans_menu()
            self.transfrom_top.setMenu(top_menus)
        #print 'cp_abs_flag', cp_abs_flag
    
    def load_transform_setting(self):
        global cp_abs_flag
        global ommit_manip_link
        if os.path.isfile(self.trs_setting_path):#保存ファイルが存在したら
            with open(self.trs_setting_path, 'r') as f:
                save_data = json.load(f)
            try:
                cp_abs_flag = save_data['cp_abs']
                ommit_manip_link = save_data['manip_link']
            except:
                cp_abs_flag = False
                ommit_manip_link = False
                
    def save_transform_setting(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        save_data = {}
        save_data['cp_abs'] = cp_abs_flag
        save_data['manip_link'] = ommit_manip_link
        with open(self.trs_setting_path, 'w') as f:
            json.dump(save_data, f)
            
    #リセットアクターバインドポーズを実行
    def reset_actor(self):
        joint_animation.reset_actor()
    #ダグノードの選択フィルタリングを変更する
    def select_filter_mode(self, mode=0):
        filters = ['All', "Marker", "Joint", "Surface", "Curve", "Deformer", "Other"]
        filter_coms = ["Marker", "Joint", "Curve", "Surface", "Deformer", "Dynamic", "Rendering", "Other"]
        for f in filter_coms:
            if filters[mode] == 'All':
                mel.eval('setObjectPickMask '+f+' true;')
                continue
            if f == filters[mode]:
                mel.eval('setObjectPickMask '+f+' true;')
            else:
                mel.eval('setObjectPickMask '+f+' false;')
        
    #コンテキストが変更されたらui上のコンテキストも移動する
    def set_select_context(self):
        if select_but.isChecked():
            self.pre_context = cmds.currentCtx() 
            select_but.setIcon(QIcon(image_path+self.sel_on_icon))
            cmds.setToolTo('selectSuperContext')
            self.set_disable(mode=None, but_id=None)
            #self.cog_but.setDisabled(True)
            #qt.change_button_color(self.cog_but, textColor=120, bgColor=hilite)
        else:
            select_group_but.setChecked(False)
            #self.cog_but.setDisabled(False)
            #qt.change_button_color(self.cog_but, textColor=text_col, bgColor=hilite)
            #qt.change_button_color(self.cog_but, textColor=text_col, bgColor=ui_color, mode='button')
        #セレクトボタンが解除された時の挙動、以前選択のコンテキストが無い場合はセレクトモードから動かない
        #ある時はいぜんのコンテキストに移行
        #print cmds.currentCtx() 
        if cmds.currentCtx() != 'selectSuperContext':#別のツールに移行する場合は抜ける
            select_but.setIcon(QIcon(image_path+self.sel_off_icon))
            return
        if not select_but.isChecked():
            #print 'pre context : ', self.pre_context
            if self.pre_context == 'selectSuperContext':
                select_but.setChecked(True)
            else:
                select_but.setIcon(QIcon(image_path+self.sel_off_icon))
                cmds.setToolTo(self.pre_context)
        
    #ライブサーフェイススナップを設定する
    def make_live_snap(self):
        sel = cmds.ls(sl=True)
        shapes = cmds.listRelatives(sel, s=True, f=True)
        #print 'Get Shape :', shapes
        if shapes:
            for s in shapes:
                cmds.makeLive(s)
        else:
            cmds.makeLive()
        
    def freeze(self):
        freeze.freeze()
    
    def freeze_m(self):
        freeze.main(pop_zero_poly=True)
        
    def add_to_set(self):
        sets.add_to_set_members()
        
    def remove_from_set(self):
        sets.remove_set_members()
    
    #親子付け切り離し、KTG_Modelルートがあればそのしたへ、無い場合はワールド直下へ。
    def cut_node(self):
        selection = pm.ls(sl=True, l=True)
        for sel in selection:
            p_node = sel
            type = pm.nodeType(sel)
            if type != 'transform' and type != 'joint':
                continue
            roop = 0
            while True:
                #print p_node
                p_node = pm.listRelatives(p_node, p=True)
                if pm.nodeType(p_node) == 'KTG_ModelRoot':
                    pm.parent(sel, p_node)
                    break
                if not p_node:
                    pm.parent(sel, w=True)
                    break
                roop += 1
                if roop > 300:
                    #print 'too many roop :'
                    break
        pm.select(selection, r=True)
        
    def parent_node(self):
        try:
            cmds.parent()
        except Exception as e:
            print e.message
            pass
            
    def toggle_prop(self):
        if self.prop_but.isChecked():
            self.sym_but.setChecked(False)
            self.toggle_sym()
            cmds.softSelect(e=True, softSelectEnabled=True)
        else:
            cmds.softSelect(e=True, softSelectEnabled=False)
            
    def get_pre_about(self):
        global pre_about
        pre_about = cmds.symmetricModelling(q=True, a=True)
            
    def toggle_sym(self):
        if self.sym_but.isChecked():
            self.prop_but.setChecked(False)
            self.toggle_prop()
            try:
                #print pre_about
                cmds.symmetricModelling(e=True, symmetry=True, about=pre_about)
                if 'sym_window' in globals():
                    if pre_about == 'world':
                        sym_window.sym_group.button(1).setChecked(True)
                    if pre_about == 'object':
                        sym_window.sym_group.button(2).setChecked(True)
                    if pre_about == 'topo':
                        sym_window.sym_group.button(3).setChecked(True)
            except:
                cmds.symmetricModelling(e=True, symmetry=True, about='world')
                if 'sym_window' in globals():
                    sym_window.sym_group.button(1).setChecked(True)
                
            #cmds.symmetricModelling(e=True, topoSymmetry=0) 
        else:
            cmds.symmetricModelling(e=True, symmetry=False)
            if maya_ver >= 2015:
                cmds.symmetricModelling(e=True, topoSymmetry=False)
            if 'sym_window' in globals():
                sym_window.sym_group.button(0).setChecked(True)
        
    def pop_option_window(self, mode='prop'):
        #print 'pop up prop option window'
        dock_dtrl = self.parent()
        #pos = dock_dtrl.mapToGlobal(QPoint(0, 0))
        if mode == 'prop':
            global prop_option
            try:
                prop_option.close()
            except:
                pass
            prop_option = PropOption()
        if mode == 'sym':
            global sym_window
            try:
                sym_window.close()
            except:
                pass
            sym_window = SymOption()
        if mode == 'filter':
            global filter_window
            try:
                filter_window.close()
            except:
                pass
            filter_window = FilterOption()
            for but in self.filter_but_list:
                but.clicked.connect(filter_window.load_filter_but)
        if mode == 'transform':
            global trs_setting_window
            try:
                trs_setting_window.close()
            except:
                pass
            trs_setting_window = TransformSettingOption()
            
        
    #Child_Compを切り替え
    def toggle_child_comp(self):
        child_comp = self.child_comp_but.isChecked()
        cmds.manipMoveContext('Move', e=True, pcp=child_comp)
        cmds.manipRotateContext('Rotate', e=True, pcp=child_comp)
        cmds.manipScaleContext('Scale', e=True, pcp=child_comp)
        
    #スナップ設定をトグル
    def toggle_snap(self):
        pass
        
    #セットの作成
    def create_set(self):
        #print 'create set :'
        result = str(cmds.promptDialog(title="Creat Set", 
            cancelButton="Cancel", defaultButton="OK", 
            button=["OK", 
                "Cancel"], 
            message="Input Set Name", 
            dismissString="Cancel"))
        if result == "OK":
            name = cmds.promptDialog(query=1, text=1)
            cmds.sets(n=name)
                
    #コンストラクションヒストリのオンオフ
    def toggle_immed(self):
        immed_mode = self.immed_but.isChecked()
        if immed_mode:
            immed_mode = False
        else:
            immed_mode = True
        #print 'toggle immed :', immed_mode
        set = cmds.constructionHistory(toggle=immed_mode)
        selection = cmds.ls(sl=True, l=True)
        for sel in selection:
            try:
                cmds.sets(sel, add=set)
            except Exception as e:
                print e.message
                pass
                
    #アトリビュートのロック状態を調べてUIに反映する
    attr_lock_flag_list = [[None, None, None], [None, None, None], [None, None, None]]
    all_attr_list = [['.sx', '.sy', '.sz'], ['.rx', '.ry', '.rz'], ['.tx', '.ty', '.tz'],[]]
    def attribute_lock_state(self, mode=0, check_only=False):
        #print 'check attribute lock', mode
        if mode == 3:#モード3なら全部処理する
            #print 'check all lines'
            self.attribute_lock_state(mode=0, check_only=True)
            self.attribute_lock_state(mode=1, check_only=True)
            self.attribute_lock_state(mode=2, check_only=True)
            return
        lock_state_list = [None, None, None]
        all_lock_flag = True
        attr_list = self.all_attr_list[mode]
        selection = cmds.ls(sl=True, l=True)
        for s in selection:
            for i, attr in enumerate(attr_list):
                try:
                    lock_flag = cmds.getAttr(s+attr, lock=True)
                except Exception as e:
                    #print e.message
                    lock_flag = False
                #print lock_flag, s+attr
                #一個でもロックされてたら全解除
                if lock_flag:
                    if not check_only:
                        self.toggle_lock_attr(mode=mode, state=False, objects=selection)
                        check_key_anim()
                        return
                #前回の状態と比較して、ロック状態が違えばマルチフラグを立てる
                pre_lock_flag = lock_state_list[i]
                if pre_lock_flag is None:
                    lock_state_list[i] = lock_flag
                    continue
                else:
                    if pre_lock_flag != lock_flag:
                        lock_state_list[i] = 'multi'
        #チェックモードでなければロック実行
        if selection:
            if check_only:
                #チェックモードの時はラインカラー変換のみ
                self.change_lock_color(mode=mode, lock_state_list=lock_state_list)
            else:
                self.toggle_lock_attr(mode=mode, state=True, objects=selection)
        else:
            self.change_lock_color(mode=mode, lock_state_list=[False]*3)
        check_key_anim()
            
    def toggle_lock_attr(self, mode=0, state=False, objects=None):
        attr_list = self.all_attr_list[mode]
        for s in objects:
            for i, attr in enumerate(attr_list):
                cmds.setAttr(s+attr, lock=state)
        state_list = [state]*3
        self.change_lock_color(mode=mode, lock_state_list=state_list)
        
    def change_lock_color(self, mode=0, lock_state_list=None):
        lines_list = self.all_xyz_list[mode]
        for line, lock_state in zip(lines_list, lock_state_list):
            if lock_state is True:
                qt.change_button_color(line, textColor=locked_text_col, bgColor=locked_bg_col )
            elif lock_state is False:
                qt.change_button_color(line, textColor=string_col, bgColor=bg_col)
            else:
                qt.change_button_color(line, textColor=locked_text_col, bgColor=multi_lock_bg)
        #マルチライン入力後にリセットするためにステイトを保存しておく
        self.attr_lock_flag_list[mode] = lock_state_list[:]
                
    #スケール入力をオブジェクトに反映
    def scaling(self, text='', axis=0, focus=True):
        global world_str_mode
        global world_str_axis
        world_str_mode=0
        world_str_axis=axis
        #print '/*/*/*/*/scaling'
        global pre_scale
        if text == str(pre_scale[axis]):
            #print 'skip scaling'
            return
        #print 'scaling method :',axis , 'pre :', pre_scale, 'current :', text
        #print 'scale :', text
        space = self.space_list[space_group.checkedId()]
        value, sign = self.text2num(text)
        if value is None:
            sisidebar_sub.get_matrix()
            return
        sid = space_group.checkedId()
        if self.child_comp_but.isChecked():
            pcp = ', pcp=True'
        else:
            pcp = ''
        selection = cmds.ls(sl=True, l=True)
        if cmds.selectMode(q=True, o=True):
            for sel in selection:
                #オブジェクトモードの時はローカル変換のみサポート
                #scl = [cmds.getAttr(sel+'.scale'+a)for a in self.axis_attr_list]
                scl = cmds.xform(sel, q=True, r=True, s=True)
                if sign:
                    exec('scl[axis] '+sign+'= value')
                else:
                    scl[axis]=value
                #スケール実行
                exec('cmds.scale(scl[0], scl[1], scl[2], sel'+pcp+')')
                exec('scale'+self.axis_list[axis]+'.setText(str(scl[axis]))')
        else:#コンポーネント選択の時の処理
            if pre_scale[axis] == value:
                return
            #カーブもとっておく
            cv_selection = cmds.ls(sl=True, type='double3', fl=True)
            components = cmds.polyListComponentConversion(selection, tv=True)
            if components:
                components = cmds.filterExpand(components, sm=31)+cv_selection
            else:
                components = cv_selectione
            obj_list = list(set([vtx.split('.')[0] for vtx in components]))
            obj_dict = {obj:[] for obj in obj_list}
            [obj_dict[vtx.split('.')[0]].append(vtx) for vtx in components]
            add_scale = [1.0, 1.0, 1.0]
            if sign:
               if sign == '+':
                   add_value = 1.0+value
               elif sign == '-':
                   add_value = 1.0-1*value
               else:
                   exec('add_value = 1.0 '+sign+' value')
            else:
                add_value = value
            add_scale[axis] = add_value
            #print 'add scale :', add_scale
            #COGのときは全てのコンポーネントの中心ピボット
            if self.cog_but.isChecked():
                piv_pos = []
                for mesh, vtx in obj_dict.items():
                    piv_pos += cmds.xform(vtx, q=True, t=True, ws=True)
                piv_pos = self.get_piv_pos(piv_pos)
                #print 'Pivot COG :', piv_pos
                if sid == 0 or sid ==4:
                    cmds.scale(add_scale[0], add_scale[1], add_scale[2], components, r=True, ws=True, p=piv_pos)
                if sid == 1 or sid == 2 or sid == 5:
                    cmds.scale(add_scale[0], add_scale[1], add_scale[2], components, r=True, ls=True, p=piv_pos)
                if sid == 3:
                    cmds.scale(add_scale[0], add_scale[1], add_scale[2], components, r=True, os=True, p=piv_pos)
            else:#それぞれのメッシュの中心ピボット
                for mesh, vtx in obj_dict.items():
                    if cmds.nodeType(mesh) == 'mesh':
                        mesh = cmds.listRelatives(mesh, p=True, f=True)[0]
                    #print 'comp_mode pre scale :', pre_scale
                    base_pos = cmds.xform(mesh, q=True, t=True, ws=True)
                    #print 'comp_mode base scale position :', base_pos
                    if sid == 3:#オブジェクトモードの時だけそれぞれの角度にスケール
                        #print 'object mode :'
                        #cmds.xform(vtx, s=add_scale, r=True, os=True)
                        cmds.scale(add_scale[0], add_scale[1], add_scale[2], vtx, r=True, os=True)
                    else:#それ以外の場合はグローバル座標それぞれの位置にスケール
                        #print 'add_mode :'
                        #SIだとコンポーネントスケールはワールドもローカルも手打ちでは同じ動きをする。分けられるけど、どうしよう。
                        #cmds.scale(add_scale[0], add_scale[1], add_scale[2], vtx, r=True, ws=True, p=base_pos)
                        #分けたバージョンは以下
                        if sid == 0 or sid ==4:
                            cmds.scale(add_scale[0], add_scale[1], add_scale[2], vtx, r=True, ws=True, p=base_pos)
                        if sid == 1 or sid == 2 or sid == 5:
                            cmds.scale(add_scale[0], add_scale[1], add_scale[2], vtx, r=True, ls=True, p=base_pos)
        sisidebar_sub.get_matrix()
        #self.out_focus()
        if focus:
            global input_line_id#フォーカス外すラインを限定する
            global input_srt_id#フォーカス外すラインを限定する
            input_srt_id = 0
            input_line_id = axis
            create_focus_job()
        
    #ローテーション入力をオブジェクトに反映
    def rotation(self, text='', axis=0, focus=True):
        global world_str_mode
        global world_str_axis
        world_str_mode=1
        world_str_axis=axis
        #print '/*/*/*/*/rotation'
        global pre_rot
        if text == str(pre_rot[axis]):
            #print 'skip rot'
            return
        #print 'rotate method :',axis , 'pre :', pre_scale, 'current :', text
        sid = space_group.checkedId()
        space = self.space_list[sid]
        value, sign = self.text2num(text)
        if value is None:
            sisidebar_sub.get_matrix()
            return
        if self.child_comp_but.isChecked():
            pcp = ', pcp=True'
        else:
            pcp = ''
        selection = cmds.ls(sl=True, l=True)
        if cmds.selectMode(q=True, o=True):
            for sel in selection:
                if sid == 1 or sid == 2:#ローカルスペースとビューの時の処理
                    rot = cmds.xform(sel, q=True, ro=True)
                else:#グローバル処理
                    rot = cmds.xform(sel, q=True, ro=True, ws=True)
                if sign:
                    exec('rot[axis] '+sign+'= value')
                    #print rot
                else:
                    rot[axis]=value
                #回転実行
                if sid == 1 or sid == 2:#ローカルスペースとビューの時の処理
                    exec('cmds.rotate(rot[0], rot[1], rot[2], sel'+pcp+', os=True)')
                else:#グローバル処理
                    exec('cmds.rotate(rot[0], rot[1], rot[2], sel, ws=True'+pcp+')')
                exec('trans'+self.axis_list[axis]+'.setText(str(rot[axis]))')
        else:#コンポーネント選択の時の処理
            if pre_rot[axis] == value:
                return
            #カーブもとっておく
            cv_selection = cmds.ls(sl=True, type='double3', fl=True)
            components = cmds.polyListComponentConversion(selection, tv=True)
            if components:
                components = cmds.filterExpand(components, sm=31)+cv_selection
            else:
                components = cv_selection
            obj_list = list(set([vtx.split('.')[0] for vtx in components]))
            obj_dict = {obj:[] for obj in obj_list}
            [obj_dict[vtx.split('.')[0]].append(vtx) for vtx in components]
            add_rot = [0.0, 0.0, 0.0]
            current_rot = [0.0, 0.0, 0.0]
            if sign:
               if sign == '+':
                   add_value = value
               elif sign == '-':
                   add_value = -1*value
               else:
                   add_value = 0.0
            else:
                add_value = value
            add_rot[axis] = add_value
            #print 'New rot :', add_rot
            if self.cog_but.isChecked():
                #COGのときは全てのコンポーネントの中心ピボット
                #グローバル回転+COGを処理
                piv_pos = []
                for mesh, vtx in obj_dict.items():
                    piv_pos += cmds.xform(vtx, q=True, t=True, ws=True)
                piv_pos = self.get_piv_pos(piv_pos)
                #print 'Pivot COG :', piv_pos
                if sid == 0 or sid == 4:
                    cmds.rotate(add_rot[0], add_rot[1], add_rot[2], components, r=True, ws=True, p=piv_pos)
                if sid == 3:#オブジェクトモードの時
                    cmds.rotate(add_rot[0], add_rot[1], add_rot[2], components, r=True, eu=True, p=piv_pos)
                if sid == 1 or sid == 2 or sid == 5:#ローカルスペース
                    cmds.rotate(add_rot[0], add_rot[1], add_rot[2], components, r=True, os=True, p=piv_pos)
                    #return
            else:
                #COGグローバル以外の処理
                for mesh, vtx in obj_dict.items():
                    if cmds.nodeType(mesh) == 'mesh':
                        mesh = cmds.listRelatives(mesh, p=True, f=True)[0]
                    #print 'comp_mode pre rot :', pre_rot
                    if not self.cog_but.isChecked():
                        piv_pos = cmds.xform(mesh, q=True, t=True, ws=True)
                        #print 'comp_mode piv rot position :', piv_pos
                    if sid == 3:#オブジェクトモードの時
                        #print 'object mode :'
                        #cmds.xform(vtx, s=add_scale, r=True, os=True)
                        cmds.rotate(add_rot[0], add_rot[1], add_rot[2], vtx, r=True, eu=True, p=piv_pos)
                    if sid == 0 or sid == 4:#ワールドスペース
                        #print 'global_mode :'
                        cmds.rotate(add_rot[0], add_rot[1], add_rot[2], vtx, r=True, ws=True, p=piv_pos)
                    if sid == 1 or sid == 2 or sid == 5:#ローカルスペース
                        #print 'local_mode :'
                        cmds.rotate(add_rot[0], add_rot[1], add_rot[2], vtx, r=True, os=True, p=piv_pos)
        sisidebar_sub.get_matrix()
        #self.out_focus()
        if focus:
            global input_line_id#フォーカス外すラインを限定する
            global input_srt_id#フォーカス外すラインを限定する
            input_srt_id = 1
            input_line_id = axis
            create_focus_job()
            
    #移動をオブジェクトに反映
    def translation(self, text='', axis=0, focus=True):
        global world_str_mode
        global world_str_axis
        world_str_mode=2
        world_str_axis=axis
        #print '/*/*/*/*/translation'
        global pre_trans
        if text == self.focus_text:
            #print 'focus same', text, self.focus_text
            return
        #同じ数字が打っても効かないので前々回のラインとも比較する
        if text == str(pre_trans[axis]) and text == self.pre_pre_lines_text[2][axis]:
            #print 'Same Input Text : Skip trans'
            return
        #print 'transration method :',axis , 'pre :', pre_trans, 'current :', text
        space = self.space_list[space_group.checkedId()]
        value, sign = self.text2num(text)
        if value is None:
            sisidebar_sub.get_matrix()
            return
        sid = space_group.checkedId()
        #print space
        #print self.child_comp_but.isChecked()
        if self.child_comp_but.isChecked():
            pcp = ', pcp=True'
        else:
            pcp = ''
        selection = cmds.ls(sl=True, l=True)
        if cmds.selectMode(q=True, o=True):
            for sel in selection:
                if sid == 1 or sid == 2:#ローカルスペースとビューの時の処理
                    pos = cmds.xform(sel, q=True, t=True)
                    #exec('pos = cmds.xform(sel, q=True, t=True'+space+')')
                    #pos = [cmds.getAttr(sel+'.translate'+a)for a in self.axis_attr_list]
                else:#グローバル処理
                    pos = cmds.xform(sel, q=True, t=True, ws=True)
                if sign:
                    exec('pos[axis] '+sign+'= value')
                    #print pos
                else:
                    pos[axis]=value
                #移動実行
                if sid in local_sids:#ローカルスペースとビューの時の処理
                    exec('cmds.move(pos[0], pos[1], pos[2], sel'+pcp+',ls=True)')
                else:#グローバル処理
                    exec('cmds.move(pos[0], pos[1], pos[2], sel, ws=True'+pcp+')')
                exec('trans'+self.axis_list[axis]+'.setText(str(pos[axis]))')
        else:#コンポーネント選択の時の処理
            if text == self.focus_text:
                #print 'focus same component'
                return
            if pre_trans[axis] == value and text == self.pre_pre_lines_text[2][axis]:
                #print 'same! component'
                return
            #カーブもとっておく
            cv_selection = cmds.ls(sl=True, type='double3', fl=True)
            components = cmds.polyListComponentConversion(selection, tv=True)
            if components:
                components = cmds.filterExpand(components, sm=31)+cv_selection
            else:
                components = cv_selection
            obj_list = list(set([vtx.split('.')[0] for vtx in components]))
            #obj_list = cmds.ls(hl=True)
            obj_dict = {obj:[] for obj in obj_list}
            [obj_dict[vtx.split('.')[0]].append(vtx) for vtx in components]
            #print obj_dict
            for mesh, vtx in obj_dict.items():
                if cmds.nodeType(mesh) == 'mesh':
                    mesh = cmds.listRelatives(mesh, p=True, f=True)[0]
                #print 'comp_mode pre trans :', pre_trans
                add_trans = [0.0, 0.0, 0.0]
                if sid == 0 or sid == 4:#ワールドスペース
                    base_trans = cmds.xform(mesh, q=True, t=True, ws=True)
                else:#ローカルスペース
                    base_trans = cmds.xform(mesh, q=True, t=True, os=True)
                if sign:
                    if sign == '+':
                        add_value = value
                    elif sign == '-':
                        add_value = -1*value
                    else:
                        exec('add_value = pre_trans[axis] '+sign+' value-pre_trans[axis]')
                else:
                    if cp_abs_flag:
                        for line_obj in self.t_xyz_list:
                            if line_obj.hasFocus():
                                break
                        else:
                            #print 'skip for trans in scale rot mode'
                            return
                        #print 'run cp absolute'
                        self.scaling(text='0.0', axis=axis, focus=True)
                    add_value = value - pre_trans[axis]
                #print 'add value', add_value
                add_trans[axis] = add_value
                if sid == 0 or sid == 4:#ワールドスペース
                    cmds.move(add_trans[0], add_trans[1], add_trans[2], vtx, r=True, ws=True)
                    #cmds.xform(vtx, t=add_trans, r=True, ws=True)
                elif sid == 1 or sid == 2 or sid == 5:#ローカルスペース
                    cmds.move(add_trans[0], add_trans[1], add_trans[2], vtx, r=True, ls=True)
                    #cmds.xform(vtx, t=add_trans, r=True, os=True)
                elif sid == 3:#オブジェクトスペース
                    cmds.move(add_trans[0], add_trans[1], add_trans[2], vtx, r=True, os=True)
        sisidebar_sub.get_matrix()
        #self.out_focus()
        if focus:
            global input_line_id#フォーカス外すラインを限定する
            global input_srt_id
            input_srt_id = 2
            input_line_id = axis
            create_focus_job()
            
    #一軸を絶対値にした位置リストを返す
    def exchange_abs_val(self, components, axis, abs):
        pos_list = [cmds.xform(con, q=True, t=True, ws=True) for con in components]
        return [map(lambda a:pos[a] if a != axis else abs, range(3)) for pos in pos_list]
            
    def get_piv_pos(self, piv_pos):
        start = dt.datetime.now()
        if np_flag:
            piv_pos = np.average(np.array(piv_pos).reshape(len(piv_pos)/3, 3), axis=0)
        else:
            srt_list = [0, 0, 0]
            for i in range(0, len(piv_pos), 3):
                srt_list[0] += piv_pos[i+0]
                srt_list[1] += piv_pos[i+1]
                srt_list[2] += piv_pos[i+2]
            piv_pos = map(lambda a: a/(len(piv_pos)/3), srt_list)
        end = dt.datetime.now()
        culc_time = end - start
        view_np_time(culc_time=culc_time)
        return piv_pos
        
        
    #入力文字を分解して数値とシンボルに変える
    def text2num(self, text):
        #計算式の答えがあればそのまま返す、無い場合は四則演算モードへ
        value = self.formula_analyze(text)
        if value:
            #リストタイプだったら特殊処理する
            if isinstance(value, list):
                #ヒストリをまとめながら実行
                qt.Callback(self.linear_sort_selection(value))
                return None, None
            else:
                return value, None
        else:
            if text == ' ':
                return 0.0, None
            signs = ['+', '-', '*', '/']
            try:
                return float(text), None
            except:
                try:
                    for s in signs:
                        if text.startswith(s+'='):
                            text = text[2:]
                            sign = s
                        if text.endswith(s):
                            text = text[:-1]
                            sign = s
                        try:
                            if float(text)==0.0 and s=='/':
                                return None, None
                            return float(text), s
                        except:
                            pass
                except:
                    pass
            return None, None
        
    #計算式を解析して戻す
    def formula_analyze(self, text):
        #print 'input formula :',  text
        text = text.upper()
        text = text.replace(' ', '')
        text = text.replace('R(', 'r(')
        text = text.replace('L(', 'l(')
        text = text.replace('/', '/1.0/')#強制的にフロート変換する
        
        R=self.rand_generater()
        r=self.rand_generater
        
        L=self.linear_generater()
        l=self.linear_generater
        
        try:
            #evalで式を評価、失敗したらNoneを返す
            ans = eval(text)
            #print 'culc anser :', ans
            return ans
        except Exception as e:
            print e.message
            return None
            
    #リニア変換を行う
    def linear_sort_selection(self, value_list):
        global world_str_mode
        global world_str_axis
        #print 'cluc list type :', value_list
        #print 'selection object :', self.linear_selection
        srt_func_list = [self.scaling, self.rotation, self.translation]
        for sel, v in zip(self.linear_selection, value_list):
            #print sel, v
            cmds.select(sel, r=True)
            srt_func_list[world_str_mode](text=str(v), axis=world_str_axis)
        cmds.select(self.linear_selection, r=True)
            
    #オブジェクト数に対するリニア数リストを返す
    def linear_generater(self, mini=None, maxi=None):
        if mini is None or maxi is None:
            return None
        if cmds.selectMode(q=True, o=True):
            self.linear_selection = cmds.ls(sl=True, l=True)
        else:
            self.linear_selection = cmds.ls(hi=True)
        if self.linear_selection:
            count = len(cmds.ls(sl=True))
            par = (maxi-mini)/float(count-1)
            l_list = [mini+(par*i) for i in range(count)]
            #print l_list
            return l_list
            
    #ランダム数を書式によって生成
    def rand_generater(self, mini=None, maxi=None, seed=None):
        if maxi is None and mini is None:
            return random.random()
        if mini is not None and maxi is None:
            #print 'only mini'
            maxi = mini
            mini = 0.0
            return random.uniform(mini, maxi)
        if mini is not None and maxi is not None:
            #print 'min max'
            if seed is not None:
                #print 'seed'
                random.seed(seed)
            return random.uniform(mini, maxi)
            
        
    pre_group_mode = None
    def change_button_group(self):
        #print 'change_button_group'
        global pre_context_space
        self.pre_select_group = space_group.checkedId()
        #if cmds.currentCtx() == pre_context_space:
            #print 'same context escape chenge group'
            #return
        if select_scale.isChecked():
            if self.pre_group_mode == 'scale' and not self.init_flag:
                #print 'skip same group mode :'
                return
            try:
                self.pre_group_mode = 'scale'
                #print 'change to uni vol mode'
                space_group.removeButton(view_but)
                #space_group.removeButton(plane_but)
                scl_vol_group.addButton(view_but, 2)
                #scl_vol_group.addButton(plane_but, 5)
                if cmds.selectMode(q=True, o=True):
                    space_group.button(self.scl_obj_space).setChecked(True)
                    self.rebuild_uni_vol(mode=self.uni_obj_mode)
                if cmds.selectMode(q=True, co=True):
                    space_group.button(self.scl_cmp_space).setChecked(True)
                    self.rebuild_uni_vol(mode=self.uni_cmp_mode)
            except Exception as e:
                #print 'change space error'
                print e.message
        else:
            if self.pre_group_mode == 'other':
                #print 'skip same group mode other:'
                return
            try:
                self.pre_group_mode = 'other'
                #print 'change to normal mode'
                space_group.addButton(view_but, 2)
                #space_group.addButton(plane_but, 5)
                scl_vol_group.removeButton(view_but)
                #scl_vol_group.removeButton(plane_but)
                if select_rot.isChecked():
                    space_group.button(self.rot_space).setChecked(True)
                if select_trans.isChecked():
                    space_group.button(self.trans_space).setChecked(True)
                if select_but.isChecked():
                    space_group.button(self.pre_select_group).setChecked(True)
                    
            except Exception as e:
                #print 'change space error'
                print e.message
        pre_context_space = cmds.currentCtx()
        
#2016以降ピックリファレンス後のツールが変わるから修正する
def after_pick_context(ctx):
    global space_group
    space_group.button(4).setChecked(True)       
    window.chane_context_space()
    window.keep_srt_select(mode=3)#スペース選択状態が変わらないように保存
    cmds.setToolTo(ctx)#SRTのコンテキストに戻す
    
#UI上のボタンからキーフレームを設定、解除する
def set_key_frame(mode=0, axis=0, force=None):
    #右クリックの場合は３軸全部を再帰処理する
    if axis == 3:
        all_id = [True if key_colors[mode*3+i] == 3  else False for i in range(3)]
        if all(all_id):
            force = False
        else:
            force = True
        for i in range(3):
            set_key_frame(mode=mode, axis=i, force=force)
        return
    global key_colors
    #print key_colors
    selection = cmds.ls(sl=True, l=True, type='transform')
    if not selection:
        return
    key_names = [['scaleX', 'scaleY', 'scaleZ'],
                        ['rotateX', 'rotateY', 'rotateZ'], 
                        ['translateX', 'translateY', 'translateZ']]
    key_buts = [[key_scale_x, key_scale_y, key_scale_z], 
                        [key_rot_x, key_rot_y, key_rot_z], 
                        [key_trans_x, key_trans_y, key_trans_z]]
    id = mode*3+axis
    if force is not None:
        set_key_flag = force
    else:
        if key_colors[id] == 3:
            set_key_flag = False
        else:
            set_key_flag = True
    k_name = key_names[mode][axis]
    c_time = cmds.currentTime(q=True)
    for s in selection:
        if mode == 0:
            c_val = cmds.xform(s, q=True, r=True, s=True)
        if mode == 1:
            c_val = cmds.xform(s, q=True, r=True, ro=True)
        if mode == 2:
            c_val = cmds.xform(s, q=True, r=True, t=True)
        if set_key_flag:
            #print 'set key', k_name, c_val[axis]
            cmds.setKeyframe(s, at=k_name, v=c_val[axis])
            #key_buts[mode][axis].setIcon(QIcon(image_path+'Key_R.png'))
            #key_colors[id] = 3
        else:
            cmds.cutKey(s, at=k_name, t=(c_time, c_time))
            if mode == 0:
                cmds.xform(s, s=c_val)
            if mode == 1:
                cmds.xform(s, ro=c_val)
            if mode == 2:
                cmds.xform(s, t=c_val)
            f_curves = cmds.keyframe(s, query=True, name=True)
            '''
            if not f_curves:
                f_curves = []
            for fc in f_curves:
                if k_name in fc:
                    t_val = cmds.getAttr(fc+'.output')
                    if round(c_val[axis], 3) == round(t_val, 3):
                        key_buts[mode][axis].setIcon(QIcon(image_path+'Key_G.png'))
                        key_colors[id] = 1
                    else:
                        key_buts[mode][axis].setIcon(QIcon(image_path+'Key_Y.png'))
                        key_colors[id] = 2
                    break
            else:
                key_buts[mode][axis].setIcon(QIcon(image_path+'Key_N.png'))
                key_colors[id] = 0
            '''
    check_key_anim()
                
#何もしないコンテキストを用意しておく
def clear_prd():
    pass
    
#子のノードを維持を強制的に設定するコンテキスト
def set_child_comp(mode):
    #print 'set pcp :'
    if center_mode_but.isChecked():
        #cmds.manipScaleContext('Scale', e=True, mode=0)
        cmds.manipScaleContext('Scale', e=True, pcp=True)
        cmds.manipRotateContext('Rotate', e=True, pcp=True)
        cmds.manipMoveContext('Move', e=True, pcp=True)
        
#センター移動をオブジェクトにベイクする
def transform_center():
    #print 'bake center mode :', centers
    #cmds.undoInfo(ock=True)
    global centers
    if not centers:
        #print 'center node not found'
        return
    #ベイク中はセンターモードフラグを下げる
    sisidebar_sub.set_bake_flag(mode=True)
    current_selection = pm.ls(sl=True, l=True, tr=True)
    dummy = common.TemporaryReparent().main(mode="create")
    for sel, center in zip(center_objects, centers):
        #print 'check bake method :', sel, center
        cs = pm.xform(center, q=True, s=True, os=True, r=True)
        #cs=[1,1,1]
        cp = pm.xform(center, q=True, t=True, ws=True)
        cr = pm.xform(center, q=True, ro=True, ws=True)
        #print 'bake center node transform', sel ,cs, cp, cr
        common.TemporaryReparent().main(str(sel), dummyParent=dummy, mode="cut")      
        #cmds.makeIdentity(str(sel), n=0, s=1, r=1, jointOrient=0, t=1, apply=True, pn=1)
        #アニメーション接続があるとベイクできないのでSRTを個別にベイク
        try:
            cmds.makeIdentity(str(sel), n=0, s=0, r=0, jointOrient=0, t=1, apply=True, pn=1)
        except Exception as e:
            print e.message
        try:
            cmds.makeIdentity(str(sel), n=0, s=0, r=1, jointOrient=0, t=0, apply=True, pn=1)
        except Exception as e:
            print e.message
        try:
            cmds.makeIdentity(str(sel), n=0, s=1, r=0, jointOrient=0, t=0, apply=True, pn=1)
        except Exception as e:
            print e.message
        cmds.move(cp[0], cp[1], cp[2], str(sel)+'.scalePivot', str(sel)+'.rotatePivot', ws=True, pcp=True)
        cmds.rotate(cr[0], cr[1], cr[2], str(sel)+'.scalePivot', str(sel)+'.rotatePivot', ws=True, pcp=True)
        cmds.scale(cs[0], cs[1], cs[2], str(sel)+'.scalePivot', str(sel)+'.rotatePivot', os=True, pcp=True)
        common.TemporaryReparent().main(str(sel), dummyParent=dummy, mode="parent")
    common.TemporaryReparent().main(dummyParent=dummy, mode="delete")
    #cmds.undoInfo(cck=True)
    #if pm.ls(sl=True, l=True, tr=True) != current_selection:
    #print 'reselect for bake center :', current_selection
    pm.select(current_selection, r=True)
    sisidebar_sub.set_bake_flag(mode=False)
    
#センターモードを切り替える
def toggle_center_mode(init=None, mode=None, change=False):
    #cmds.undoInfo(cn='tgl_center', ock=True)
    global center_mode
    global center_objects
    global centers
    global pre_pcp_mode
    global pre_space
    if change:#選択変更時の挙動
        transform_center()
        sisidebar_sub.get_matrix()
        changed_selection  = pm.ls(sl=True, l=True, tr=True)
        #print 'chenge selection to :', changed_selection
        if changed_selection == centers:
            #print 'skip for same centers', centers
            #cmds.undoInfo(cn='tgl_center', cck=True)
            return
        if changed_selection == center_objects:
            #print 'skip for same objects', center_objects
            #cmds.undoInfo(cn='tgl_center', cck=True)
            return
    if mode:
        if init == 'init':
            pre_space = cmds.manipScaleContext('Scale', q=True, mode=True)
            cmds.manipScaleContext('Scale', e=True, mode=0)
            center_mode = True
            pre_pcp_mode = [cmds.manipScaleContext('Scale', q=True, pcp=True),
                                    cmds.manipRotateContext('Rotate', q=True, pcp=True),
                                    cmds.manipMoveContext('Move', q=True, pcp=True)]
            #print 'save pcp mode', pre_pcp_mode
            #ボタントグル時のモードをCulcに格納しておく
            sisidebar_sub.set_center_flag(mode=True)
        centers = []
        if not change:
            center_objects = pm.ls(sl=True, l=True, tr=True)
        else:
            center_objects = changed_selection
        #print 'start center mode :', center_objects
        if not center_objects:
            #cmds.undoInfo(cn='tgl_center', cck=True)
            return
        for sel in center_objects:
            s = pm.xform(sel, q=True, s=True, os=True, r=True)
            #s=[1,1,1]
            r = pm.xform(sel, q=True, ro=True, ws=True)
            p = pm.xform(sel, q=True, t=True, ws=True)
            pm.group(sel, n=str(sel)+'_center')
            center = pm.ls(sl=True, l=True)[0]
            centers.append(center)
            #print center
            cmds.move(p[0], p[1], p[2], str(center), str(center)+'.scalePivot', str(center)+'.rotatePivot', ws=True, pcp=True)
            cmds.scale(s[0], s[1], s[2], str(center), os=True, pcp=True)
            cmds.rotate(r[0], r[1], r[2], str(center), ws=True, pcp=True)
        pm.select(centers)
    if not mode:
        #print 'end center mode :', center_objects
        if init == 'init':
            #ボタントグル時のモードをCulcに格納しておく
            sisidebar_sub.set_center_flag(mode=False)
            center_mode = False
            #print 'end center mode'
            #print 'reset to pre pcp mode :', pre_pcp_mode
            cmds.manipScaleContext('Scale', e=True, mode=pre_space)
            cmds.manipScaleContext('Scale', e=True, pcp=pre_pcp_mode[0])
            cmds.manipRotateContext('Rotate', e=True, pcp=pre_pcp_mode[1])
            cmds.manipMoveContext('Move', e=True, pcp=pre_pcp_mode[2])
        #センターのトランスフォームをベイク
        transform_center()
        #親子付けを解除して元に戻す
        center_dict=dict()
        for sel, center in zip(center_objects, centers):
            center_dict[center] = sel
            p_node = pm.listRelatives(center, p=True, f=True)
            #print 'reparent node to :', p_node, sel
            if not p_node:
                pm.parent(sel, w=True)
            pm.parent(sel, p_node)
        #print 'get center dict', center_dict
        if change:
            #print changed_selection, centers
            pm.select(cl=True)
            for node in changed_selection:
                #print 'select node :', node
                if node in centers:
                    #print 'select center child', center_dict[node],
                    pm.select(center_dict[node], add=True)
                else:
                    pm.select(node, add=True)
        #まとめてセンターを消す
        pm.delete(centers)
        #グローバル変数を初期化
        centers = []
        center_objects = []
        #コンポーネントモードで終了したばあいはモード変異を反映する。
        if cmds.selectMode(q=True, co=True):
            cmds.selectMode(o=True)
            cmds.selectMode(co=True)
    #cmds.undoInfo(cn='tgl_center', cck=True)
              
#キーアニメの有無を確認して色を変える
def check_key_anim():
    #print 'check_key_anim'
    selection = cmds.ls(sl=True, l=True, type='transform')
    global key_colors
    key_colors = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    key_names = ['scaleX', 'scaleY', 'scaleZ', 
                        'rotateX', 'rotateY', 'rotateZ', 
                        'translateX', 'translateY', 'translateZ']
    key_buts = [key_scale_x, key_scale_y, key_scale_z, key_rot_x, key_rot_y, key_rot_z, key_trans_x, key_trans_y, key_trans_z]
    icon_list =  ['Key_N.png', 'Key_G.png', 'Key_Y.png', 'Key_R.png', 'Key_N.png', 'Key_B.png']
    c_time = cmds.currentTime(q=True)
    if not selection:
        for i in range(9):
            key_buts[i].setIcon(QIcon(image_path+icon_list[0]))
        
    for s in selection:
        f_curves = cmds.keyframe(s, query=True, name=True)
        if not f_curves:
            f_curves = []
            #key_colors = [4]*9#明示的に空のキーであることを示す
        #対称軸の名前でループ
        for i ,kn in enumerate(key_names):
            #ノードの値を取得して抽出
            mode = i/3
            axis = i%3
            if mode == 0:
                c_val = cmds.xform(s, q=True, r=True, s=True)
            if mode == 1:
                c_val = cmds.xform(s, q=True, r=True, ro=True)
            if mode == 2:
                c_val = cmds.xform(s, q=True, r=True, t=True)
            #print 'c_val :', c_val[axis]
            for fc in f_curves:
                if kn in fc:
                    #元の値がなく、F_Curveが見つかったら緑色に
                    temp_color = 1
                    #キーを探す
                    c_key = cmds.keyframe(fc, q=True, vc=True, t=(c_time, c_time))
                    #print 'c_key :', c_key
                    #キーが無いときの処理
                    if not c_key:
                        t_val = cmds.getAttr(fc+'.output')
                        #print 'get atter :', t_val
                        #値が一致しなかったら黄色に
                        if round(c_val[axis], 3) != round(t_val, 3):
                            temp_color = 2
                    else:
                        #キーとSRTの値が一致したら赤色に
                        if round(c_val[axis], 3) == round(c_key[0], 3):
                            temp_color = 3
                        else:#一致しなかったら黄色
                            temp_color = 2
                            
                    break
            else:
                #Fカーブが無いときはグレーに
                temp_color = 4
                #print 'set color to :', temp_color, i
            #他のオブジェクトアニメ情報と比較してそのままにするか青にするか決定
            if key_colors[i] == 0:
                key_colors[i] = temp_color
            else:
                if key_colors[i] != temp_color:
                    key_colors[i] = 5
    #状態に合わせてボタンカラーを変更
    for i in range(9):
        key_buts[i].setIcon(QIcon(image_path+icon_list[key_colors[i]]))
    #print key_colors
#コンテキストが変更されたときにお知らせを発行
def change_context():
    #print '*+*+*+*+*+*+* change context func *+*+*+**+*+*+**+*'
    #print 'siber get context :', cmds.currentCtx()
    if cmds.currentCtx() == 'selectSuperContext':
        #print '*+*+**+*+*** change to select context *+*+*+*+***+*+*+*'
        select_but.setChecked(True)
    window.select_from_current_context()
        
#選択モード、オブジェクト、コンポーネントモードでボタン名、選択可能を変える
def set_active_mute(mode=0):
    if select_scale.isChecked():
        mode = 0
    if select_rot.isChecked():
        mode = 1
    if select_trans.isChecked():
        mode = 2
    if select_but.isChecked():
        mode = 3
        #space_group.button(2).setChecked(True)
    #print 'change antive mute mode :', mode
    #オブジェクト、コンポーネントモード切替時に外側からモードがわかるようにグローバル保存
    global text_col
    global mute_text
    global hilite
    if maya_ver <= 2015:
        local_name = 'Local'
        rotloc_name = 'Local'
        comp_name = 'NAvrg'
    else:
        local_name = 'Parent'
        rotloc_name = 'Object'
        comp_name = 'Comp'
    obj_mode_list =[['World', local_name, 'Uni/Vol', 'Object', u'/Ref', comp_name],
                            ['World', rotloc_name, 'View', 'Gimbal', u'/Ref', comp_name],
                            ['World', local_name, 'Normal', 'Object', u'/Ref', comp_name],
                            ['World', local_name, 'View', 'Object', u'/Ref', comp_name]]
    cmp_mode_list =[['World', local_name, 'Uni/Vol', 'Object', u'/Ref', comp_name],
                            ['World', rotloc_name, 'View', 'Gimbal', u'/Ref', comp_name],
                            ['World', local_name, 'Normal', 'Object', u'/Ref', comp_name],
                            ['World', local_name, 'View', 'Object', u'/Ref', comp_name]]
    '''SI準拠の軸命名、紛らわしいので廃止
    obj_mode_list = [['Global', 'Local', 'Uni/Vol', 'Object', u'/Ref', comp_name],
                            ['Global', 'Local', 'View', 'Add', u'/Ref', comp_name],
                            ['Global', 'Local', 'Normal', 'Par', u'/Ref', comp_name],
                            ['Global', 'Local', 'View', 'Par', u'/Ref', comp_name]]
    cmp_mode_list = [['Global', 'Local', 'Uni/Vol', 'Object', u'/Ref', comp_name],
                            ['Global', 'Local', 'View', 'Object', u'/Ref', comp_name],
                            ['Global', 'Local', 'Normal', 'Object', u'/Ref', comp_name],
                            ['Global', 'Local', 'View', 'Object', u'/Ref', comp_name]]
    '''
    #オブジェクトモード、スケールの時だけスペース設定にミュートが発生するので特殊処理
    mute_list = [False, False, False, False, True, False]
    sel_mute_list = [False, False, False, True, True, True]
    text_col_list = [text_col, text_col, text_col, text_col, mute_text, text_col]
    sel_text_col_list = [text_col, text_col, text_col, mute_text, mute_text, mute_text]
    if cmds.selectMode(q=True, o=True):
        name_list = obj_mode_list[mode]
    else:
        name_list = cmp_mode_list[mode]
    for i, (button, name) in enumerate(zip(space_but_list, name_list)):
        if cmds.selectMode(q=True, o=True) and mode == 0:
            mute_flag = mute_list[i]
            color = text_col_list[i]
        elif mode == 3:
            mute_flag = sel_mute_list[i]
            color = sel_text_col_list[i]
        else:
            mute_flag = False
            color = text_col
        #2015以下ではコンポーネントモードがローテーションで使えないので封印
        if maya_ver <= 2015:
            if i == 5 and mode == 1:
                mute_flag = True
                color = mute_text
        button.setDisabled(mute_flag)
        #Uni-Volモードの名前が変わらないようにチェック
        try:
            if name == 'Uni/Vol':
                if cmds.selectMode(q=True, o=True):
                    mode = window.uni_obj_mode
                else:
                    mode = window.uni_cmp_mode
                if mode ==  2:
                    name='Uni'
                if mode ==  5:
                    name='Vol'
        except:
            pass
        button.setText(name)
        qt.change_button_color(button, textColor=color, bgColor=ui_color, hiColor=hilite, mode='button', toggle=True, destroy=destroy_flag, dsColor=border_col)
    #グループセレクションとクラスタセレクションモード切替
    if cmds.selectMode(q=True, o=True):
        select_group_but.setText('Group')
    else:
        select_group_but.setText('Cluster')
    #グループセレクションとクラスタセレクションモード切替
    if cmds.selectMode(q=True, o=True):
        select_group_but.setText('Group')
        center_mode_but.setDisabled(False)
        qt.change_button_color(center_mode_but, textColor=text_col, bgColor=ui_color, hiColor=hilite, mode='button', toggle=True, destroy=destroy_flag, dsColor=border_col)
    else:
        select_group_but.setText('Cluster')
        center_mode_but.setDisabled(True)
        center_mode_but.setChecked(False)
        qt.change_button_color(center_mode_but, textColor=mute_text, bgColor=ui_color, mode='button', toggle=True, destroy=destroy_flag, dsColor=border_col)
        
def set_srt_text(scale, rot, trans):
    scale = map(str, scale)
    rot = map(str, rot)
    trans = map(str, trans)
    #念のため0のマイナス符号を除去
    scale = map(lambda a : a.replace('-0.0', '0.0') if a=='-0.0' else a, scale)
    rot = map(lambda a : a.replace('-0.0', '0.0') if a=='-0.0' else a, rot)
    trans = map(lambda a : a.replace('-0.0', '0.0') if a=='-0.0' else a, trans)
    scale_x.setText(scale[0])
    scale_y.setText(scale[1])
    scale_z.setText(scale[2])
    rot_x.setText(rot[0])
    rot_y.setText(rot[1])
    rot_z.setText(rot[2])
    trans_x.setText(trans[0])
    trans_y.setText(trans[1])
    trans_z.setText(trans[2])
        
def set_pre_transform(trans, rot, scale):
    global pre_trans
    global pre_rot
    global pre_scale
    pre_trans = trans
    pre_rot = rot
    pre_scale = scale
    
#一旦スケールX値をリセットしてメインウィンドウクラスに変更をお知らせする
def set_temp_text(text):
    scale_x.setText(text)
    
#マニピュレータのPODタイプを選択ノードに合わせて変更する
def chenge_manip_type():
    window.set_up_manip()
    
#前回終了時にウィンドウ表示されていたら復元する
def load_with_start_up():
    save_data = read_save_file()
    if save_data['display']:
        Option()
#load_with_start_up()

        
class PropOption(qt.MainWindow):
    def __init__(self, parent = None):
        super(PropOption, self).__init__(parent)
        #print pos
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        #self.mainLayout = QHBoxLayout()
        p_layout = QGridLayout()
        wrapper.setLayout(p_layout)
        #f_layout.addWidget(menus)
        qt.change_widget_color(self, textColor=menu_text, bgColor=ui_color )
                                        
        self.msg00 = lang.Lang(
        en='Volume',
        ja=u'ボリューム')
        self.msg01 = lang.Lang(
        en='Surface',
        ja=u'サーフェス')
        self.msg02 = lang.Lang(
        en='Global',
        ja=u'グローバル')
        self.msg03 = lang.Lang(
        en='Object',
        ja=u'オブジェクト')
        vn = 0
        msg = lang.Lang(
        en='Falloff mode:',
        ja=u'減衰モード:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        p_layout.addWidget(label, vn, 0, 1, 2)
        self.prop_mode = QComboBox(self)
        self.prop_mode.addItem(self.msg00.output(), 0)
        self.prop_mode.addItem(self.msg01.output(), 1)
        self.prop_mode.addItem(self.msg02.output(), 2)
        self.prop_mode.addItem(self.msg03.output(), 3)
        qt.change_widget_color(self.prop_mode, 
                                        textColor=menu_text, 
                                        bgColor=mid_color,
                                        baseColor=base_col)
        p_layout.addWidget(self.prop_mode, vn, 2, 1, 3)
        self.prop_mode.setCurrentIndex(0)
        self.prop_mode.currentIndexChanged.connect(self.change_mode)
        
        msg = lang.Lang(
        en='Reset',
        ja=u'リセット')
        reset_but = QPushButton(msg.output(), self)
        qt.change_button_color(reset_but, textColor=text_col, bgColor=mid_color)
        reset_but.clicked.connect(self.reset)
        p_layout.addWidget(reset_but, vn, 7, 1 , 2)
        
        vn += 1
        
        msg = lang.Lang(
        en='Falloff radius:',
        ja=u'減衰半径:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        p_layout.addWidget(label, vn, 0, 1, 2)
        self.radius = QDoubleSpinBox(self)#スピンボックス
        self.radius.setRange(0, 1000)
        self.radius.setValue(5.0)#値を設定
        self.radius.setDecimals(2)#値を設定
        qt.change_widget_color(self.radius, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        p_layout.addWidget(self.radius, vn, 2, 1, 3)
        #スライダバーを設定
        self.radius_sld = QSlider(Qt.Horizontal,self)
        self.radius_sld.setRange(0, 100000)
        p_layout.addWidget(self.radius_sld, vn, 5, 1, 4)
        #mainLayout.addWidget(self.__pushSld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.radius_sld.valueChanged[int].connect(lambda:self.radius.setValue(self.radius_sld.value()/100.0))
        self.radius.editingFinished.connect(lambda:self.radius_sld.setValue(self.radius.value()*100))
        self.radius.valueChanged[float].connect(self.change_radius)
        #self.__pushSld.valueChanged[int].connect(qt.Callback(lambda :self.pushComponent(self.__pushBox.value())))
        vn += 1
        
        p_layout.addWidget(qt.make_h_line(), vn, 0, 1 , 9)
        vn += 1
        
        msg = lang.Lang(
        en='- Select Fall Off Curve Type-',
        ja=u'- 減衰カーブタイプを選択 -')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        p_layout.addWidget(label, vn, 0, 1, 9)
        vn += 1
        
        curve_icons = [':/softCurveProfile.png', ':/mediumCurveProfile.png', ':/linearCurveProfile.png', ':/hardCurveProfile.png', 
        ':/craterCurveProfile.png', ':/waveCurveProfile.png', ':/stairsCurveProfile.png', ':/ringCurveProfile.png', ':/sineCurveProfile.png']
        self.curve_values = ["1,0,2,0,1,2", "1,0.5,2,0,1,2,1,0,2", "0,1,0,1,0,1,0,1,1", "1,0,0,0,1,2", "0,0,2,1,0.8,2,0,1,2", 
        "1,0,2,0,0.16,2,0.75,0.32,2,0,0.48,2,0.25,0.64,2,0,0.8,2,0,1,2",
        "1,0,1,0.75,0.25,1,0.5,0.5,1,0.75,0.25,1,0.25,0.75,1,1,0.249,1,0.749,0.499,1,0.499,0.749,1", 
        "0,0.25,2,1,0.5,2,0,0.75,2", 
        "1,0,2,0,0.16,2,1,0.32,2,0,0.48,2,1,0.64,2,0,0.8,2,0,1,2"]
        
        self.curve_group = QButtonGroup(self)#ボタンをまとめる変数を定義
        self.but_list = []
        for i, ci in enumerate(curve_icons):
            button = make_flat_btton(icon=ci, name='', text=text_col, bg=hilite, checkable=True, w_max=24)
            p_layout.addWidget(button, vn, i, 1, 1)
            self.curve_group.addButton(button, i)
        self.curve_group.buttonClicked[int].connect(self.set_curve_type)
        #cmds.softSelect(e=1, softSelectCurve="1,0,2,0,0.16,2,1,0.32,2,0,0.48,2,1,0.64,2,0,0.8,2,0,1,2")
        
        self.init_data()
        self.radius_sld.setValue(self.radius.value()*100)
        
        self.show()
        move_to_best_pos(object=self, offset=prop_offset)
        
    def set_curve_type(self, id):
        cv = self.curve_values[id]
        cmds.softSelect(e=1, softSelectCurve=cv)
        
    def change_mode(self):
        mode = self.prop_mode.currentText()
        id= self.prop_mode.currentIndex()
        #print mode
        cmds.softSelect(ssf=id, e=True)
        #mel.eval('setSoftSelectFalloffMode("'+mode+'")')
        
    def change_radius(self, radius):
        cmds.softSelect(softSelectDistance=radius, e=True)
        
    def init_data(self):
        radius = cmds.softSelect(softSelectDistance=True, q=True)
        mode = cmds.softSelect(ssf=True, q=True)
        self.radius.setValue(radius)
        self.prop_mode.setCurrentIndex(mode)
        
    def reset(self):
        self.radius.setValue(5.0)
        self.prop_mode.setCurrentIndex(0)
        cmds.softSelect(ssr=True, e=True)
        buttons = self.curve_group.buttons()
        for but in buttons:
            self.curve_group.removeButton(but)
            but.setChecked(False)
        for i, but in enumerate(buttons):
            self.curve_group.addButton(but, i)
        
class SymOption(qt.MainWindow):
    axis_list = ['x', 'y', 'z']
    def __init__(self, parent = None):
        super(SymOption, self).__init__(parent)
        #print pos
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        #self.mainLayout = QHBoxLayout()
        s_layout = QGridLayout()
        wrapper.setLayout(s_layout)
        #f_layout.addWidget(menus)
        qt.change_widget_color(self, textColor=menu_text, bgColor=ui_color )
                                        
        self.msg00 = lang.Lang(
        en='Off',
        ja=u'オフ')
        self.msg01 = lang.Lang(
        en='World',
        ja=u'ワールド')
        self.msg02 = lang.Lang(
        en='Object',
        ja=u'オブジェクト')
        self.msg03 = lang.Lang(
        en='Topology',
        ja=u'トポロジ')
        vn = 0
        msg = lang.Lang(
        en='Symmetry:',
        ja=u'シンメトリ:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        s_layout.addWidget(label, vn, 0, 1, 2)
        off = QRadioButton(self.msg00.output(), self)
        qt.change_widget_color(off, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        world = QRadioButton(self.msg01.output(), self)
        qt.change_widget_color(world, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        object = QRadioButton(self.msg02.output(), self)
        qt.change_widget_color(object, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        s_layout.addWidget(off, vn, 2, 1, 2)
        s_layout.addWidget(world, vn+1, 2, 1, 2)
        s_layout.addWidget(object, vn+2, 2, 1, 2)
        if maya_ver >= 2015:
            topology = QRadioButton(self.msg03.output(), self)
            qt.change_widget_color(topology, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
            s_layout.addWidget(topology, vn+3, 2, 1, 2)
        self.sym_group = QButtonGroup(self)
        self.sym_group.addButton(off, 0)
        self.sym_group.addButton(world, 1)
        self.sym_group.addButton(object, 2)
        if maya_ver >= 2015:
            self.sym_group.addButton(topology, 3)
        self.sym_group.button(0).setChecked(True)#初期値設定
        self.sym_group.buttonClicked.connect(self.change_mode)
        
        msg = lang.Lang(
        en='Reset',
        ja=u'リセット')
        reset_but = QPushButton(msg.output(), self)
        qt.change_button_color(reset_but, textColor=text_col, bgColor=mid_color)
        reset_but.clicked.connect(self.reset)
        s_layout.addWidget(reset_but, vn, 7, 1, 2)
        vn += 4
        #シンメトリ軸の設定
        msg = lang.Lang(
        en='Symmetry Axis:',
        ja=u'シンメトリ軸:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        s_layout.addWidget(label, vn, 0, 1, 2)
        x = QRadioButton('X', self)
        qt.change_widget_color(x, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        y = QRadioButton('Y', self)
        qt.change_widget_color(y, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        z = QRadioButton('Z', self)
        qt.change_widget_color(z, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        s_layout.addWidget(x, vn, 2, 1, 1)
        s_layout.addWidget(y, vn, 3, 1, 1)
        s_layout.addWidget(z, vn, 4, 1, 1)
        self.axis_group = QButtonGroup(self)
        self.axis_group.addButton(x, 0)
        self.axis_group.addButton(y, 1)
        self.axis_group.addButton(z, 2)
        self.axis_group.button(0).setChecked(True)#初期値設定
        self.axis_group.buttonClicked.connect(self.change_axis)
        
        vn += 1
        msg = lang.Lang(
        en='Tolerance:',
        ja=u'許容値:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        s_layout.addWidget(label, vn, 0, 1, 2)
        self.tolerance = QDoubleSpinBox(self)#スピンボックス
        self.tolerance.setRange(0.0001, 0.5)
        self.tolerance.setDecimals(4)#値を設定
        self.tolerance.setValue(0.0010)#値を設定
        qt.change_widget_color(self.tolerance, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        s_layout.addWidget(self.tolerance, vn, 2, 1, 2)
        #スライダバーを設定
        self.tolerance_sld = QSlider(Qt.Horizontal,self)
        self.tolerance_sld.setRange(1, 50000)
        s_layout.addWidget(self.tolerance_sld, vn, 4, 1, 5)
        #mainLayout.addWidget(self.__pushSld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.tolerance_sld.valueChanged[int].connect(lambda:self.tolerance.setValue(self.tolerance_sld.value()/100000.0))
        self.tolerance.editingFinished.connect(lambda:self.tolerance_sld.setValue(self.tolerance.value()*100000))
        self.tolerance.valueChanged[float].connect(self.change_tolerance)
        vn += 1
        #法線方向に合わせるラベル設定
        msg = lang.Lang(
        en='Preserve seam:',
        ja=u'継ぎ目の保持:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text, bgColor= ui_color)
        s_layout.addWidget(label, vn, 0, 1, 2)
        self.preserve_seam = QCheckBox('', self)
        self.preserve_seam.stateChanged.connect(self.toggle_seam)
        #qt.change_button_color(self.preserve_seam, textColor=menu_text ,  bgColor=base_col )
        qt.change_widget_color(self.preserve_seam, textColor=menu_text, bgColor=ui_color, baseColor=radio_base_col)
        s_layout.addWidget(self.preserve_seam,vn, 2, 1, 1)
        vn += 1
        msg = lang.Lang(
        en='Seam Tolerance:',
        ja=u'継ぎ目の許容値:')
        label = QLabel(msg.output(), self)
        qt.change_button_color(label, textColor=menu_text, bgColor= ui_color)
        s_layout.addWidget(label, vn, 0, 1, 2)
        self.seam_tol = QDoubleSpinBox(self)#スピンボックス
        self.seam_tol.setRange(0, 0.5)
        self.seam_tol.setDecimals(4)#値を設定
        self.seam_tol.setValue(0.0010)#値を設定
        qt.change_widget_color(self.seam_tol, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        s_layout.addWidget(self.seam_tol, vn, 2, 1, 2)
        #スライダバーを設定
        self.seam_tol_sld = QSlider(Qt.Horizontal,self)
        self.seam_tol_sld.setRange(0, 50000)
        s_layout.addWidget(self.seam_tol_sld, vn, 4, 1, 5)
        #mainLayout.addWidget(self.__pushSld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.seam_tol_sld.valueChanged[int].connect(lambda:self.seam_tol.setValue(self.seam_tol_sld.value()/100000.0))
        self.seam_tol.editingFinished.connect(lambda:self.seam_tol_sld.setValue(self.seam_tol.value()*100000))
        self.seam_tol.valueChanged[float].connect(self.change_seam_tol)
        
        self.init_data()
        self.tolerance_sld.setValue(self.tolerance.value()*100000)
        self.seam_tol_sld.setValue(self.seam_tol.value()*100000)
        self.show()
        
        move_to_best_pos(object=self, offset=sym_offset)
        
    def change_mode(self):
        global pre_about
        id = self.sym_group.checkedId()
        #print mode
        if id == 0:
            cmds.symmetricModelling(s=0)
            window.sym_but.setChecked(False)
        else:
            if id== 1:
                cmds.symmetricModelling(e=True, symmetry=True, about='world')
                pre_about = 'world'
            if id == 2:
                cmds.symmetricModelling(e=True, symmetry=True, about='object')
                pre_about = 'object'
            if id == 3:
                try:
                    cmds.symmetricModelling(e=True, symmetry=True, ts=True)
                    pre_about = 'topo'
                except Exception as e:
                    print e.message
                    self.sym_group.button(0).setChecked(True)#初期値設定
                    cmds.symmetricModelling(s=0)
                    msg = lang.Lang(
                    en='Topological symmetry cannot be activated. You must select a seam edge before activation can occur',
                    ja=u'トポロジの対称を有効にできません。有効にする前に、継ぎ目エッジを選択する必要があります。')
                    cmds.warning( msg.output())
                    pre_about = 'world'
            window.sym_but.setChecked(True)
            window.toggle_sym()
    def change_axis(self):
        axis = self.axis_group.checkedId()
        #print cmds.symmetricModelling(q=True, ax=True)
        cmds.symmetricModelling(e=True, ax=self.axis_list[axis])
        
    def change_tolerance(self, tolerance):
        cmds.symmetricModelling(e=True, t=tolerance)
    def change_seam_tol(self, seam_tol):
        cmds.symmetricModelling(e=True, st=seam_tol)
    def toggle_seam(self):
        pre_seam = self.preserve_seam.isChecked()
        #print pre_seam
        cmds.symmetricModelling(ps=pre_seam)
        
    def init_data(self):
        global pre_about
        sym = cmds.symmetricModelling(q=True, s=True)
        about = cmds.symmetricModelling(q=True, a=True)
        if sym == 0:
            self.sym_group.button(0).setChecked(True)
            pre_about = 'world'
        else:
            if about == 'world':
                self.sym_group.button(1).setChecked(True)
            if about == 'object':
                self.sym_group.button(2).setChecked(True)
            if about == 'topo':
                self.sym_group.button(3).setChecked(True)
            pre_about = about
                
        axis = cmds.symmetricModelling(q=True, ax=True)
        axis_id = self.axis_list.index(axis)
        self.axis_group.button(axis_id).setChecked(True)
            
        tolerance = cmds.symmetricModelling(q=True, t=True)
        self.tolerance.setValue(tolerance)
        
        preserve_seam = cmds.symmetricModelling(q=True, ps=True)
        self.preserve_seam.setChecked(preserve_seam)
        
        seam_tol = cmds.symmetricModelling(q=True, st=True)
        self.seam_tol.setValue(seam_tol)
        
        if maya_ver >= 2015:
            topology = cmds.symmetricModelling(q=True, ts=True)
        else:
            topology = False
        #print sym, about, axis, tolerance, preserve_seam, seam_tol, topology
        
    def reset(self):
        sym = cmds.symmetricModelling(q=True, s=True)
        if sym != 0:
            self.sym_group.button(1).setChecked(True)
            cmds.symmetricModelling(e=True, symmetry=True, about='world')
            
        self.axis_group.button(0).setChecked(True)
        cmds.symmetricModelling(e=True, ax='x')
        
        self.tolerance.setValue(0.001)
        self.preserve_seam.setChecked(True)
        self.seam_tol.setValue(0.001)
        
class TransformSettingOption(qt.MainWindow):
    dir_path = os.path.join(
        os.getenv('MAYA_APP_dir'),
        'Scripting_Files')
    save_file = dir_path+'\\sisidebar_transform_setting_'+str(maya_ver)+'.json'
    def __init__(self, parent = None):
        super(TransformSettingOption, self).__init__(parent)
        
        load_transform_setting()
        
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        
        self.main_layout = QVBoxLayout()
        wrapper.setLayout(self.main_layout)
        qt.change_widget_color(self, textColor=menu_text, bgColor=ui_color)
        
        #print 'Init Transform Setting Option'
        
        msg = lang.Lang(
        en='- View number of decimal places -',
        ja=u'- 少数点以下の表示桁数 -:')
        label = QLabel(msg.output(),self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        
        self.sliderLayout = QHBoxLayout()
        self.main_layout.addLayout(self.sliderLayout)
        self.view_decimal = QSpinBox(self)#スピンボックス
        self.view_decimal.setRange(0, 10)
        self.view_decimal.setValue(view_decimal_value)#値を設定
        self.sliderLayout.addWidget(self.view_decimal)
        qt.change_widget_color(self.view_decimal, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        #スライダバーを設定
        self.view_decimal_sld = QSlider(Qt.Horizontal,self)
        self.view_decimal_sld.setRange(0, 10)
        self.view_decimal_sld.setValue(self.view_decimal.value())
        self.sliderLayout.addWidget(self.view_decimal_sld)
        #mainLayout.addWidget(self.view_decimal_sld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.view_decimal_sld.valueChanged[int].connect(self.view_decimal.setValue)
        self.view_decimal.valueChanged[int].connect(self.view_decimal_sld.setValue)
        self.view_decimal_sld.valueChanged[int].connect(self.change_view_decimal)
        self.view_decimal_sld.valueChanged[int].connect(self.save_setting)
        
        self.main_layout.addWidget(make_h_line())
        
        msg = lang.Lang(
        en='- Round number of decimal places -',
        ja=u'- 少数点以下の丸める桁数 -:')
        label = QLabel(msg.output(),self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        
        self.sliderLayout = QHBoxLayout()
        self.main_layout.addLayout(self.sliderLayout)
        self.round_decimal = QSpinBox(self)#スピンボックス
        self.round_decimal.setRange(0, 10)
        self.round_decimal.setValue(round_decimal_value)#値を設定
        self.sliderLayout.addWidget(self.round_decimal)
        qt.change_widget_color(self.round_decimal, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        #スライダバーを設定
        self.round_decimal_sld = QSlider(Qt.Horizontal,self)
        self.round_decimal_sld.setRange(0, 10)
        self.round_decimal_sld.setValue(self.round_decimal.value())
        self.sliderLayout.addWidget(self.round_decimal_sld)
        #mainLayout.addWidget(self.round_decimal_sld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.round_decimal_sld.valueChanged[int].connect(self.round_decimal.setValue)
        self.round_decimal.valueChanged[int].connect(self.round_decimal_sld.setValue)
        self.round_decimal_sld.valueChanged[int].connect(self.change_round_decimal)
        self.round_decimal_sld.valueChanged[int].connect(self.save_setting)
        
        self.main_layout.addWidget(make_h_line())
        
        msg = lang.Lang(
        en='- Mouse gesture input speed -',
        ja=u'- マウスジェスチャー入力速度 -:')
        label = QLabel(msg.output(),self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        
        self.sliderLayout = QHBoxLayout()
        self.main_layout.addLayout(self.sliderLayout)
        self.mouse_gesture = QSpinBox(self)#スピンボックス
        self.mouse_gesture.setRange(0, 20)
        self.mouse_gesture.setValue(mouse_gesture_speed)#値を設定
        self.sliderLayout.addWidget(self.mouse_gesture)
        qt.change_widget_color(self.mouse_gesture, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        #スライダバーを設定
        self.mouse_gesture_sld = QSlider(Qt.Horizontal,self)
        self.mouse_gesture_sld.setRange(0, 20)
        self.mouse_gesture_sld.setValue(self.mouse_gesture.value())
        self.sliderLayout.addWidget(self.mouse_gesture_sld)
        #mainLayout.addWidget(self.mouse_gesture_sld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.mouse_gesture_sld.valueChanged[int].connect(self.mouse_gesture.setValue)
        self.mouse_gesture.valueChanged[int].connect(self.mouse_gesture_sld.setValue)
        self.mouse_gesture_sld.valueChanged[int].connect(change_mouse_gesture)
        self.mouse_gesture_sld.valueChanged[int].connect(self.save_setting)
        
        self.show()
        move_to_best_pos(object=self, offset=transform_offset)
      
    def save_setting(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        with open(self.save_file, 'w') as f:
            save_data = {}
            save_data['view_decimal'] = self.view_decimal_sld.value()
            save_data['round_decimal'] = self.round_decimal_sld.value()
            save_data['mouse_gesture'] = self.mouse_gesture_sld.value()
            json.dump(save_data, f)
            
            
    def change_view_decimal(self, value):
        global view_decimal_value
        sisidebar_sub.set_view_decimal(decimal=value)
        view_decimal_value = value
        sisidebar_sub.get_matrix()
        
    def change_round_decimal(self, value):
        global round_decimal_value
        sisidebar_sub.set_round_decimal(decimal=value)
        round_decimal_value = value
        sisidebar_sub.get_matrix()
        top_menus = window.create_trans_menu()
        window.transfrom_top.setMenu(top_menus)
        if 'transform_manu_window' in globals():
            transform_manu_window.re_init_window()
        
#マウスジェスチャー設定から速度と比率を決定する
def change_mouse_gesture(value):
    global mouse_count_ratio
    global mouse_gesture_ratio
    if value <= 10:
        mouse_count_ratio =  11 - value
        mouse_gesture_ratio = 1.0
    else:
        mouse_count_ratio =  1
        mouse_gesture_ratio = value / 10.0
         
global view_decimal_value
global round_decimal_value
global mouse_gesture_speed
global mouse_gesture_ratio
global mouse_count_ratio
view_decimal_value = 3
round_decimal_value = 3
mouse_gesture_speed = 5
mouse_gesture_ratio = 1.0
mouse_count_ratio = 6
def load_transform_setting():
    global view_decimal_value
    global round_decimal_value
    global mouse_gesture_speed
    dir_path = os.path.join(
        os.getenv('MAYA_APP_dir'),
        'Scripting_Files')
    save_file = dir_path+'\\sisidebar_transform_setting_'+str(maya_ver)+'.json'
    if os.path.exists(save_file):#保存ファイルが存在したら
        with open(save_file, 'r') as f:
            try:
                save_data = json.load(f)
                #print save_data
                view_decimal_value = save_data['view_decimal']
                round_decimal_value = save_data['round_decimal']
                mouse_gesture_speed = save_data['mouse_gesture']
            except Exception as e:
                view_decimal_value = 3
                round_decimal_value = 3
                mouse_gesture_speed = 5
                mouse_count_ratio = 6
                print e.message   
    else:
        view_decimal_value = 3
        round_decimal_value = 3
        mouse_gesture_speed = 5
        mouse_count_ratio = 6
    sisidebar_sub.set_view_decimal(decimal=view_decimal_value)
    sisidebar_sub.set_round_decimal(decimal=round_decimal_value)
    change_mouse_gesture(mouse_gesture_speed)
        
#選択フィルターのオプション設定
class FilterOption(qt.MainWindow):
    dir_path = os.path.join(
        os.getenv('MAYA_APP_dir'),
        'Scripting_Files')
    def __init__(self, parent = None):
        super(FilterOption, self).__init__(parent)
        #print pos
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        #self.mainLayout = QHBoxLayout()
        self.main_layout = QVBoxLayout()
        wrapper.setLayout(self.main_layout)
        qt.change_widget_color(self, textColor=menu_text, bgColor=ui_color)
        
        fw=None
        fh=None
        filter_label = make_flat_btton(name='- Selection Filter Option -', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=20, tip='- Selection Filter Option -')
        self.main_layout.addWidget(filter_label)
        filter_label.setDisabled(True)
        self.main_layout.addWidget(window.make_h_line())
        
        self.all_filter = make_flat_btton(name='All Node Types', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from all node types')
        self.all_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.all_filter.text()))
        self.main_layout.addWidget(self.all_filter)
        self.transform_filter = make_flat_btton(name='Transform node', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Transform node')
        self.transform_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.transform_filter.text()))
        self.main_layout.addWidget(self.transform_filter)
        self.joint_filter = make_flat_btton(name='Joint', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Joint')
        self.joint_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.joint_filter.text()))
        self.main_layout.addWidget(self.joint_filter)
        self.shape_filter = make_flat_btton(name='Shape node', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Shape node')
        self.shape_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.shape_filter.text()))
        self.main_layout.addWidget(self.shape_filter)
        self.dummy_but_a = make_flat_btton(name='Nan', text=mute_text, bg=hilite, checkable=False, w_max=fw, h_max=fh, tip='Future filters will be added')
        self.main_layout.addWidget(self.dummy_but_a)
        self.dummy_but_a.setVisible(False)
        self.dummy_but_b = make_flat_btton(name='Nan', text=mute_text, bg=hilite, checkable=False, w_max=fw, h_max=fh, tip='Future filters will be added')
        self.main_layout.addWidget(self.dummy_but_b)
        self.dummy_but_b.setVisible(False)
        self.parent_cons_filter = make_flat_btton(name='Parent Constraint', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Parent Constraint')
        self.parent_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.parent_cons_filter.text()))
        self.main_layout.addWidget(self.parent_cons_filter)
        self.point_cons_filter = make_flat_btton(name='Point Constraint', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Point Constraint')
        self.point_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.point_cons_filter.text()))
        self.main_layout.addWidget(self.point_cons_filter)
        self.orient_cons_filter = make_flat_btton(name='Orient Constraint', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Orient Constraint')
        self.orient_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.orient_cons_filter.text()))
        self.main_layout.addWidget(self.orient_cons_filter)
        self.scale_cons_filter = make_flat_btton(name='Scale Constraint', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Scale Constraint')
        self.scale_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.scale_cons_filter.text()))
        self.main_layout.addWidget(self.scale_cons_filter)
        self.aim_cons_filter = make_flat_btton(name='Aim Constraint', text=text_col, bg=hilite, checkable=True, w_max=fw, h_max=fh, tip='Search from Aim Constraint')
        self.aim_cons_filter.clicked.connect(lambda : self.set_filter_but(filter_type=self.aim_cons_filter.text()))
        self.main_layout.addWidget(self.aim_cons_filter)
        self.dummy_but_c = make_flat_btton(name='Nan', text=mute_text, bg=hilite, checkable=False, w_max=fw, h_max=fh, tip='Future filters will be added')
        self.main_layout.addWidget(self.dummy_but_c)
        self.dummy_but_c.setVisible(False)
        
        self.filter_but_list = [self.all_filter, self.transform_filter, 
                                    self.joint_filter,self.shape_filter, 
                                    self.dummy_but_a, self.dummy_but_b, 
                                    self.parent_cons_filter, self.point_cons_filter, 
                                    self.orient_cons_filter, self.scale_cons_filter, 
                                    self.aim_cons_filter, self.dummy_but_c]
                                    
        for but in self.filter_but_list:
            but.clicked.connect(window.load_filter_but)
        
        self.load_filter_but()
        self.show()
        self.resize(200,0)#できるだけちぢめとく
        move_to_best_pos(object=self, offset=filter_offset)
        
    #セレクションフィルター状態をロード
    def load_filter_but(self):
        save_file = self.dir_path+'\\sisidebar_selection_filter_'+str(maya_ver)+'.json'
        if os.path.exists(save_file):#保存ファイルが存在したら
            with open(save_file, 'r') as f:
                save_data = json.load(f)
            all_flags = save_data['all_flags']
            for flag, but in zip(all_flags, self.filter_but_list):
                but.setChecked(flag)
                
    #テキスト検索タイプを全部かそれ以外で切り替える
    def set_filter_but(self, filter_type=''):
        #print 'set filter type :', filter_type
        if filter_type == 'All Node Types':
            if self.all_filter.isChecked():
                for filter_but in self.filter_but_list[1:]:
                    filter_but.setChecked(False)
            else:
                self.all_filter.setChecked(True)
        else:
            self.all_filter.setChecked(False)
        #全部オフならAllにチェックを入れる
        all_flags = [but.isChecked() for but in self.filter_but_list]
        if not any(all_flags):
            self.all_filter.setChecked(True)
            all_flags[0]=True
        #ボタンの状態を保存しておく
        save_file = self.dir_path+'\\sisidebar_selection_filter_'+str(maya_ver)+'.json'
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
        with open(save_file, 'w') as f:
            json.dump({'all_flags':all_flags}, f)
    
#明るめのラインを返す
global line_list
line_list = []
def make_h_line(text=255, bg=128):
    global line_list
    line = qt.make_h_line()
    qt.change_button_color(line, textColor=text, bgColor=bg)
    line_list.append(line)
    return line    
#Numpyモード比較計算時間を表示
def view_np_time(culc_time):
    try:
        window.culc_time_line.setText(culc_time)
    except:
        pass
    
def check_option_parm():
    #コンテキストからの変更をUIになるべく反映する
    window.check_ui_button()
    #window.get_init_space()
    try:
        sym_window.init_data()
    except:
        pass
    try:
        prop_option.init_data()
    except:
        pass
        
#フォーカスを外す実行関数を呼び出し
def out_focus():
    window.out_focus()
    
#フォーカスジョブの有無をクリアする
def clear_focus_job():
    #print 'clear_focus_job'
    global focus_job
    focus_job = None
    
#フォーカスを外すジョブを作る、処理終了後に一度だけ実行される
def create_focus_job():
    global focus_job
    if not 'focus_job' in globals():
        #print 'create_focus_job'
        focus_job = cmds.scriptJob(ro=True, e=("idle", sisidebar_sub.out_focus), protected=True)
    else:
        #print 'create_focus_job'
        if focus_job is None:
            focus_job = cmds.scriptJob(ro=True, e=("idle", sisidebar_sub.out_focus), protected=True)
            
def change_selection_display():
    window.display_selection()
    
#UIの再構築--------------------------------------------------------------------------------------------
def get_save_dir():
    _dir = os.environ.get('MAYA_APP_DIR')
    return os.path.join(_dir, 'Scripting_Files')

def get_shelf_floating_filepath():
    return os.path.join(get_save_dir(), 'shelf_floating.json')
      
def get_ui(name, weight_type):
    all_ui = {w.objectName(): w for w in QApplication.allWidgets()}
    ui = []
    for k, v in all_ui.items():
        if name not in k:
            continue
        # 2017だとインスタンスの型をチェックしないと別の物まで入ってきてしまうらしい
        # 2016以前だと比較すると通らなくなる…orz
        if maya_ver >= 2017:
            if v.__class__.__name__ == weight_type:
                return v
        else:
            return v
    return None      

def get_show_repr(vis_judgment=True):
    '''
    UIの状態を取得
    :param vis_judgment:表示状態を考慮するか
    :return:
    '''
    dict_ = {}
    dict_['display'] = False
    dict_['dockable'] = True
    dict_['floating'] = True
    dict_['area'] = None
    dict_['x'] = 0
    dict_['y'] = 0
    dict_['width'] = 400
    dict_['height'] = 150

    _ui = get_ui(TITLE, 'SiSideBarWeight')
    if _ui is None:
        return dict_

    if vis_judgment is True and _ui.isVisible() is False:
        return dict_

    dict_['display'] = True
    dict_['dockable'] = _ui.isDockable()
    dict_['floating'] = _ui.isFloating()
    dict_['area'] = _ui.dockArea()
    if dict_['dockable'] is True:
        dock_dtrl = _ui.parent()
        _pos = dock_dtrl.mapToGlobal(QtCore.QPoint(0, 0))
    else:
        _pos = _ui.pos()
    _sz = _ui.geometry().size()
    dict_['x'] = _pos.x()
    dict_['y'] = _pos.y()
    dict_['width'] = _sz.width()
    dict_['height'] = _sz.height()
    return dict_
    
TITLE = "SiSideBar"
def make_ui():
    # 同名のウインドウが存在したら削除
    ui = get_ui(TITLE, 'SiSideBarWeight')
    if ui is not None:
        ui.close()

    app = QApplication.instance()
    ui = SiSideBarWeight()
    return ui

def load_floating_data():
    path = get_shelf_floating_filepath()
    if os.path.isfile(path) is False:
        return None
    f = open(path, 'r')
    dict_ = json.load(f)
    return dict_
    
def main(x=None, y=None, init_pos=False):
    print 'si side bar : main'
    #Maya2016以下はいままで通りのしょり
    if maya_ver <= 2016:
        Option(init_pos=init_pos)
        return
    # 画面中央に表示
    global window
    window = make_ui()
    save_data = window.load(init_pos=False)
    _floating = load_floating_data()
    if _floating:
        width = _floating['width']
        height = _floating['height']
    else:
        width = None
        height = None

    ui_script = "import sisidebar.sisidebar_main;sisidebar.sisidebar_main.restoration_workspacecontrol()"
    
    # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
    opts = {
        "dockable": True,
        "floating": True,
        "area": "right",
        "allowedArea": None,
        "x": None,
        "y": None,
        # below options have been introduced at 2017
        "widthSizingProperty": None,
        "heightSizingProperty": None,
        "initWidthAsMinimum": None,
        "retain": False,
        "plugins": None,
        "controls": None,
        "uiScript": ui_script,
        "closeCallback": None
    }
    window.setDockableParameters(**opts)
    '''
    # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
    opts = {
        "dockable": True,
        "floating": True,
        "width": width,
        "height": height,
        # 2017でのバグ回避のため area: left で決め打ちしてしまっているが
        # 2017未満ではrestoration_docking_ui で area を再設定するため問題ない
        # 2017 では workspace layout にどこにいるか等の実体がある
        "area": "left",
        "allowedArea": None,
        "x": x,
        "y": y,

        # below options have been introduced at 2017
        "widthSizingProperty": None,
        "heightSizingProperty": None,
        "initWidthAsMinimum": None,
        "retain": False,
        "plugins": None,
        "controls": None,
        "uiScript": ui_script,
        "closeCallback": None
    }

    window.setDockableParameters(**opts)
    '''

def restoration_workspacecontrol():
    print 'si side bar : restoration_workspacecontrol'
    # workspacecontrolの再現用
    global window
    window = make_ui()
    ui_script = "import sisidebar.sisidebar_main;sisidebar.sisidebar_main.restoration_workspacecontrol()"
    # 保存されたデータのウインドウ位置を使うとウインドウのバーが考慮されてないのでズレる
    opts = {
        "dockable": True,
        "floating": False,
        "area": "left",
        "allowedArea": None,
        "x": None,
        "y": None,
        # below options have been introduced at 2017
        "widthSizingProperty": None,
        "heightSizingProperty": None,
        "initWidthAsMinimum": None,
        "retain": False,
        "plugins": None,
        "controls": None,
        "uiScript": ui_script,
        "closeCallback": None
    }
    window.setDockableParameters(**opts)
    


if __name__ == '__main__':
    main()