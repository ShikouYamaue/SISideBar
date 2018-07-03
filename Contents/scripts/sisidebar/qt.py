# -*- coding: utf-8 -*-
from maya import OpenMayaUI, cmds
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
    imp.find_module("shiboken2")
    import shiboken2 as shiboken
except ImportError:
    import shiboken
    
maya_window = shiboken.wrapInstance(long(OpenMayaUI.MQtUtil.mainWindow()), QWidget)
    
maya_ver = int(cmds.about(v=True)[:4])
maya_api_ver = int(cmds.about(api=True))
try:
    from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
    #2017以降だったらパッチあてる、2018でもまだ不具合あるっぽい
    if 2017 <= maya_ver and maya_ver < 2019:
        # TODO: 新バージョンが出たら確認すること
        print 'import patched mixin'
        from .patch import m2017
        #from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
        MayaQWidgetDockableMixin = m2017.MayaQWidgetDockableMixin2017
        #from .patch.ringoMixin import MayaQWidgetDockableMixin
            
    else:
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
        
    class MainWindow(MayaQWidgetBaseMixin, QMainWindow):
        def __init__(self, *args, **kwargs):
            super(MainWindow, self).__init__(*args, **kwargs)
    class DockWindow(MayaQWidgetDockableMixin, QMainWindow):
        def __init__(self, *args, **kwargs):
            super(DockWindow, self).__init__(*args, **kwargs)
           
    #2018の不具合対応のためにQMainWindow用意しておく
    if 2017 <= maya_ver and maya_ver < 2019:
        class SubWindow(QMainWindow):
            def __init__(self, parent = maya_window):
                super(SubWindow, self).__init__(maya_window)
    else:
        class SubWindow(MayaQWidgetBaseMixin, QMainWindow):
            def __init__(self, *args, **kwargs):
                super(SubWindow, self).__init__(*args, **kwargs)
        
           
#2014以前はMixin無いのでMainWindow使う
except ImportError:
    import shiboken
    maya_window = shiboken.wrapInstance(long(OpenMayaUI.MQtUtil.mainWindow()), QWidget)
    
    class MainWindow(QMainWindow):
        def __init__(self, parent = maya_window):
            super(MainWindow, self).__init__(maya_window)
           
    class DockWindow(QMainWindow):
        def __init__(self, parent = maya_window):
            super(DockWindow, self).__init__(maya_window)
            
    class SubWindow(QMainWindow):
        def __init__(self, parent = maya_window):
            super(SubWindow, self).__init__(maya_window)
    
    
    
    
class Callback(object):
    def __init__(self, func, *args, **kwargs):
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs
    
    def __call__(self, *args, **kwargs):
        cmds.undoInfo(openChunk=True)
        try:
            return self.__func(*self.__args, **self.__kwargs)
            
        except:
            raise
            
        finally:
            cmds.undoInfo(closeChunk=True)
            
def getMayaWindow():
    try:
        imp.find_module("shiboken2")
        import shiboken2
        return shiboken2.wrapInstance(long(OpenMayaUI.MQtUtil.mainWindow()), QWidget)

    except ImportError:
        import shiboken
        return shiboken.wrapInstance(long(OpenMayaUI.MQtUtil.mainWindow()), QWidget)
    
