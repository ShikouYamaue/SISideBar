# -*- coding: utf-8 -*-
from maya import cmds
from maya import mel
from . import common

#選択セットにノード、コンポーネント追加
def add_to_set_members():
    selection = cmds.ls(sl=True)
    
    if selection:
        setCount = 0
        for node in selection:
            if cmds.nodeType(node) != 'objectSet':
                continue
            for sel in selection:
                if sel == node:
                    continue
                try:
                    cmds.sets(sel, add=node)
                except Exception as e:
                    print e.message
            setCount += 1
        if setCount == 0:
            cmds.confirmDialog( title='Error',message='Please select set_node')

#選択セットのノード、コンポーネントを削除
def remove_set_members():
    selection = cmds.ls(sl=True)
    if selection:
        setCount = 0
        for node in selection:
            if cmds.nodeType(node) != 'objectSet':
                continue
            setMembers = cmds.sets(node, int=node)
            for removeNode in selection:
                if removeNode == node:
                    continue
                try:
                    print 'Remove from set :', node, ': Object :', removeNode
                    cmds.sets(removeNode, rm=node)
                except:
                    pass
            setCount += 1
        if setCount == 0:
            cmds.confirmDialog( title='Error',message='Please select set_node')

