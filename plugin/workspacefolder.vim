if exists('g:loaded_workspacefolder')
    finish
endif
let g:loaded_workspacefolder = 1

let g:WS_SERVER_REQUEST = 'SERVER_REQUEST'
let g:WS_SERVER_RESPONSE = 'SERVER_RESPONSE'
let g:WS_SERVER_ERROR = 'SERVER_ERROR'
let g:WS_SERVER_NOTIFY = 'SERVER_NOTIFY'
let g:WS_CLIENT_REQUEST = 'CLIENT_REQUEST'
let g:WS_CLIENT_RESPONSE = 'CLIENT_RESPONSE'
let g:WS_CLIENT_ERROR = 'CLIENT_ERROR'
let g:WS_CLIENT_NOTIFY = 'CLIENT_NOTIFY'


augroup WorkspaceFolder
    autocmd!
    autocmd FileType python call ws#lsp#documentOpen()
    "autocmd CursorMoved *.py call ws#lsp#highlight()
    autocmd TextChanged *.py call ws#lsp#documentChange()
    autocmd InsertLeave *.py call ws#lsp#documentChange()
    autocmd BufEnter *.py call ws#lsp#diagnostics#updateLocList()
augroup END


call ws#rpc#register_notify_callback('textDocument/publishDiagnostics', function('ws#lsp#diagnostics#receive'))

