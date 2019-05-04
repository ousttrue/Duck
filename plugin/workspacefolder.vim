if exists('g:loaded_workspacefolder')
    "finish
endif
let g:loaded_workspacefolder = 1

augroup WorkspaceFolder
    autocmd!
    autocmd FileType * call wf#lsp#setFileType()
augroup END

