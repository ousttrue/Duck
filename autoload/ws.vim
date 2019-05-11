" interfaces for ws

function! ws#documentOpen() abort
    call ws#lsp#documentOpen()
endfunction

function! ws#documentChange() abort
    call ws#lsp#documentChange()
endfunction

function! ws#updateLocList()
    call ws#lsp#diagnostics#updateLocList()
endfun

function! ws#gotoDefinition() abort
    call ws#lsp#gotoDefinition()
endfunction

function! ws#hover() abort

endfunction

function! ws#references() abort

endfunction

function! ws#complete(findstart, base) abort
    return ws#lsp#complete(a:findstart, a:base)
endfunction
