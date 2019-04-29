# WorkspaceFolder

Debug depends on build, build depends on code, and code depends on the root path(workspaceFolder).

vimでDebugAdapterを駆動するバックエンドを作る計画。

* pyls + ms-python.pythonのDebugAdapter の環境を最初に作る
* [後で]cquery + webfreak.debugのDebugAdapter
* [後で]dls + webfreak.debugのDebugAdapter
* [後で]C#

## 主な機能

### Debug Adapter の起動

https://microsoft.github.io/debug-adapter-protocol/overview

* VSCodeの拡張を起動して、標準入出力から制御する。
* vimのjob経由で起動する。
* AdapterAdapter 的なものになるのだけど、DebugAdapter毎に微妙に挙動違うのでこのレイヤーで差異を吸収する。

### Task実行

#### Build
* make, dub, MSBuild 等の呼び出し代行。
* レジストリ経由でcmake, MSBuild 等を発見する能力。vswhere。

#### MetaBuild

* cmake, premake。プロジェクトやソリューション、Makefileの生成。
* コーディングの一部は、これの影響を受ける(Includeパスや、csのプロジェクト参照など)
* 事前の環境整備。npm installなど。

### Language Server の起動

https://microsoft.github.io/language-server-protocol/

* VSCodeの拡張を起動して、標準入出力から制御する。
* vimのjob経由で起動する。
* LSPがクラッシュしても自動で再起動する。

### WorkspaceFolderの確定

* 設定ファイルは Workspace.toml。
* 無くても親フォルダを遡りながらWorkspaceFolderを確定させる。
* .git, .vscode, package.json, Makefile, dub.json, setup.py等の探索。

### vim plugin と 単体実行

* vim plugin から job で DAP と LSP の実行を代行させる(vimscriptよくわからん)。
* コマンドラインからの単体実行(ややこしいところは `python3` で解決)。
* DAP, LSP のセッションのロギングとか。

## コマンドライン

subcommands

### wrap

他のコマンドをラップする。lsp, dap のデバッグ用。
例えば、vim-lsp が pyls を起動するのに割り込む。

#### --logfile=file

ロギングしてデバッグの助けにする。

### job

vimのjob経由で起動するモード。
標準入出力から制御する。JSON-RPC。

### task

Workspace.toml に記述されたtaskを実行する。
実行時の cwd を調整する。

### run

他のコマンドを実行する。
実行時の cwd を調整する。