#ウィジェットカラーを変更する関数
def change_widget_color(widget, 
                                        hibgColor = [100, 140, 180],
                                        hitxColor = 255,
                                        textColor=200, 
                                        bgColor=68,
                                        baseColor=42,
                                        windowText=None):
    '''引数
    widget 色を変えたいウィジェットオブジェクト
    bgColor 背景色をRGBのリストか0～255のグレースケールで指定、省略可能。
    '''
    #リスト型でなかったらリスト変換、グレースケールが指定ができるように。
    if not isinstance(hibgColor, list):
        hibgColor = [hibgColor, hibgColor, hibgColor]
    if not isinstance(hitxColor, list):
        hitxColor = [hitxColor, hitxColor, hitxColor]
    if not isinstance(textColor, list):
        textColor = [textColor, textColor, textColor]
    if not isinstance(bgColor, list):
        bgColor = [bgColor, bgColor, bgColor]
    if not isinstance(baseColor, list):
        baseColor = [baseColor, baseColor, baseColor]
        
    #色指定
    bgColor = QColor(*bgColor)
    textColor = QColor(*textColor)
    hibgColor = QColor(*hibgColor)
    hitxColor = QColor(*hitxColor)
    baseColor = QColor(*baseColor)
    #ウィジェットのカラー変更
    palette = QPalette()
    palette.setColor(QPalette.Button, bgColor)
    palette.setColor(QPalette.Background, bgColor)
    palette.setColor(QPalette.Base, baseColor)
    palette.setColor(QPalette.Text, textColor)
    
    palette.setColor(QPalette.ButtonText, textColor)
    palette.setColor(QPalette.Highlight, hibgColor)
    palette.setColor(QPalette.HighlightedText, hitxColor)
    
    #ウィンドウテキストの特殊処理
    if windowText is not None:
        if not isinstance(windowText, list):
            windowText = [windowText, windowText, windowText]
        windowTextColor = QColor(*windowText)
        #print windowText
        palette.setColor(QPalette.WindowText, windowTextColor)
    # ウィジェットにパレットを設定
    widget.setAutoFillBackground(True)
    widget.setPalette(palette)
    
'''
パレットを使って指定する色は次のものがある。
WindowText
Button
Light
Midlight
Dark
Mid
Text
BrightText
ButtonText
Base
Window
Shadow
Highlight
HighlightedText
Link
LinkVisited
AlternateBase
NoRole
ToolTipBase
ToolTipText
NColorRoles = ToolTipText + 1
Foreground = WindowText
Background = Window // ### Qt 5: remove
'''
def change_border_style(button):
    button. setStyleSheet('QPushButton{border-style:solid; border-width: 2px; border-color: red ; border-radius: 1px;}' +\
                                    'QPushButton:hover{border-style:solid; border-width: 2px; border-color: red ; border-radius: 1px;}'+\
                                    'QPushButton:pressed{border-style:solid; border-width: 2px; border-color: red ; border-radius: 1px;}')

#ボタンカラーを変更する関数
def change_button_color(button, textColor=200, bgColor=68, hiColor=68, hiText=255, hiBg=[97, 132, 167], dsColor=[255, 128, 128],
                                        mode='common', toggle=False, hover=True, destroy=False, dsWidth=1):
    '''引数
    button 色を変えたいウィジェットオブジェクト
    textColor ボタンのテキストカラーをRGBのリストか0～255のグレースケールで指定、省略可能。
    bgColor 背景色をRGBのリストか0～255のグレースケールで指定、省略可能。
    '''
    #リスト型でなかったらリスト変換、一ケタでグレー指定ができるように。
    textColor = to_3_list(textColor)
    bgColor = to_3_list(bgColor)
    hiColor = to_3_list(hiColor)
    hiText = to_3_list(hiText)
    hiBg = to_3_list(hiBg)
    dsColor = to_3_list(dsColor)
    #ボタンをハイライトカラーにする
    if toggle and button.isChecked():
        bgColor = hiColor
    #ホバー設定なら明るめの色を作る
    if hover:
        hvColor = map(lambda a:a+20, bgColor)
    else:
        hvColor = bgColor
    #RGBをスタイルシートの16進数表記に変換
    textHex =  convert_2_hex(textColor)
    bgHex = convert_2_hex(bgColor)
    hvHex = convert_2_hex(hvColor)
    hiHex = convert_2_hex(hiColor)
    htHex = convert_2_hex(hiText)
    hbHex = convert_2_hex(hiBg)
    dsHex = convert_2_hex(dsColor)
    
    #destroy=True
    #ボタンはスタイルシートで色変更、色は16進数かスタイルシートの色名で設定するので注意
    if mode == 'common':
        button.setStyleSheet('color: '+textHex+' ; background-color: '+bgHex)
    if mode == 'button':
        if not destroy:
            button. setStyleSheet('QPushButton{background-color: '+bgHex+'; color:  '+textHex+' ; border: black 0px}' +\
                                            'QPushButton:hover{background-color: '+hvHex+'; color:  '+textHex+' ; border: black 0px}'+\
                                            'QPushButton:pressed{background-color: '+hiHex+'; color: '+textHex+'; border: black 2px}')
        if destroy:
            button. setStyleSheet('QPushButton{background-color: '+bgHex+'; color:  '+textHex+'; border-style:solid; border-width: '+str(dsWidth)+'px; border-color:'+dsHex+'; border-radius: 0px;}' +\
                                            'QPushButton:hover{background-color: '+hvHex+'; color:  '+textHex+'; border-style:solid; border-width: '+str(dsWidth)+'px; border-color:'+dsHex+'; border-radius: 0px;}'+\
                                            'QPushButton:pressed{background-color: '+hiHex+'; color: '+textHex+'; border-style:solid; border-width: '+str(dsWidth)+'px; border-color:'+dsHex+'; border-radius: 0px;}')
    if mode == 'window':
        button. setStyleSheet('color: '+textHex+';'+\
                        'background-color: '+bgHex+';'+\
                        'selection-color: '+htHex+';'+\
                        'selection-background-color: '+hbHex+';')
 
    '''
    ## 最終的に設定する変数
    style = ''
    ## 枠線の色と太さ
    # border = 'border: 2px solid gray;'
    border = 'border-style:solid; border-width: 1px; border-color:gray;'
    ## 枠線の丸み
    borderRadius = 'border-radius: %spx;' % (30/2)
    ## ボタンのスタイルを作成
    buttonStyle = 'QPushButton{%s %s}' % (border, borderRadius)
    ## ボタンのスタイルを追加 
    style += buttonStyle
    ## 上記のパラメータを設定
    button.setStyleSheet(style)
    '''
    
    '''
    #スタイルシート参考
    button. setStyleSheet('QPushButton{background-color: cyan; color: black; border: black 2px} +\
                                    QPushButton:hover{background-color: green; color: black; border: black 2px} +\
                                    QPushButton:pressed{background-color: red; color: black; border: black 2px}')
    '''
