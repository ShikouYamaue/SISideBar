# -*- coding: utf-8 -*-
from maya import cmds
import math
import json
import os
from . import qt
from . import lang
from . import common
from . import vector

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
    
save_path = os.path.join(
        os.getenv('MAYA_APP_dir'),
        'Scripting_Files')
        
maya_ver = int(cmds.about(v=True)[:4])

class ExtrudeEdgeUV(qt.MainWindow):
    n_uvs = []
    saw_edges = []
    ex_edges = []
    save_file = save_path+'\\sisidebar_extrude_setting_'+str(maya_ver)+'.json'
    def __init__(self, parent = None, menu_text=95, string_col=255, mid_color =160, bg_col=52,  ui_color=50, text_col=0, hilite=192):
        super(ExtrudeEdgeUV, self).__init__(parent)
        self.load_data()
        
        wrapper = QWidget()
        self.setCentralWidget(wrapper)
        self.main_layout = QVBoxLayout()
        wrapper.setLayout(self.main_layout)
        qt.change_widget_color(self, textColor=menu_text, bgColor=ui_color)
        msg = lang.Lang(
        en='- UV extrusion distance -',
        ja=u'- UVの押し出し距離 -:').output()
        label = QLabel(msg,self)
        qt.change_button_color(label, textColor=menu_text ,  bgColor= ui_color )
        self.main_layout.addWidget(label)
        
        self.slider_layout = QHBoxLayout()
        self.main_layout.addLayout(self.slider_layout)
        self.d_ratio = QDoubleSpinBox(self)#スピンボックス
        self.d_ratio.setRange(0, 10)
        self.d_ratio.setValue(self.d_ratio_val)#値を設定
        self.slider_layout.addWidget(self.d_ratio)
        qt.change_widget_color(self.d_ratio, textColor=string_col, bgColor=mid_color, baseColor=bg_col)
        #スライダバーを設定
        self.d_ratio_sld = QSlider(Qt.Horizontal,self)
        self.d_ratio_sld.setRange(0, 1000)
        self.d_ratio_sld.setValue(self.d_ratio.value()*100)
        self.slider_layout.addWidget(self.d_ratio_sld)
        self.d_ratio_sld.installEventFilter(self)
        #スライダーとボックスの値をコネクト。連動するように設定。
        self.d_ratio_sld.valueChanged.connect(lambda : self.d_ratio.setValue(self.d_ratio_sld.value()/100.0))
        self.d_ratio.editingFinished.connect(lambda : self.d_ratio_sld.setValue(self.d_ratio.value()*100))
        self.d_ratio_sld.valueChanged.connect(qt.Callback(self.push_out))
        #ソフトエッジ角度の設定
        self.main_layout.addWidget(qt.make_h_line())
        msg = lang.Lang(
        en='- Smoothing Angle -',
        ja=u'- スムース角の設定 -:').output()
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
        msg = lang.Lang(en='Extrude edges', ja=u'エッジを押し出し').output()
        self.main_layout.addWidget(qt.make_h_line())
        button = qt.make_flat_button(name = msg, text=text_col, bg=hilite, ui_color=ui_color, checkable=False, h_max=24, h_min=24)
        button.clicked.connect(qt.Callback(self.extrude_edge_uv))
        self.main_layout.addWidget(button)
        msg = lang.Lang(en='Saw UV', ja=u'UVを縫合').output()
        self.main_layout.addWidget(qt.make_h_line())
        button = qt.make_flat_button(name = msg, text=text_col, bg=hilite, ui_color=ui_color, checkable=False, h_max=24, h_min=24)
        button.clicked.connect(qt.Callback(self.saw_uvs))
        self.main_layout.addWidget(button)
        
    def _init_ui(self):
        self.show()
        
    def closeEvent(self, e):
        self.save_data()
        
    #アンドゥチャンクを制御しておく
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            #print 'in'
            cmds.undoInfo(openChunk=True)
        if event.type() == QEvent.MouseButtonRelease:
            #print 'out'
            cmds.undoInfo(closeChunk=True)
        return False
        
    def load_data(self):
        if os.path.exists(self.save_file):#保存ファイルが存在したら
            with open(self.save_file, 'r') as f:
                try:
                    save_data = json.load(f)
                    self.d_ratio_val = save_data['d_ratio']
                    self.soft_angle_val= save_data['soft_angle']
                except Exception as e:
                    self.d_ratio_val = 1.0
                    self.soft_angle_val= 120
                    print e.message   
        else:
            self.d_ratio_val = 1.0
            self.soft_angle_val= 120
            
    def save_data(self):
        save_data = {'d_ratio':self.d_ratio.value(),
                    'soft_angle':self.soft_angle.value()}
        with open(self.save_file, 'w') as f:
            json.dump(save_data, f)
    
    def extrude_edge_uv(self):
        self.ex_edges = []
        sel = cmds.ls(sl=True)
        self.s_edges = common.conv_comp(sel, mode='edge')
        s_vtx = common.conv_comp(sel, mode='vtx')
        self.saw_uvs(mode='pre')#事前に押し出し対象のUVを縫い合わせておく
        if not self.s_edges:
            return
        ev_dict ,vec_dict, ev_uv_dict = self.make_edge_vtx_dict(self.s_edges)
        #print 'ev_dict :', ev_dict
        #print 'vec_dict :', vec_dict
        #押し出しを実行する
        cmds.polyExtrudeEdge(self.s_edges,
                            keepFacesTogether=True,
                            smoothingAngle=self.soft_angle.value(),
                            translate=[0, 0, 0])
        self.ex_edges = cmds.ls(sl=True)
        n_edges = common.conv_comp(self.ex_edges, mode='edge')
        n_faces = common.conv_comp(self.ex_edges, mode='face')
        self.n_uvs = common.conv_comp(n_faces, mode='uv')
        #print 'pre_move_uvs :', self.n_uvs
        #根本の位置合わせする
        new_vec_dict = {}
        for nuv in self.n_uvs[:]:
            vtx = common.conv_comp(nuv, mode='vtx')[0]
            edge = common.conv_comp(nuv, mode='edge')[0]
            if edge+' '+vtx in ev_dict.keys():
                uv_pos = ev_dict[edge+' '+vtx]
                #print 'get_uv_pos', nuv, uv_pos
                cmds.polyEditUV(nuv, u=uv_pos[0], v=uv_pos[1] ,r=False)
                self.n_uvs.remove(nuv)
                key_uv = ev_uv_dict[edge+' '+vtx]
                new_vec_dict[nuv] = vec_dict[key_uv]
        #print 'post push uvs :', self.n_uvs
        #押し出し先を根本につけて押し出しベクトル辞書をつくる
        self.uv_vec_dict = {}
        self.base_pos_dict = {}
        for nuv in self.n_uvs:
            edges = common.conv_comp(nuv, mode='edge')
            face = common.conv_comp(nuv, mode='face')
            f_uvs = common.conv_comp(face, mode='uv')
            for edge in edges:
                if edge in n_edges:
                    continue
                #print 'get new edge :', edge
                e_uvs = common.conv_comp(edge, mode='uv')
                l_uvs = list(set(f_uvs) & set(e_uvs))
                #print 'new edge uvs :', l_uvs
                for uv in l_uvs:
                    if not uv in new_vec_dict.keys():
                        continue
                    uv_pos = cmds.polyEditUV(uv, query=True)
                    cmds.polyEditUV(nuv, u=uv_pos[0], v=uv_pos[1] ,r=False)
                    self.uv_vec_dict[nuv] = new_vec_dict[uv]
                    self.base_pos_dict[nuv] = uv_pos
                    self.saw_edges.append(edge)#縫い合わせ用リストに入れておく
        self.push_out()
        cmds.setToolTo('moveSuperContext')
        
    def push_out(self):
        for uv in self.n_uvs:
            base_pos = self.base_pos_dict[uv]
            uv_pos = self.uv_vec_dict[uv]
            u = uv_pos[0]*self.d_ratio.value()/10+base_pos[0]
            v = uv_pos[1]*self.d_ratio.value()/10+base_pos[1]
            cmds.polyEditUV(uv, u=u, v=v ,r=False)
            
    #エッジと頂点のセットでuv座標を記録しておく
    def make_edge_vtx_dict(self, edges):
        edge_vtx_dict = {}
        vec_dict = {}
        pos_dict = {}
        ev_uv_dict = {}
        if not edges:
            return
        for edge in edges:
            uvs = common.conv_comp(edge, mode='uv')
            for uv in uvs:
                vtx = common.conv_comp(uv, mode='vtx')[0]
                pos = cmds.polyEditUV(uv, query=True)
                edge_vtx_dict[edge+' '+vtx] = pos
                vec_dict[uv] = self.culc_push_vec(uv)
                pos_dict[uv] = pos
                ev_uv_dict[edge+' '+vtx] = uv
        return edge_vtx_dict, vec_dict, ev_uv_dict
        
    #押し出し方向を計算する
    def culc_push_vec(self, uv):
        #s_edge_uv = common.conv_comp(edges, mode='uv')
        re_uvs = common.conv_comp(uv, mode='edge')
        re_uvs = common.conv_comp(re_uvs, mode='uv')
        rf_uvs = common.conv_comp(uv, mode='face')
        rf_uvs = common.conv_comp(rf_uvs, mode='uv')
        #論理積をとってベクトルをとるUVを絞り込む
        r_uvs = list(set(re_uvs)&set(rf_uvs))
        # uv, r_uvs
        uv_pos = cmds.polyEditUV(uv, q=True)
        #それぞれのUVを取得して正規化
        push_vec = [0.0,0.0]
        for ruv in r_uvs:
            #if ruv in s_edge_uv:
                #continue
            if ruv == uv:
                continue
            ruv_pos = cmds.polyEditUV(ruv, q=True)
            uv_vec =  [uv_pos[0]-ruv_pos[0], uv_pos[1]-ruv_pos[1]]
            if vector.get_length(uv_vec) == 0.0:#ベクトル0の場合はスキップする
                continue
            #均等に押し広げるためにあらかじめ正規化したベクトルの合計を出す
            uv_vec = vector.normalize(uv_vec)
            push_vec = [push_vec[0]+uv_vec[0], push_vec[1]+uv_vec[1]]
        push_vec = vector.normalize(push_vec)#正規化
        return push_vec
    #縫い合わせる
    def saw_uvs(self, mode='after'):
        if mode == 'after':
            saw_edges = self.saw_edges
            self.n_uvs = []
        else:
            saw_edges = common.conv_comp(self.s_edges, mode='vtx')
            saw_edges = common.conv_comp(saw_edges, mode='edge')
            for edge in self.s_edges:
                saw_edges.remove(edge)
        if not saw_edges:
            return
        checked_edges = []
        for edge in saw_edges:
            uvs = common.conv_comp(edge, mode='uv')
            uv_pos = [str(map(lambda x:round(x, 5), cmds.polyEditUV(uv, q=True))) for uv in uvs]
            #print len(uv_pos)
            uv_pos = list(set(uv_pos))
            #if mode=='pre':
                #print edge, len(uv_pos)
            if len(uv_pos) > 2:
                continue
            checked_edges.append(edge)
        if checked_edges:
            cmds.polyMapSew(checked_edges, ch=True)
        cmds.polyMapSew(self.s_edges, ch=True)#付け根のUVを縫合する
        self.saw_edges = []
        cmds.select(self.ex_edges, r=True)
#ExtrudeEdgeUV()._init_ui()