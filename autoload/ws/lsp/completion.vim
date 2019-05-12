let s:context = {
            \   'id': 0,
            \ }

function! s:_complete(start, items) abort
    let l:completion = []

    for l:item in a:items
        call add(l:completion, l:item.insertText)
    endfor

    call complete(a:start, l:completion)
endfunction

function! s:complete(context, ret) abort
    if a:context.id != s:context.id
        return
    endif

    let l:t = type(a:ret)
    let l:start = s:context.start + 1
    if l:t==7
        return
    elseif l:t==3
        " list
        call s:_complete(l:start, a:ret)
    elseif l:t==4
        " dict
        call s:_complete(l:start, a:ret.items)
    endif
endfunction

function! ws#lsp#completion#complete(findstart, base) abort
    if a:findstart
        let l:line = getline('.')
        let l:col = col('.')
        let l:start = l:col - 1
        while l:start > 0 && l:line[l:start - 1] =~ '\a'
            let l:start -= 1
        endwhile
        let s:context = {
                    \   'id' : s:context.id + 1,
                    \   'path' : expand('%:p'),
                    \   'line' : line('.')-1,
                    \   'col' : l:col,
                    \   'start': l:start,
                    \ }
        return s:context.col
    endif

    " sync current text
    call ws#documentChange()

    " send request
    call ws#rpc#request(function('s:complete', [s:context]),
                \ 'request_document_completion',
                \ s:context.path,
                \ s:context.line,
                \ s:context.col)

    return []
endfunction
