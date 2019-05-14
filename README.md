# WorkspaceFolder

Debug depends on build, build depends on code, and code depends on the root path(workspaceFolder).

vimでDebugAdapterを駆動するバックエンドを作る計画。

Python-3.7

## コマンドライン

```
usage: ws [-h] [--logfile LOGFILE] [--debug] [--rpc]
          [task [task ...]]
```

### `--logging`

* ⭕️ ロギングしてデバッグの助けにする。
* ⭕️ http splitter
* 🔨 出力パスをproject_rootに決め打ちする
* 🔨 LSPロギング(JSON-RPC) `root/.ws/YYYYMMDD.python.lsplog`
* 🔨 ログからlspを自動運転できるようにする
* 🔨 DAPロギング `root/.ws/YYYYMMDD.python.daplog`
* 🔨 ログからdapを自動運転できるようにする

### `--rpc`

* ⭕️ vimのjob経由で起動するモード。
* ⭕️ 標準入出力から接続する。
* ⭕️ JSON-RPC on HTTPもどき(Content-Lengthヘッダのみ)

### `task`

`task` 引数をtask名として順番に実行する。

* ⭕️ レジストリ経由でcmake, MSBuild 等を発見する能力。vswhere。
* タスクの実行
    * ⭕️ make, dub, MSBuild 等の呼び出し代行。
    * ⭕️ cmake, premake。プロジェクトやソリューション、Makefileの生成。
    * ⭕️ タスクの依存関係
* 🔨 vsvars.bat から環境変数を取り込む
* 🔨 実行時の環境変数のコントロール
* ⭕️ mingwのtoolchain選択
* ⭕️ 実行ログ
* ⭕️ Workspace.toml に記述されたtaskを実行する。
* [Workspace.toml](./neovim/Workspace.toml)

```toml
# Workspace.toml

[[tasks]]
name = 'deps_cmake' # required
depends = ['clone']
cwd = 'neovim/.deps' # mkdir & chdir
command = ['cmake', '../third-party', '-G', 'Visual Studio 15 2017 Win64']
```

## vimplugin

* ⭕️ job で起動する
* ⭕️ transportは、 `LSP` と同じ `HTTP-keepalive` 的なストリーム
* ⭕️ protocolは、 `JSON-RPC`

## DAP

https://microsoft.github.io/debug-adapter-protocol/overview

* 🔨 VSCodeの拡張を起動して、標準入出力から制御する。
* 🔨 vimのjob経由で起動する。
* 🔨 Workspace.tomlに起動内容を記述
* 🔨 breakpoint管理

## LSP

https://microsoft.github.io/language-server-protocol/

* ⭕️ vimのjob経由で起動する。
* ⭕️ project root。親フォルダを遡りながら確定させる。
    * `python` setup.py
    * `d` dub.json
    * `cs` *.csproj

### 通信ログのバッファ

* ⭕️ wfとのJSON-RPC通信のログを表示
* ⭕️ document毎の表示する

### 状態表示

* 🔨 state管理(stopped, starting, run)
* 🔨 workspace(rootpath, language)
* 🔨 document(relative path from rootpath)

### Workspaceの管理

* ⭕️ 違うフォルダのプロジェクトを開いたときに新しいworkspaceとして、別のlspプロセスを起動する

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
* 🔨 前のRequestが終わっていない時のキャンセル

### `textDocument/publishDiagnostics`

* ⭕️ receive
* ⭕️ location list
* ⭕️ buffer切り替え時に復旧する
* ⭕️ gutter

### `textDocument/highlight`

* 🔨 前のRequestが終わっていない時のキャンセル

### `textDocument/hover`

* ⭕️ `call ws#hover`
* 🔨 前のRequestが終わっていない時のキャンセル

### `textDocument/references`

* ⭕️ `call ws#references`
* 🔨 jump list(LocationListに一時的に出す？)
* 🔨 前のRequestが終わっていない時のキャンセル

### `textDocument/completion`

* ⭕️ omnifunc
* 🔨 kind
* 🔨 menu
* 🔨 detail(signature)
* 🔨 documentation(preview)
* 🔨 前のRequestが終わっていない時のキャンセル

### `textDocument/symbol`

### `textDocument/rename`

### `textDocument/formatter`

## LanguageServer

使ってみたサーバー。
アタッチしてデバッグできる言語じゃないと、うまくいかないときどうしようもない。

### `python`

#### pyls

https://github.com/palantir/python-language-server

```
[mypy] No parent module -- cannot perform relative import
```

相対import使用時に回避不能。

https://github.com/tomv564/pyls-mypy/issues/17

mypyの `--command` 引数を使う場合に、mypyにソースのファイルパスを渡す方法を追加してやる必要がある。
`pyls-mypy` で `mypy` にモンキーパッチか

* ⭕️ gotoDefinition
* ⭕️ references
* ⭕️ hover
* ⭕️ diagonostics
* ⭕️ completion

### `d`
#### dls

`dub run dls`

dub.json のある階層に chdir する必要がある？

* 🔨 gotoDefinition(初回だけ動く？)
* 🔨 references
* 🔨 hover
* ⭕️ diagonostics
* 🔨 completion

#### serve-d

`dub run -a x86_mscoff serve-d`

よくわからん。

### `csharp`
#### omnisharp

`omnisharp -lsp`

初期化がうまくいかず。

`Initialize` の送り方が違う？

Extension

https://www.nuget.org/packages/OmniSharp.Extensions.JsonRpc/


になっているらしい。どうやって有効にするのか。

マスターをビルドして、 `OmniSharp.exe -lsp` でよさそうだなのだが・・・。

`./build.ps1 -taget Quick` でビルドできる。

`http` 版と `stdio` 版があって、stdio版が目的のもの。
こいつに、 `-lsp` 引数をつけるのだが・・・

https://github.com/OmniSharp/omnisharp-vim/issues/451

> OmniSharp-roslyn does have an LSP implementation, but it's not complete yet. However OmniSharp-vim and OmniSharp-roslyn predate LSP and still communicate using their older protocols.

OmniSharp-vim は古いプロトコルを使っていると言うておるな。

`OmniSharp-vim` の動作条件は、 `*.sln` の存在だった。

OmniSharp-roslyn にアタッチしてデバッグしないと無理。

した。

initialize引数の textcapablity と workspacecapblity を非null( `{}` でよい)にしないと NullReferenceExcepion で初期化に失敗する。

* ⭕️ gotoDefinition
* ⭕️ references
* ⭕️ hover
* ⭕️ diagonostics
* 🔨 completion IndexOutOfRangeException LspRequestRouter.cs: 161

requestがちゃんと帰ってくるようになるまでちょっと時間がかかる。
15秒くらい？

### fsharp

#### fhsarp-language-server

https://github.com/fsprojects/fsharp-language-server

### node-js

### typescript

### clang

