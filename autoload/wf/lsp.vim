function! wf#lsp#setFileType()
    let l:path = expand('%:p')
    call wf#rpc#notify('document_open', l:path)
endfunction
