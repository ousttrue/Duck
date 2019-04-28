# WorkspaceFolder

Debug depends on build, build depends on code, and code depends on the workspaceFolder.

vimでDebugAdapterを駆動するバックエンドを作る計画。

* pyls + ms-python.pythonのDebugAdapter の環境を最初に作る
* [後で]cquery + webfreak.debugのDebugAdapter
* [後で]dls + webfreak.debugのDebugAdapter
* [後で]C#

## Debug(Debug Adapter Protocol)

https://microsoft.github.io/debug-adapter-protocol/overview

* VSCodeの拡張を起動して、標準入出力から制御する。
* AdapterAdapter 的なものになるのだけど、DebugAdapter毎に微妙に挙動違うのでこのレイヤーで差異を吸収する。

## Build(Task実行)

* make, dub, MSBuild 等の呼び出し代行。
* cmake, MSBuild 等を発見する能力。vswhere

## Coding(Language Server Protocol)

https://microsoft.github.io/language-server-protocol/

* VSCodeの拡張を起動して、標準入出力から制御する。
* LSPがクラッシュしても自動で再起動する。

## MetaBuild(Task実行)

* cmake, premake。プロジェクトやソリューション、Makefileの生成。
* コーディングの一部は、これの影響を受ける(Includeパスや、csのプロジェクト参照など)
* 事前の環境整備。npm installなど。

## WorkspaceFolderの確定

* 設定ファイルは WorkspaceFolder.toml。
* 無くても親フォルダを遡りながらWorkspaceFolderを確定させる。
* .git, .vscode, package.json, Makefile, dub.json, setup.py等の探索。

## vim plugin と 単体実行

* vim plugin で job で DAP と LSP の実行を代行させる(vimscriptよくわからん)。
* コマンドラインからの単体実行(ややこしいところは、 `python3` で解決)。
* DAP, LSP のセッションのロギングとか。

