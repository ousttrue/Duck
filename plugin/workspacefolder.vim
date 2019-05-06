if exists('g:loaded_workspacefolder')
    finish
endif
let g:loaded_workspacefolder = 1

let g:WF_SERVER_REQUEST = 'SERVER_REQUEST'
let g:WF_SERVER_RESPONSE = 'SERVER_RESPONSE'
let g:WF_SERVER_ERROR = 'SERVER_ERROR'
let g:WF_SERVER_NOTIFY = 'SERVER_NOTIFY'
let g:WF_CLIENT_REQUEST = 'CLIENT_REQUEST'
let g:WF_CLIENT_RESPONSE = 'CLIENT_RESPONSE'
let g:WF_CLIENT_ERROR = 'CLIENT_ERROR'
let g:WF_CLIENT_NOTIFY = 'CLIENT_NOTIFY'


augroup WorkspaceFolder
    autocmd!
    autocmd FileType python call wf#lsp#documentOpen()
    "autocmd CursorMoved *.py call wf#lsp#highlight()
    autocmd TextChanged *.py call wf#lsp#documentChange()
    autocmd InsertLeave *.py call wf#lsp#documentChange()
    autocmd BufEnter *.py call wf#lsp#diagnostics#updateLocList()
augroup END


call wf#rpc#register_notify_callback('textDocument/publishDiagnostics', function('wf#lsp#diagnostics#receive'))

