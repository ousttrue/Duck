if exists('g:loaded_workspacefolder')
    "finish
endif
let g:loaded_workspacefolder = 1

augroup WorkspaceFolder
    autocmd!
    autocmd FileType * call wf#lsp#setFileType()
    autocmd CursorMoved * call wf#lsp#highlight()
augroup END

function! s:on_diagnostics(diagnostics)
    echom printf("diagnostics: %s", a:diagnostics)
endfunction

call wf#rpc#register_notify_callback('textDocument/publishDiagnostics', function('s:on_diagnostics'))

