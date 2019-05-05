function! wf#lsp#setFileType() abort
    let l:path = expand('%:p')
    call wf#rpc#notify('notify_document_open', l:path)
endfunction

function! s:is_null_or_empty(ret) abort
    let l:t = type(a:ret)
    if l:t==7
        return 1
    endif
    if l:t==3
        return len(a:ret)==0
    endif
    return 0
endfunction

function! s:goto(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif

    " ToDo: tagjump
    let l:pos = a:ret[0]
    call cursor(l:pos.range.start.line+1, l:pos.range.start.character+1)
endfunction

function! wf#lsp#gotoDefinition() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1
    call wf#rpc#request(function('s:goto'), 'request_document_definition', l:path, l:line, l:col)
endfunction

function! s:highlight(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif
    echo printf("highlight: %s", a:ret)
endfunction

function! wf#lsp#highlight() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1
    call wf#rpc#request(function('s:highlight'), 'request_document_highlight', l:path, l:line, l:col)
endfunction
