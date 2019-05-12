" document毎に保存しておく
let s:diagnostics_map = {}


" reference
" https://github.com/w0rp/ale/blob/master/autoload/ale/lsp/response.vim

" Constants for message severity codes.
let s:SEVERITY_ERROR = 1
let s:SEVERITY_WARNING = 2
let s:SEVERITY_INFORMATION = 3
let s:SEVERITY_HINT = 4


" カレントバッファに対するdiagnosticsリストをLocationListに投入する
function! ws#lsp#diagnostics#updateLocList()
    let l:path = fnamemodify(expand("%"), ":p")
    let l:path = substitute(l:path, "\\", "/", "g")
    let l:bufnr = bufnr("%")
    let l:winid = bufwinid(l:bufnr)
    let l:what = { 'title': 'diagnostics' }
    if !has_key(s:diagnostics_map, l:path)
        "echo printf("%s not found", l:path)
        call setloclist(l:winid, [])
        return
    endif
    let l:list = s:diagnostics_map[l:path]

    call ws#loclist#apply(l:list, l:winid, l:bufnr)
    call ws#sign#apply(l:list, l:path)
endfunction

function! ws#lsp#diagnostics#receive(params)
    " file:///C:/tmp/file.txt
    let l:path = a:params.uri[8:]

    let l:loclist = []
    for l:diagnostic in a:params.diagnostics
        let l:severity = get(l:diagnostic, 'severity', 0)
        let l:loclist_item = {
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

    let s:diagnostics_map[l:path] = l:loclist

    "echo printf("notify: %s %d items", l:path, len(l:loclist))
    if mode() == 'n'
        call ws#lsp#diagnostics#updateLocList()
    endif

endfunction
