if exists('g:loaded_workspacefolder')
    "finish
endif
let g:loaded_workspacefolder = 1

augroup WorkspaceFolder
    autocmd!
    autocmd FileType * call wf#lsp#setFileType()
    autocmd CursorMoved * call wf#lsp#highlight()
augroup END

" diagnostics {{{
" reference
" https://github.com/w0rp/ale/blob/master/autoload/ale/lsp/response.vim

" Constants for message severity codes.
let s:SEVERITY_ERROR = 1
let s:SEVERITY_WARNING = 2
let s:SEVERITY_INFORMATION = 3
let s:SEVERITY_HINT = 4

function! s:on_diagnostics(params)
    " file:///C:/tmp/file.txt
    let l:bufnr = bufnr('^' . a:params.uri[8:] . '$')
    if l:bufnr == -1
        return
    endif

    let l:loclist = []

    for l:diagnostic in a:params.diagnostics
        let l:severity = get(l:diagnostic, 'severity', 0)
        let l:loclist_item = {
                    \ 'bufnr': l:bufnr,
                    \ 'text': substitute(l:diagnostic.message, '\(\r\n\|\n\|\r\)', ' ', 'g'),
                    \ 'type': 'E',
                    \ 'lnum': l:diagnostic.range.start.line + 1,
                    \ 'col': l:diagnostic.range.start.character + 1,
                    \ 'end_lnum': l:diagnostic.range.end.line + 1,
                    \ 'end_col': l:diagnostic.range.end.character,
                    \}

        if l:severity == s:SEVERITY_WARNING
            let l:loclist_item.type = 'W'
        elseif l:severity == s:SEVERITY_INFORMATION
            " TODO: Use 'I' here in future.
            let l:loclist_item.type = 'W'
        elseif l:severity == s:SEVERITY_HINT
            " TODO: Use 'H' here in future
            let l:loclist_item.type = 'W'
        endif

        if has_key(l:diagnostic, 'code')
            if type(l:diagnostic.code) == v:t_string
                let l:loclist_item.code = l:diagnostic.code
            elseif type(l:diagnostic.code) == v:t_number && l:diagnostic.code != -1
                let l:loclist_item.code = string(l:diagnostic.code)
                let l:loclist_item.nr = l:diagnostic.code
            endif
        endif

        if has_key(l:diagnostic, 'source')
            let l:loclist_item.detail = printf(
                        \   '[%s] %s',
                        \   l:diagnostic.source,
                        \   l:diagnostic.message
                        \)
            let l:loclist_item.text = printf(
                        \   '[%s] %s',
                        \   l:diagnostic.source,
                        \   l:loclist_item.text
                        \)
        endif

        call add(l:loclist, l:loclist_item)
    endfor

    let l:winid = bufwinid(l:bufnr)
    call setloclist(l:winid, l:loclist)
    lopen
endfunction


call wf#rpc#register_notify_callback('textDocument/publishDiagnostics', function('s:on_diagnostics'))
" }}}
