## -*- coding: utf-8 -*-
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import uuid

from maya import cmds
from maya import mel
from maya import OpenMayaUI as omui

# Import available PySide or PyQt package, as it will work with both
try:
    from PySide2.QtCore import Qt, QPoint, QSize
    from PySide2.QtCore import Signal
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance
    _qtImported = 'PySide2'
except ImportError, e1:
    try:
        from PyQt4.QtCore import Qt, QPoint, QSize
        from PyQt4.QtCore import pyqtSignal as Signal
        from PyQt4.QtGui import *
        from sip import wrapinstance as wrapInstance
        _qtImported = 'PyQt4'
    except ImportError, e2:
        raise ImportError, '%s, %s'%(e1,e2)   

# https://gist.github.com/ryusas/626483f760c95b90622219d550c4985b
u"""
Maya 2017 workspaceControl の問題回避のサンプル。
workspaceControl と workspaceControlState のゴミが残らないようにする。
retain=False の場合でも何故か state のゴミが残ってしまうが、
scriptJob で workspaceControl の削除を監視して state も同時に削除するようにする。
retain=True の場合は、UI が閉じたとしても state は残って良いはずなので監視はしない。
いずれにせよ、スタートアップの UI 再生時にエラーとなった場合は
（そのツールをアンインストールしたり、何らかの問題が発生している場合）、
UI が閉じられた（削除ではない）時に workspaceControl と state がともに削除されるようにする。
exec を通しているのは、何故かそうするとグローバルスコープが汚れないため。
"""
_CODE_TEMPLATE = """
exec('''
import maya.cmds as cmds
name = '%s'
retain = %r
def deleteWSCtl(*a):
    if cmds.workspaceControl(name, ex=True):
        cmds.deleteUI(name)
    if cmds.workspaceControlState(name, ex=True):
        cmds.workspaceControlState(name, remove=True)
try:
    if not retain:
        cmds.scriptJob(uid=(name, deleteWSCtl))
    %s
except:
    from traceback import print_exc
    print_exc()
    def cleanup():
        if cmds.workspaceControl(name, q=True, vis=True):
            cmds.workspaceControl(name, e=True, vcc=deleteWSCtl)
        else:
            deleteWSCtl()
    cmds.evalDeferred(cleanup)
''')
"""


