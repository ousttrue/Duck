function! s:is_null_or_empty(ret) abort
    let l:t = type(a:ret)
    if l:t==7
        return 1
    elseif l:t==3
        return len(a:ret)==0
    elseif l:t==4
        return len(a:ret)==0
    endif
    echom printf("is_null_or_empty: %s",a:ret)
    return 0
endfunction

function! s:prepare_preview(bufname) abort
    call ws#buffer#get_or_create(a:bufname)
    let l:current = ws#buffer#begin(a:bufname)

        let &l:filetype = 'markdown'
        " clear
        normal %d

    call ws#buffer#end(l:current)

    " show in preview
    execute printf('pedit %s', expand('%'))
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" open & change
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
function! ws#documentOpen() abort
    let l:path = expand('%:p')
    let l:text = ws#buffer#get_text()
    call ws#rpc#notify('notify_document_open', l:path, l:text)
endfunction

function! ws#documentChange() abort
    echom "didChange"
    let l:path = expand('%:p')
    let l:text = ws#buffer#get_text()
    call ws#rpc#notify('notify_document_change', l:path, l:text)
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" diagnostics & highlight
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
function! ws#updateLocList()
    call ws#lsp#diagnostics#updateLocList()
endfun

function! s:highlight(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif
    "echo printf("highlight: %s", a:ret)
endfunction

function! ws#highlight() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1
    call ws#rpc#request(function('s:highlight'), 'request_document_highlight', l:path, l:line, l:col)
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" defnition
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
function! s:goto(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif

    let l:pos = a:ret[0]
    " echom printf("goto %s", l:pos)
    let l:start = l:pos.range.start
    call ws#position#goto(l:pos.uri, l:start.line+1, l:start.character+1)
endfunction

function! ws#gotoDefinition() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1
    call ws#rpc#request(function('s:goto'),
                \ 'request_document_definition', l:path, l:line, l:col)
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" references
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
let s:REFENRECES_BUFFER = 'WS_REFERNCES'

function! s:to_path(uri) abort
    return printf("%s%s", toupper(a:uri[8]), a:uri[9:])
endfunction

function! s:references_preview(items)
    call ws#buffer#get_or_create(s:REFENRECES_BUFFER)
    let l:current = ws#buffer#begin(s:REFENRECES_BUFFER)

    " clear
    normal %d
    " update

    echom getcwd()
    for l:item in a:items
        let l:name = fnamemodify(s:to_path(l:item.uri), ':~:.')
        let l:item = printf("%s: %s", l:name, l:item.range.start)
        silent put =l:item
    endfor
    " Delete first empty line
    0delete _

    call ws#buffer#end(l:current)
endfunction

function! s:references(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif

    if !len(a:ret)
        return
    endif

    call ws#position#keep(function('s:references_preview', [a:ret]))
endfunction

function! ws#references() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1

    " prepare preview
    call ws#position#keep(function('s:prepare_preview', [s:REFENRECES_BUFFER]))

    call ws#rpc#request(function('s:references'),
                \ 'request_document_references', l:path, l:line, l:col)
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" hover
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
let s:HOVER_BUFFER = 'WS_HOVER'
function! s:hover_preview(contents) abort
    call ws#buffer#get_or_create(s:HOVER_BUFFER)
    let l:current = ws#buffer#begin(s:HOVER_BUFFER)

    " clear
    normal %d
    silent put =a:contents
    " Delete first empty line
    0delete _

    call ws#buffer#end(l:current)
endfunction

function! s:hover(ret) abort
    if s:is_null_or_empty(a:ret)
        " no result
        return
    endif
    if !len(a:ret.contents)
        return
    endif

    call ws#position#keep(function('s:hover_preview', [a:ret.contents]))
endfunction

function! ws#hover() abort
    let l:path = expand('%:p')
    let l:line = line('.')-1
    let l:col = col('.')-1

    " prepare preview
    call ws#position#keep(function('s:prepare_preview', [s:HOVER_BUFFER]))

    call ws#rpc#request(function('s:hover'),
                \ 'request_document_hover', l:path, l:line, l:col)
endfunction

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" completion
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
function! ws#complete(findstart, base) abort
    return ws#lsp#completion#complete(a:findstart, a:base)
endfunction

