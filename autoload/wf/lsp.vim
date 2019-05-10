function! s:is_null_or_empty(ret) abort
    let l:t = type(a:ret)
    if l:t==7
        return 1
    endif
    if l:t==3
        return len(a:ret)==0
    endif
    echom printf("%s",a:ret)
    return 0
endfunction

function! s:get_buffer_text() abort
    if &fileformat == 'unix'
        let line_ending = "\n"
    elseif &fileformat == 'dos'
        let line_ending = "\r\n"
    elseif &fileformat == 'mac'
        let line_ending = "\r"
    else
        echoerr "unknown value for the 'fileformat' setting: " . &fileformat
    endif
    return join(getline(1, '$'), line_ending).line_ending
endfunction

function! wf#lsp#documentOpen() abort
    let l:path = expand('%:p')
    let l:text = s:get_buffer_text()
    call wf#rpc#notify('notify_document_open', l:path, l:text)
endfunction

" goto definition {{{
function! s:goto(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif

    let l:pos = a:ret[0]
    " echom printf("goto %s", l:pos)
    call wf#position#goto(l:pos.uri, l:pos.range.start.line+1, l:pos.range.start.character+1)
endfunction

function! wf#lsp#gotoDefinition() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1
    call wf#rpc#request(function('s:goto'), 'request_document_definition', l:path, l:line, l:col)
endfunction
" }}}

" highlight {{{
function! s:highlight(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif
    "echo printf("highlight: %s", a:ret)
endfunction

function! wf#lsp#highlight() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1
    call wf#rpc#request(function('s:highlight'), 'request_document_highlight', l:path, l:line, l:col)
endfunction
" }}}

" did change {{{

function! wf#lsp#documentChange() abort
    echom "didChange"
    let l:path = expand('%:p')
    let l:text = s:get_buffer_text()
    call wf#rpc#notify('notify_document_change', l:path, l:text)
endfunction

" }}}
