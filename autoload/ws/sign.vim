sign define ws_error text=EE texthl=ErrorMsg
sign define ws_warning text=WW texthl=WarningMsg
sign define ws_info text=II


let s:signs = []
let s:first_id = 5000


function! ws#sign#apply(list, path) abort

    call ws#sign#clear()

    let l:id = s:first_id

    for l:item in a:list
        execute printf(":sign place %d line=%d name=%s file=%s", 
                    \ l:id, l:item.lnum, "ws_error", a:path)
        call add(s:signs, l:id)

        let l:id += 1
    endfor

endfunction

function! ws#sign#clear() abort

    for l:id in s:signs
        execute printf(":sign unplace %d", l:id)
    endfor
    let s:signs = []

endfunction