def to_3_list(item):
    if not isinstance(item, list):
        item = [item]*3
    return item
    
#16真数に変換する
def convert_2_hex(color):
    hex = '#'
    for var in color:
        #format(10進数, 'x')で16進数変換
        var = format(var, 'x')
        if  len(var) == 1:
            #桁数合わせのため文字列置換
            hex = hex+'0'+str(var)
        else:
            hex = hex+str(var)
    return hex

#垂直分割線を追加する関数
def make_v_line():
    vline = QFrame()
    vline.setFrameShape(QFrame.VLine)
    vline.setFrameShadow(QFrame.Sunken)
    return vline
    
#水平分割線を追加する関数
def make_h_line():
    hline = QFrame()
    hline.setFrameShape(QFrame.HLine)
    hline.setFrameShadow(QFrame.Sunken)
    return hline
    
#ctrl,shiftでフォーカスが飛ばないカスタムラインエディット
class LineEdit(QLineEdit):
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Control or key == Qt.Key.Key_Shift:
            return
        super(self.__class__, self).keyPressEvent(event)
        
#右クリックボタンクラスの作成
class RightClickButton(QPushButton):
    rightClicked = Signal()
    def __init__(self, *args, **kwargs):
        super(RightClickButton, self).__init__(*args, **kwargs)
        self.clicked.connect(check_key_modifiers)
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.rightClicked.emit()
        else:
            super(self.__class__, self).mouseReleaseEvent(e)
            
class RightClickToolButton(QToolButton):
    rightClicked = Signal()
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.rightClicked.emit()
        else:
            super(self.__class__, self).mouseReleaseEvent(e)
            
