# WorkspaceFolder

Debug depends on build, build depends on code, and code depends on the root path(workspaceFolder).

vimでDebugAdapterを駆動するバックエンドを作る計画。

Python-3.7

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

```
usage: ws [-h] [--logfile LOGFILE] [--debug] [--rpc] [--wrap]
          [args [args ...]]
```

### `--logfile file`

* ⭕️ ロギングしてデバッグの助けにする。
* ⭕️ http splitter
* 🔨 LSPロギング(JSON-RPC)
* 🔨 DAPロギング

### `--wrap`

`args` 引数をコマンドラインとして実行する。

* ⭕️ 他のコマンドをラップする。lsp, dap のデバッグ用。 例えば、vim-lsp が pyls を起動するのに割り込む。

`$ wf --wrap --logfile log.txt pyls`

* 🔨 taskで記述できるようにして廃止する

### `--rpc`

* ⭕️ vimのjob経由で起動するモード。
* ⭕️ 標準入出力から接続する。
* ⭕️ JSON-RPC on HTTPもどき(Content-Lengthヘッダのみ)

### task

`args` 引数をtask名として順番に実行する。

* ⭕️ Workspace.toml に記述されたtaskを実行する。
* 🔨 Workspace.toml に引数無し実行の記述を作る。

## vimplugin

* ⭕️ job で起動する
* ⭕️ transportは、 `LSP` と同じ `HTTP-keepalive` 的なストリーム
* ⭕️ protocolは、 `JSON-RPC`

## LSP

### 通信ログのバッファ

* ⭕️ wfとのJSON-RPC通信のログを表示

### 状態表示

* 🔨 workspace(rootpath, language)
* 🔨 document(relative path from rootpath)

### Workspaceの管理

* 🔨 違うフォルダのプロジェクトを開いたときにworkspaceを変更する

### `textDocument/didOpen`

* ⭕️ autocmd FileType

### `textDocument/didChange`

* ⭕️ autocmd TextChanged, InsertLeave
* ⭕️ document バージョンをincrement

### `textDocument/definition`

* ⭕️ `call ws#gotoDefinition`
* ⭕️ cursor move
* ⭕️ 他のファイルへのジャンプ
* ⭕️ jumplist

### `textDocument/publishDiagnostics`

* ⭕️ receive
* ⭕️ location list
* ⭕️ buffer切り替え時に復旧する
* ⭕️ gutter

### `textDocument/highlight`

### `textDocument/hover`

* ⭕️ `call ws#hover`

### `textDocument/references`

* ⭕️ `call ws#references`
* 🔨 jump list(LocationListに一時的に出す？)

### `textDocument/completion`

* ⭕️ omnifunc
* 🔨 kind
* 🔨 menu
* 🔨 detail(signature)
* 🔨 documentation(preview)

### `textDocument/rename`

### `textDocument/formatter`

## LanguageServer

### `py` pyls

```
[mypy] No parent module -- cannot perform relative import
```

相対import使用時に回避不能。

https://github.com/tomv564/pyls-mypy/issues/17

mypyの `--command` 引数を使う場合に、mypyにソースのファイルパスを渡す方法を追加してやる必要がある。
`pyls-mypy` で `mypy` にモンキーパッチか

* ⭕️ gotoDefinition
* 🔨 references
* ⭕️ hover
* ⭕️ completion
* ⭕️ diagonostics

### `d` dls

`dub run dls`

dub.json のある階層に chdir する必要がある？

* 🔨 gotoDefinition(初回だけ動く？)
* 🔨 references
* 🔨 hover
* 🔨 completion
* ⭕️ diagonostics

### `d` serve-d

`dub run -a x86_mscoff serve-d`

よくわからん。

### `cs` omnisharp

`omnisharp -lsp`

初期化がうまくいかず。

`Initialize` の送り方が違う？

