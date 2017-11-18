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
    class SubWindow(QMainWindow):
        def __init__(self, parent = maya_window):
            super(SubWindow, self).__init__(maya_window)
           
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
#ボタンカラーを変更する関数
def change_button_color(button, textColor=200, bgColor=68, hiColor=68, hiText=255, hiBg=[97, 132, 167], 
                                        mode='common', toggle=False, hover=True):
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
    
    #ボタンはスタイルシートで色変更、色は16進数かスタイルシートの色名で設定するので注意
    if mode == 'common':
        button.setStyleSheet('color: '+textHex+' ; background-color: '+bgHex)
    if mode == 'button':
        button. setStyleSheet('QPushButton{background-color: '+bgHex+'; color:  '+textHex+' ; border: black 0px}' +\
                                        'QPushButton:hover{background-color: '+hvHex+'; color:  '+textHex+' ; border: black 0px}'+\
                                        'QPushButton:pressed{background-color: '+hiHex+'; color: '+textHex+'; border: black 2px}')
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
    
