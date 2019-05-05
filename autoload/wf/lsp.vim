function! wf#lsp#setFileType()
    let l:path = expand('%:p')
    call wf#rpc#notify('notify_document_open', l:path)
endfunction

function! s:goto(ret)
    echom printf("goto: %s", a:ret)
endfunction

function! wf#lsp#gotoDefinition()
    let l:path = expand('%:p')
    let l:line = line('.')
    let l:col = col('.')
    call wf#rpc#request(function('s:goto'), 'request_document_definition', l:path, l:line, l:col)
endfunction
