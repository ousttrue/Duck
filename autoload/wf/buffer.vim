function! wf#buffer#bufnr(path)
    let l:nr = bufnr(a:path)
    if l:nr!=-1
        return l:nr
    endif

    return -1
endfunction
