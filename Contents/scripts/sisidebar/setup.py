# -*- coding: utf-8 -*- 
from maya import cmds
from . import lang
import os

#AutoSetWorkSpace
def check_open():
    current_project = cmds.workspace(q=True, rootDirectory=True)
    scene_path = cmds.file(q=True, sceneName=True)
    scene_name = cmds.file(q=True, shortName=True, sceneName=True)
    msg01 = lang.Lang(
                en='Workspace not found',
                ja=u'ワークスペースがみつかりません')
    dir_list = scene_path.split('/')
    for i in range(len(dir_list)):
        dir_list = dir_list[:-1]
        root_dir = '/'.join(dir_list)+'/'
        try:
            all_files = os.listdir(root_dir)
        except:
            cmds.inViewMessage( amg=msg01.output(), pos='midCenterTop', fade=True, ta=0.75, a=0.5)
            return
        for file in all_files:
            if file == 'workspace.mel':
                set_work_space(root_dir)
                return
    cmds.inViewMessage( amg=msg01.output(), pos='midCenterTop', fade=True, ta=0.75, a=0.5)
    
def set_work_space(root_dir):
    cmds.workspace(root_dir, o=True)
    current_project = cmds.workspace(q=True, rootDirectory=True)
    print 'Set Current Work Space :', current_project
    msg00 = lang.Lang(
                en='Set Current Work Space :<hl>'+current_project+'<hl>',
                ja=u'現在のプロジェクトを<hl>' +current_project+u'</hl>に設定しました')
    cmds.inViewMessage( amg=msg00.output(), pos='midCenterTop', fade=True, ta=0.75, a=0.5)
    
#ドラッグドロップでオープンシーンする
def open_scene(mime_data):
    url_list = mime_data.urls()
    ext_dict = {'.ma':'mayaAscii', '.mb':'mayaBinary'}
    for file in url_list:
        file = file.toString().replace('file://', '')
        file_name, ext = os.path.splitext(file)
        if not ext.lower() in ext_dict.keys():
            continue
        #保存するかどうか
        msg05 = lang.Lang(
            en='untitled scene',
            ja=u'無題のシーン'
        )
        msg05 = msg05.output()
        scene_path = cmds.file(q=True, sceneName=True)
        if  scene_path == '':
            scene_path = msg05
        msg01 = lang.Lang(
            en='Save changes to '+scene_path+'?',
            ja= scene_path+u'への変更を保存しますか？'
        )   
        msg02 = lang.Lang(
            en='Save',
            ja=u'保存'
        )
        msg03 = lang.Lang(
            en="Don't Save",
            ja=u'保存しない'
        )
        msg04 = lang.Lang(
            en='Cancel',
            ja=u'キャンセル'
        )
        msg01 = msg01.output()
        msg02 = msg02.output()
        msg03 = msg03.output()
        msg04 = msg04.output()
        proc = cmds.confirmDialog(m=msg01, t='', b= [msg02, msg03, msg04], db=msg02, cb=msg04, icn='question',ds=msg03)
        if proc == msg04:
            return
        elif proc == msg03:
            pass
        elif proc == msg02:
            if scene_path == msg05:
                mel.eval("SaveSceneAs;")
            else:
                cmds.file(save=True)
        
        if file.startswith('/'):
            file_path = file[1:]
        else:
            file_path = '//'+file[:]
        cmds.file(file_path, iv=True, f=True, o=True, typ=ext_dict[ext])
        mel.eval('addRecentFile("'+file_path+'", "'+ext_dict[ext]+'")')