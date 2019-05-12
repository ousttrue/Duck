function! ws#loclist#apply(list, winid, bufnr)

    " bufnrを投入
    let l:loclist = []
    for l:item in a:list
        let l:item.bufnr = a:bufnr

        call add(l:loclist, l:item)
    endfor

    " loclistに反映
    call setloclist(a:winid, l:loclist)

    " 開く
    if len(l:loclist)>0
        call ws#position#keep({ -> execute('lopen 4')})
    endif

endfunction
