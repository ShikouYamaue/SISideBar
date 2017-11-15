# SISideBar
インストール

    Clone or download > Download ZIP からZIPファイルをダウンロードしてください。

    解凍したSiSideBarフォルダを C:\Program Files\Autodesk\ApplicationPlugins へコピーしてください。
    
    MayaをCドライブ以外にインストールしている場合でもSiShelfフォルダは
    C:\Program Files\Autodesk\ApplicationPlugins
    に置く必要があるようです。

    ApplicationPluginsフォルダが存在しない場合は作成してください。

    動作確認はMaya2015～2018で行っています。

    不要になった場合はフォルダを削除してください。
    
    インストールに成功するとウィンドウメニューにSiSideBarが追加されます。
    
    Readmeはこれからかくです。
    Maya起動時に前回の終了状態でウィンドウ位置、ドッキング位置を復元します。
    
![20171113-212852](https://user-images.githubusercontent.com/28256498/32726190-6982b406-c8bb-11e7-9c9d-25a018194a1a.jpg)
![2017-11-13_23h23_06](https://user-images.githubusercontent.com/28256498/32730253-d5b4e294-c8c9-11e7-9c9c-0d21e2a5c8e8.png)


主な機能
    
    ・SRT選択状態のリンク

    ・マニピュレータのXYZ軸とのリンク

    ・SRT入力窓の再現
    ・四則演算入力のSI方式とMaya方式の両立（10+、+=10など）
    ・ホイール入力への対応（Shift,Ctrlで桁調整 10, 1, 0.1）
    ・コンポーネントへの入力対応
    ・3軸ボタン、を右クリックで一括入力

    ・FreezeMの再現（ヒストリをベイクしてウェイトを書き戻し、クラスタとブレンドシェイプは保護）
    ・ラティスをウェイトつけたままベイクできます
    ・ウェイトをミュートしてからFreezeMするとバインドポーズを簡単に変更できます
    ・とりあえずかけておくとメッシュにまつわる大概の不具合が解消します

    ・Freezeの再現

    ・トランスフォームスペースのリンク（Global, Local, View, Objectなど）

    ・VolモードUniモードの再現

    ・Transformメニュー再現、拡充
    ・ResetActor
    ・JointOriento↔Rotation
    ・MutchiTransform
    ・FreezeTransform
    ・ResetTransform
    ・MoveCenterToSelection

    ・アニメーションキーボタンをついか（右クリックで3軸一括設定）

    ・センターモードでセンターを移動

    ・Groupモードで選択したオブジェクトが属するセットを逆引き選択

    ・Clusterモードで選択したコンポーネントが属するクラスタ、セットを逆引き選択

    ・UIメニューの折り畳み
    
    ・UIカラーの切り替え

    ・MayaシーンファイルをUIへのドラッグドロップでOpenScene扱いで開けます。自動でSetProjectされます。

    ・Numpyモジュールがインストールされているとコンポーネント計算が3倍くらい早くなります

    ・とりあえず使用説明動画とってみました
https://youtu.be/14T5_Ak4dAE
https://youtu.be/Ymq6SQwWF8s
https://youtu.be/tC5p24b9sUQ