class MayaQWidgetDockableMixin2017(MayaQWidgetDockableMixin):
    """patched C:/Program Files/Autodesk/Maya2017/Python/Lib/site-packages/maya/app/general/mayaMixin.py"""

    def setDockableParameters(self, dockable=None, floating=None, area=None, allowedArea=None, width=None, widthSizingProperty=None, initWidthAsMinimum=None, height=None, heightSizingProperty=None, x=None, y=None, retain=True, plugins=None, controls=None, uiScript=None, closeCallback=None, *args, **kwargs):
        '''
        Set the dockable parameters.
        
        :Parameters:
            dockable (bool)
                Specify if the window is dockable (default=False)
            floating (bool)
                Should the window be floating or docked (default=True)
            area (string)
                Default area to dock into (default='left')
                Options: 'top', 'left', 'right', 'bottom'
            allowedArea (string)
                Allowed dock areas (default='all')
                Options: 'top', 'left', 'right', 'bottom', 'all'
            width (int)
                Width of the window
            height (int)
                Height of the window
            x (int)
                left edge of the window
            y (int)
                top edge of the window
                
        :See: show(), hide(), and setVisible()
        '''
        if ((dockable is True) or (dockable is None and self.isDockable())): # == Handle docked window ==
            # By default, when making dockable, make it floating
            #   This addresses an issue on Windows with the window decorators not showing up.
            if floating is None and area is None:
                floating = True

            # Create workspaceControl if needed
            if dockable is True and not self.isDockable():
                # Retrieve original position and size
                # Position
                if x is None:
                    x = self.x()
                    # Give suitable default value if null
                    if x == 0:
                        x = 250
                if y is None:
                    y = self.y()
                    # Give suitable default value if null
                    if y == 0:
                        y = 200
                # Size
                unininitializedSize = QSize(640, 480)  # Hardcode: (640,480) is the default size for a QWidget
                if self.size() == unininitializedSize:
                    # Get size from widget sizeHint if size not yet initialized (before the first show())
                    widgetSizeHint = self.sizeHint()
                else:
                    widgetSizeHint = self.size() # use the current size of the widget
                if width is None:
                    width = widgetSizeHint.width()
                if height is None:
                    height = widgetSizeHint.height()
                if widthSizingProperty is None:
                    widthSizingProperty = 'free'
                if heightSizingProperty is None:
                    heightSizingProperty = 'free'
                if initWidthAsMinimum is None:
                    initWidthAsMinimum = False

                if controls is None:
                    controls = []
                if plugins is None:
                    plugins = []

                workspaceControlName = self.objectName() + 'WorkspaceControl'

                _e = cmds.workspaceControl(workspaceControlName, query=True, exists=True)
                # Set to floating if requested or if no docking area given
                if floating is True or area is None:
                    workspaceControlName = cmds.workspaceControl(workspaceControlName,
                                                                 label=self.windowTitle(),
                                                                 retain=retain,
                                                                 loadImmediately=True,
                                                                 floating=True,
                                                                 initialWidth=width,
                                                                 widthProperty=widthSizingProperty,
                                                                 minimumWidth=initWidthAsMinimum,
                                                                 initialHeight=height,
                                                                 heightProperty=heightSizingProperty,
                                                                 requiredPlugin=plugins,
                                                                 requiredControl=controls)


                elif uiScript is None or not cmds.workspaceControl(workspaceControlName, query=True, exists=True):

                    # if self.parent() is None or self.parent() == omui.MQtUtil.mainWindow():
                    if self.parent() or isinstance(self.parent(), QMainWindow):
                        # If parented to the Maya main window or nothing, dock into the Maya main window
                        workspaceControlName = cmds.workspaceControl(workspaceControlName,
                                                                     label=self.windowTitle(),
                                                                     retain=retain,
                                                                     loadImmediately=True,
                                                                     dockToMainWindow=(area, False),
                                                                     initialWidth=width,
                                                                     widthProperty=widthSizingProperty,
                                                                     minimumWidth=initWidthAsMinimum,
                                                                     initialHeight=height,
                                                                     heightProperty=heightSizingProperty,
                                                                     requiredPlugin=plugins,
                                                                     requiredControl=controls)
                    else:
                        # Otherwise, the parent should be within a workspace control - need to go up the hierarchy to find it
                        foundParentWorkspaceControl = False
                        parent = self.parent()
                        while parent is not None:
                            dockToWorkspaceControlName = parent.objectName()
                            if cmds.workspaceControl(dockToWorkspaceControlName, q=True, exists=True):
                                workspaceControlName = cmds.workspaceControl(workspaceControlName,
                                                                             label=self.windowTitle(),
                                                                             retain=retain,
                                                                             loadImmediately=True,
                                                                             dockToControl=(dockToWorkspaceControlName, area),
                                                                             initialWidth=width,
                                                                             widthProperty=widthSizingProperty,
                                                                             minimumWidth=initWidthAsMinimum,
                                                                             initialHeight=height,
                                                                             heightProperty=heightSizingProperty,
                                                                             requiredPlugin=plugins,
                                                                             requiredControl=controls)
                                foundParentWorkspaceControl = True
                                break
                            else:
                                parent = parent.parent()

                        if foundParentWorkspaceControl is False:
                            # If parent workspace control cannot be found, just make the workspace control a floating window
                            workspaceControlName = cmds.workspaceControl(workspaceControlName,
                                                                         label=self.windowTitle(),
                                                                         retain=retain,
                                                                         loadImmediately=True,
                                                                         floating=True,
                                                                         initialWidth=width,
                                                                         widthProperty=widthSizingProperty,
                                                                         minimumWidth=initWidthAsMinimum,
                                                                         initialHeight=height,
                                                                         heightProperty=heightSizingProperty,
                                                                         requiredPlugin=plugins,
                                                                         requiredControl=controls)

                parent = omui.MQtUtil.getCurrentParent()
                mixinPtr = omui.MQtUtil.findControl(self.objectName())
                omui.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(parent))

                if uiScript is not None and len(uiScript):
                    # uiScriptはState削除のscriptJob付に加工して登録
                    code = _CODE_TEMPLATE % (workspaceControlName, retain, uiScript)
                    cmds.workspaceControl(workspaceControlName, e=True, uiScript=code)

                if closeCallback is not None:
                    cmds.workspaceControl(workspaceControlName, e=True, closeCommand=closeCallback)

                # Hook up signals
                #dockWidget.topLevelChanged.connect(self.floatingChanged)
                #dockWidget.closeEventTriggered.connect(self.dockCloseEventTriggered)
                
        else:  # == Handle Standalone Window ==
            # Make standalone as needed
            if not dockable and self.isDockable():
                # Retrieve original position and size
                dockPos = self.parent().pos()
                if x is None:
                    x = dockPos.x()
                if y is None:
                    y = dockPos.y()
                if width is None:
                    width = self.width()
                if height is None:
                    height = self.height()
                # Turn into a standalone window and reposition
                currentVisibility = self.isVisible()
                self._makeMayaStandaloneWindow() # Set the parent back to Maya and remove the parent dock widget
                self.setVisible(currentVisibility)
                
            # Handle position and sizing
            if (width is not None) or (height is not None):
                if width is None:
                    width = self.width()
                if height is None:
                    height = self.height()
                self.resize(width, height)
            if (x is not None) or (y is not None):
                if x is None:
                    x = self.x()
                if y is None:
                    y = self.y()
                self.move(x, y)


#-----------------------------------------------------------------------------
# EOF
#-----------------------------------------------------------------------------
