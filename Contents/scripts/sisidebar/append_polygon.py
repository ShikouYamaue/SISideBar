# -*- coding: utf-8 -*-
from maya import cmds
from . import common
from . import lang
from . import qt
import maya.api.OpenMaya as om
import traceback
import json
import os
import imp
import copy
import math
try:
    imp.find_module('PySide2')
    from PySide2.QtWidgets import *
    from PySide2.QtGui import *
    from PySide2.QtCore import *
except ImportError:
    from PySide.QtGui import *
    from PySide.QtCore import *
    
save_path = os.path.join(
        os.getenv('MAYA_APP_dir'),
        'Scripting_Files')
        
maya_ver = int(cmds.about(v=True)[:4])

class AppendPolygon(qt.MainWindow):
    num_list = None
    pre_mesh = None
    sub_edges = None
    last_edge = None
    mesh = None
    check_normal_flag = False
    undo_flag = False
    save_file = save_path+'\\sisidebar_append_polygon_setting_'+str(maya_ver)+'.json'
    def __init__(self, parent = None, menu_text=95, string_col=255, 
                        mid_color =160, bg_col=52,  ui_color=128, text_col=0, 
                        hilite=192, radio_base_col=255):
        super(AppendPolygon, self).__init__(parent)
        
        self.text_col = text_col
        self.hilite = hilite
        self.selected_list = []#今までの選択状態を記録する
        
        self.load_data()
        
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        self.main_layout = QVBoxLayout()
        wrapper.setLayout(self.main_layout)
        qt.change_widget_color(self, textColor=menu_text, bgColor=ui_color)
        
        #ソフトエッジ角度の設定
        msg = lang.Lang(
        en='- Smoothing Angle -',
        ja=u'- スムース角の設定 -').output()
        label = QLabel(msg,self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        self.slider_layout = QHBoxLayout()
        self.main_layout.addLayout(self.slider_layout)
        self.soft_angle = QDoubleSpinBox(self)#スピンボックス
        self.soft_angle.setRange(0, 180)
        self.soft_angle.setValue(self.soft_angle_val)#値を設定
        self.slider_layout.addWidget(self.soft_angle)
        qt.change_widget_color(self.soft_angle, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        #スライダバーを設定
        self.soft_angle_sld = QSlider(Qt.Horizontal,self)
        self.soft_angle_sld.setRange(0, 18000)
        self.soft_angle_sld.setValue(self.soft_angle.value()*100)
        self.slider_layout.addWidget(self.soft_angle_sld)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.soft_angle_sld.valueChanged.connect(lambda : self.soft_angle.setValue(self.soft_angle_sld.value()/100.0))
        self.soft_angle.editingFinished.connect(lambda : self.soft_angle_sld.setValue(self.soft_angle.value()*100))
        
        self.main_layout.addWidget(qt.make_h_line())
        
        msg = lang.Lang(en='- Component acquisition setting -', ja=u'- コンポーネント取得設定 -').output()
        label = QLabel(msg,self)#スピンボックス
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        #ラジオボタン作成
        msg = lang.Lang(en='Automatic', ja=u'自動取得').output()
        real_time = QRadioButton(msg, self)
        qt.change_widget_color(real_time, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        msg = lang.Lang(en='ボタン入力', ja=u'ボタン入力').output()
        btn_input = QRadioButton(msg, self)
        qt.change_widget_color(btn_input, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        #ラジオボタンが縦並びになるよう配置
        self.main_layout.addWidget(real_time)
        self.main_layout.addWidget(btn_input)
        #ラジオボタンを内部的に１まとめにする
        self.input_mode = QButtonGroup(self)
        self.input_mode.addButton(real_time, 0)
        self.input_mode.addButton(btn_input, 1)
        self.input_mode.buttonClicked.connect(self.change_input_mode)
        self.input_mode.buttonClicked.connect(self.save_data)
        self.input_mode.button(self.input_mode_val).setChecked(True)#初期値設定
        
        msg = lang.Lang(en='Get component', ja=u'コンポーネントを取得').output()
        #self.main_layout.addWidget(qt.make_h_line())
        self.comp_but = qt.make_flat_button(name = msg, text=text_col, bg=hilite, ui_color=ui_color, checkable=False, h_max=24, h_min=24)
        self.comp_but.clicked.connect(qt.Callback(lambda : self.append_polygon(button_input=True)))
        self.main_layout.addWidget(self.comp_but)
        
        self.main_layout.addWidget(qt.make_h_line())
        
        msg = lang.Lang(en='- Timing of face fix -', ja=u'- フェース確定のタイミング -').output()
        label = QLabel(msg,self)#スピンボックス
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        #ラジオボタン作成
        msg = lang.Lang(en='Always fixed', ja=u'常に確定').output()
        always_fix = QRadioButton(msg, self)
        qt.change_widget_color(always_fix, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        msg = lang.Lang(en='ボタン入力', ja=u'ボタン入力').output()
        btn_fix = QRadioButton(msg, self)
        qt.change_widget_color(btn_fix, textColor=menu_text,  bgColor=ui_color, baseColor=radio_base_col, windowText=menu_text)
        #ラジオボタンが縦並びになるよう配置
        self.main_layout.addWidget(always_fix)
        self.main_layout.addWidget(btn_fix)
        #ラジオボタンを内部的に１まとめにする
        self.fix_mode = QButtonGroup(self)
        self.fix_mode.addButton(always_fix, 0)
        self.fix_mode.addButton(btn_fix, 1)
        self.fix_mode.buttonClicked.connect(self.change_fix_mode)
        self.fix_mode.buttonClicked.connect(self.save_data)
        self.fix_mode.button(self.fix_mode_val).setChecked(True)#初期値設定
        
        msg = lang.Lang(en='Fix face', ja=u'フェースを確定').output()
        self.fix_but = qt.make_flat_button(name = msg, text=text_col, bg=hilite, ui_color=ui_color, checkable=False, h_max=24, h_min=24)
        self.fix_but.clicked.connect(self.reset_var)
        self.main_layout.addWidget(self.fix_but)
        
        self.create_job()
        self.create_undo_job()
        self.show()
        
        self.change_fix_mode()
        self.change_input_mode()
        
    def load_data(self):
        if os.path.exists(self.save_file):#保存ファイルが存在したら
            with open(self.save_file, 'r') as f:
                try:
                    save_data = json.load(f)
                    self.input_mode_val = save_data['input']
                    self.fix_mode_val = save_data['fix']
                    self.soft_angle_val= save_data['soft_angle']
                except Exception as e:
                    self.input_mode_val = 1
                    self.fix_mode_val = 1
                    self.soft_angle_val = 120
                    print e.message   
        else:
            self.input_mode_val = 1
            self.fix_mode_val = 1
            self.soft_angle_val= 120
            
    def save_data(self):
        save_data = {'input':self.input_mode.checkedId(),
                    'fix':self.fix_mode.checkedId(),
                    'soft_angle':self.soft_angle.value()}
        with open(self.save_file, 'w') as f:
            json.dump(save_data, f)
    
    def change_input_mode(self):
        if self.input_mode.checkedId() == 0:
            self.comp_but.setDisabled(True)
            qt.change_button_color(self.comp_but, textColor=128, bgColor=self.hilite, hover=True, mode = 'button')
        else:
            self.comp_but.setDisabled(False)
            qt.change_button_color(self.comp_but, textColor=self.text_col, bgColor=self.hilite, hover=True, mode = 'button')
        
    def change_fix_mode(self):
        if self.fix_mode.checkedId() == 0:
            self.fix_but.setDisabled(True)
            qt.change_button_color(self.fix_but, textColor=128, bgColor=self.hilite, hover=True, mode = 'button')
        else:
            self.fix_but.setDisabled(False)
            qt.change_button_color(self.fix_but, textColor=self.text_col, bgColor=self.hilite, hover=True, mode = 'button')
            
    undo_job = None
    def create_undo_job(self):
        self.undo_job = cmds.scriptJob(cu=True, e=("Undo", self.undo_control))
        
    def remove_undo_job(self):
        if self.undo_job:
            cmds.scriptJob(k=self.undo_job)
            self.undo_job = None
        
    def create_job(self):
        cmds.selectMode(co=True)
        #cmds.select(cl=True)
        self.reset_var()
        self.script_job = cmds.scriptJob(cu=True, e=("SelectionChanged", qt.Callback(self.append_polygon)))
        self.undo_flag = False
        print 'create append job :', self.script_job
        
    script_job = None
    def remove_job(self):
        if self.script_job:
            print 'remove append job :', self.script_job
            cmds.scriptJob(k=self.script_job)
            self.script_job = None
        
    def closeEvent(self, e):
        self.remove_job()
        self.remove_undo_job()
        self.save_data()
        
    def undo_control(self):
        #print '*-*-*-*-*-*undo control*-*-*-*-*-**-*'
        self.reset_var()
        
    #スクリプトジョブで選択頂点に対してアペンド制御
    def append_polygon(self, button_input=False):
        #print '******selection_change*******'
        #ボタン入力モードかどうかを判定
        if self.input_mode.checkedId() == 1 and not button_input:
            #print 'return in button mode :'
            return
        #print '-----------------------------------'
        if self.check_normal_flag:
            #'return in check mode'
            return
        if self.undo_flag:
            #print '**+*+*+*+*+*+*+*return in undo'
            self.undo_flag = False
            return
        self.sel = cmds.ls(sl=True, fl=True)
        self.mesh = cmds.ls(hl=True, l=True)
        if len(self.mesh) >1 or not self.mesh:
            self.reset_var()
            return
        if self.mesh != self.pre_mesh:
            self.reset_var()
        self.vtx = cmds.filterExpand(self.sel, sm=31)
        self.edge = cmds.filterExpand(self.sel, sm=32)
        if self.edge:
            self.vtx = common.conv_comp(self.edge, mode='vtx')
            self.uv_edge = self.edge[:]
        else:
            self.uv_edge = common.conv_comp(self.vtx, mode='edge')
            self.edge = common.conv_comp(self.vtx, mode='edge')
        if self.vtx:
            self.num_list = self.vtx2num(self.vtx)
            self.num_list = sorted(set(self.num_list), key=self.num_list.index)
        #print 'num_list :',self.num_list
        if self.num_list in self.selected_list:#以前の選択状態に含まれていたら抜ける
            #for nl in self.selected_list:
                #print 'check :', nl
            #print 'return in same selection :', self.num_list
            self.selected_list.remove(self.num_list)
            return
        if len(self.num_list) > 2:#以前の選択状態リストに追加してアンドゥ時の挙動を制御
            self.selected_list.append(self.num_list)
        self.apply_append_poly()
            
            
    #アペンド実行関数
    def apply_append_poly(self):
        #print 'try to check last edge:',self.sub_edges
        if self.sub_edges:
            self.check_last_edge()
        if len(self.num_list) < 3:
            return
        #self.all_edges = common.conv_comp(self.mesh, mode='edge')
        try:
            #print '*+*+**+**+*+*+*append polyton to :', self.num_list[:3]
            num_list = self.num_list[:3]
            cmds.polyAppendVertex(a=num_list)
            #print 'append polygon :'
            self.check_normal_uv()
            if self.last_edge:
                #print 'delete last edge', self.last_edge
                cmds.delete(self.last_edge)
            self.after_edges = common.conv_comp(self.mesh, mode='edge')
            sub_edge = len(self.all_edges)-len(self.after_edges)
            if sub_edge != 0:
                self.sub_edges = self.after_edges[sub_edge:]
            else:
                self.reset_var()
            self.num_list = self.num_list[3:]
            #print 'sub edges :', self.sub_edges
        except Exception as e:
            print e.message, common.location()
            print (traceback.format_exc())
            #print 'append error'
            self.reset_var()
        #選択が3以上なら次の面張りへ再帰
        #print 'try to next append :', self.num_list
        if self.num_list:
            self.apply_append_poly()
        if self.fix_mode.checkedId() == 0:
            self.reset_var()
            
    #法線チェックして必要に応じて反転→UV移動
    def check_normal_uv(self):
        self.check_normal_flag = True
        pre_sel = cmds.ls(sl=True)
        cmds.selectMode(o=True)
        nmv = common.conv_comp(cmds.polyInfo(nmv=True), mode='vtx')
        last_face = common.conv_comp(self.mesh, mode='face')[-1]
        last_vtx = common.conv_comp(last_face, mode='vtx')[-3:]
        #print 'nmv :',nmv
        if nmv:
            #print 'last vtx :', last_vtx
            #フェースの頂点がすべて非多様頂点だった場合は反転する
            if len(list(set(nmv) & set(last_vtx))) == 3:
                #print 'get rev face :', last_face
                cmds.polyNormal(last_face, ch=1, normalMode=4)
        self.move_uv(last_face)#UV座標の移動
        cmds.selectMode(co=True)
        cmds.select(pre_sel)
        self.check_normal_flag = False
        
        cmds.polySoftEdge(last_face, a=self.soft_angle.value())
        
    #UV座標の移動
    def move_uv(self, face):
        #print 'uv_edge :', self.uv_edge
        uvs = common.conv_comp(face, mode='uv')#作成したフェースのUV
        edge_uvs = common.conv_comp(self.uv_edge, mode='uv')#選択エッジのUV
        for uv in uvs:
            try:
                vtx = common.conv_comp(uv, mode='vtx')#UVが属する頂点
                vtx_uv = common.conv_comp(vtx, mode='uv')#頂点の共有UVたち
                target_uv = list((set(vtx_uv) & set(edge_uvs)) - set(uvs))
                #print 'get_target uv', target_uv, uv
                pos = cmds.polyEditUV(target_uv[0], query=True)
                cmds.polyEditUV(uv, u=pos[0], v=pos[1], r=False)
            except:
                return
        #UVつないでおく
        face_edges = common.conv_comp(face, mode='edge')
        cmds.polyMergeUV(face_edges, ch=1, d=0.01)
        
    #最後に張られたエッジの位置から適正な始点を返す
    def check_last_edge(self):
        try:
            if len(self.sub_edges) == 1:
                #print 'check last edge'
                self.last_edge = self.sub_edges[0]
            else:
                #print 'check last edge'
                dist = float('inf')
                pos_a = om.MPoint(cmds.pointPosition(self.mesh[0]+'.vtx['+str(self.num_list[0])+']', w=True))
                for e in self.sub_edges:
                    e_vtx = common.conv_comp(e, mode='vtx')
                    #print 'checking last :', e, e_vtx
                    pos_b = om.MPoint(cmds.pointPosition(e_vtx[0], w=True))
                    pos_c = om.MPoint(cmds.pointPosition(e_vtx[1], w=True))
                    l = (pos_a-pos_b).length() + (pos_a-pos_c).length()
                    if dist < l:
                        continue
                    self.last_edge = e
                    dist = l
            self.uv_edge = self.edge+[self.last_edge]
            #print 'get last edge:', self.last_edge
            last_num = self.vtx2num(common.conv_comp(self.last_edge, mode='vtx'))
            for num in self.num_list[:]:
                if num in last_num:
                    continue
                else:
                    last_num.append(num)
            self.num_list = last_num
            #print 'new num_list :',self.num_list
        except Exception as e:
            print e.message, common.location()
            print (traceback.format_exc())
            #print 'check edge error'
        
        
    #初期値リセット
    def reset_var(self):
        #print 'reset_var'
        self.num_list = []
        self.sub_edges = []
        self.last_edge = []
        self.pre_mesh = self.mesh
        self.all_edges = common.conv_comp(self.mesh, mode='edge')
        self.after_edges = copy.copy(self.all_edges)
            
    #頂点情報を数値に変換して戻す
    def vtx2num(self, vtx):
        num_list=[int(v[v.find('[')+1:-1]) for v in vtx]
        return num_list
        