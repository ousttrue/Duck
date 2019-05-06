function! wf#position#save()
    let s:wid = win_getid()
    let s:pos = getcurpos()
endfunction

function! wf#position#restore()
    call win_gotoid(s:wid)
    call setpos('.', s:pos)
endfunction

function! wf#position#goto(uri, line, col)
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
