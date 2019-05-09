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

* ⭕️ レジストリ経由でcmake, MSBuild 等を発見する能力。vswhere。
* タスクの実行
    * ⭕️ make, dub, MSBuild 等の呼び出し代行。
    * ⭕️ cmake, premake。プロジェクトやソリューション、Makefileの生成。
    * ⭕️ タスクの依存関係
* 🔨 vsvars.bat から環境変数を取り込む
* 🔨 実行時の環境変数のコントロール
* ⭕️ mingwのtoolchain選択
* ⭕️ 実行ログ

task定義

* [Workspace.toml](./neovim/Workspace.toml)

```toml
# Workspace.toml

[[tasks]]
name = 'deps_cmake'
depends = ['clone']
cwd = 'neovim/.deps'
command = ['cmake', '../third-party', '-G', 'Visual Studio 15 2017 Win64']
```

### Language Server の起動

https://microsoft.github.io/language-server-protocol/

* ⭕️ vimのjob経由で起動する。
    * ⭕️ pyls
    * 🔨 dls
    * 🔨 cquery
* 🔨 state管理(stopped, starting, run)

### WorkspaceFolderの確定

* 🔨 設定ファイルは Workspace.toml。
* 🔨 無くても親フォルダを遡りながらWorkspaceFolderを確定させる。
* 🔨 .git, .vscode, package.json, Makefile, dub.json, setup.py等の探索。

## コマンドライン

### `--wrap`

* ⭕️ 他のコマンドをラップする。lsp, dap のデバッグ用。 例えば、vim-lsp が pyls を起動するのに割り込む。

`$ wf --wrap --logfile log.txt pyls`

* 🔨 引数無しで任意のexeを起動できるように設定を見るようにする

#### `--logfile file`

* ⭕️ ロギングしてデバッグの助けにする。
* ⭕️ http splitter
* 🔨 LSPロギング(JSON-RPC)
* 🔨 DAPロギング

### `--rpc`

* ⭕️ vimのjob経由で起動するモード。
* ⭕️ 標準入出力から接続する。
* ⭕️ JSON-RPC on HTTPもどき(Content-Lengthヘッダのみ)

### task

* 🔨 Workspace.toml に記述されたtaskを実行する。
* 🔨 実行時の cwd を調整する。
* 🔨 Workspace.toml に引数無し実行の記述を作る。

## vimplugin

* ⭕️ job で起動する
* ⭕️ transportは、 `LSP` と同じ `HTTP-keepalive` 的なストリーム
* ⭕️ protocolは、 `JSON-RPC`

### LSP

#### 通信ログのバッファ

* ⭕️ wfとのJSON-RPC通信のログを表示
* 🔨 終了時の破棄チェックされないようにする
* 🔨 メッセージをフィルタリング(高頻度のhighlight)

#### `textDocument/didOpen`

* ⭕️ autocmd FileType

#### `textDocument/didChange`

* ⭕️ autocmd TextChanged, InsertLeave
* 🔨 document バージョンの管理

#### `textDocument/definition`

* ⭕️ cursor move
* ⭕️ 他のファイルへのジャンプ
* ⭕️ jumplist

#### `textDocument/publishDiagnostics`

* ⭕️ receive
* ⭕️ location list
* ⭕️ buffer切り替え時に復旧する
* 🔨 gutter

#### `textDocument/highlight`

使わないので hover にすべきでは？

* ⭕️ autocmd CursorMoved
* 🔨 送り過ぎないようにする

#### `textDocument/hover`

* preview

#### `textDocument/references`

* jump list

#### `textDocument/completion`

* omnifunc

#### `textDocument/rename`

