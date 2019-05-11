function! ws#position#keep(callback)
    " save
    let l:col = col('.')
    let l:line = line('.')
    let l:bufnr = bufnr('%')
    let l:wid = win_getid()
    "echom printf('<= %d:%d:%d, %d', l:wid, l:bufnr, l:line, l:col)

    call a:callback()

    call win_gotoid(l:wid)
    execute printf('%db', l:bufnr)
    call setpos('.', [l:bufnr, l:line, l:col, 0])
    "echom printf('=> %d:%d:%d, %d', l:wid, l:bufnr, l:line, l:col)
endfunction

function! ws#position#goto(uri, line, col)
    let l:path = a:uri[8:]
    let l:bufnr = bufnr(l:path)
    if l:bufnr == -1
        " new buffer
        let l:cmd=printf(":e +%d %s", a:line, l:path)
    else
        " exists buffer
        let l:cmd=printf(":%db +%d", l:bufnr, a:line)
    endif

    echom l:cmd
    execute l:cmd
endfunction