#shift0.1入力、フォーカス時に窓選択に対応したスピンボックス
class CustomDoubleSpinbox(QDoubleSpinBox):
    wheeled = Signal()
    focused = Signal()
    keypressed = Signal()
    mousepressed = Signal()
    
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.installEventFilter(self)
        
    #ホイールイベントをのっとる
    def wheelEvent(self,e):
        pass
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            self.sel_all_input()
            self.focused.emit()
        if event.type() == QEvent.Wheel:
            delta = event.delta()
            delta /= abs(delta)
            shift_mod = self.check_shift_modifiers()
            ctrl_mod = self.check_ctrl_modifiers()
            if shift_mod:
                self.setValue(self.value()+delta/10.0)
            elif ctrl_mod:
                self.setValue(self.value()+delta*10.0)
            else:
                self.setValue(self.value()+delta)
            cmds.scriptJob(ro=True, e=("idle", self.emit_wheel_event), protected=True)
        if event.type() == QEvent.KeyPress:
            self.keypressed.emit()
        if event.type() == QEvent.MouseButtonPress:
            self.mousepressed.emit()
        return False
        
    def emit_wheel_event(self):
        self.wheeled.emit()
        
    #ウェイト入力窓を選択するジョブ
    def sel_all_input(self):
        cmds.scriptJob(ro=True, e=("idle", self.select_box_all), protected=True)
        
    #スピンボックスの数値を全選択する
    def select_box_all(self):
        try:
            self.selectAll()
        except:
            pass
            
    def check_shift_modifiers(self):
        mods = QApplication.keyboardModifiers()
        isShiftPressed =  mods & Qt.ShiftModifier
        shift_mod = bool(isShiftPressed)
        return shift_mod
        
    def check_ctrl_modifiers(self):
        mods = QApplication.keyboardModifiers()
        isCtrlPressed =  mods & Qt.ControlModifier
        ctrl_mod = bool(isCtrlPressed)
        return ctrl_mod
        
#Shift押されてるかどうかを判定する関数            
def check_key_modifiers():
    global shift_mod
    mods = QApplication.keyboardModifiers()
    isShiftPressed =  mods & Qt.ShiftModifier
    #print "Shift pressed?", bool(isShiftPressed)
    shift_mod = bool(isShiftPressed)
            
#フラットボタンを作って返す
def make_flat_button(icon=None, name='', text=200, bg=[54, 51, 51], ui_color=68, border_col=[180, 140, 30], 
                                    checkable=True, w_max=None, w_min=None, push_col=120, 
                                    h_max=None, h_min=None, policy=None, icon_size=None, tip=None, flat=True, hover=True, 
                                    destroy_flag=False, context=None, costom_push=None):
    button = RightClickButton()
    button.setText(name)
    if checkable:
        button.setCheckable(True)#チェックボタンに
    if icon:
        button.setIcon(QIcon(icon))
    if flat:
        button.setFlat(True)#ボタンをフラットに
        change_button_color(button, textColor=text, bgColor=ui_color, hiColor=bg, mode='button', hover=hover, destroy=destroy_flag, dsColor=border_col)
        button.toggled.connect(lambda : change_button_color(button, textColor=text, bgColor=ui_color, hiColor=bg, mode='button', toggle=True, hover=hover, destroy=destroy_flag, dsColor=border_col))
    else:
        button.setFlat(False)
        button.setFlat(False)
        if costom_push is None:
            change_button_color(button, textColor=text, bgColor=bg, hiColor=push_col, mode='button', hover=hover, destroy=destroy_flag, dsColor=border_col)
        else:
            change_button_color(button, textColor=text, bgColor=bg, hiColor=costom_push, mode='button', hover=hover, destroy=destroy_flag, dsColor=border_col)
    #UIスケーリングサイズを取得しておく
    if cmds.optionVar( exists='interfaceScalingValue' ) and cmds.optionVar( q='interfaceScalingMode' ) == 1:
        ui_scale = cmds.optionVar( q='interfaceScalingValue' )
    else:
        ui_scale = 1.0
    if w_max:
        button.setMaximumWidth(w_max*ui_scale)
    if w_min:
        button.setMinimumWidth(w_min*ui_scale)
    if h_max:
        button.setMaximumHeight(h_max*ui_scale)
    if h_min:
        button.setMinimumHeight(h_min*ui_scale)
    if icon_size:
        x = icon_size[0]*ui_scale
        y = icon_size[1]*ui_scale
        button.setIconSize(QSize(x, y))
    else:
        icon_size = button.iconSize()
        #print icon_size
        x = icon_size.width()*ui_scale
        y = icon_size.height()*ui_scale
        button.setIconSize(QSize(x, y))
    if policy:#拡大縮小するようにポリシー設定
        button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
    if tip:
        button.setToolTip(tip)
    if context:#コンテキストメニュー設定
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(context)
    return button