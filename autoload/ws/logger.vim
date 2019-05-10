let s:BUFFER_NAME = 'WS_LOGGER'

let s:log_list = []

function! ws#logger#show()
    " show
    call ws#buffer#get_or_create(s:BUFFER_NAME)

    let l:current = ws#buffer#begin(s:BUFFER_NAME)

    " clear
    normal %d

    " update
    for l:log in s:log_list
        call append(line('$'), l:log)
    endfor

    call ws#buffer#end(l:current)
endfunction

" log {{{
function! ws#logger#log(kind, msg)
    let l:time = strftime("%H:%M:%S")
    if a:kind == g:WS_SERVER_REQUEST
        let l:item = printf("[%s]%d-> %s", l:time, a:msg.id, a:msg.method)
    elseif a:kind == g:WS_SERVER_RESPONSE
        let l:item = printf("[%s]%d-> %s", l:time, a:msg.id, a:msg.result)
    elseif a:kind == g:WS_SERVER_ERROR
        let l:item = printf("[%s]%dE> %s", l:time, a:msg.id, a:msg.error)
    elseif a:kind == g:WS_SERVER_NOTIFY
        let l:item = printf("[%s]--> %s", l:time, a:msg.method)
    elseif a:kind == g:WS_CLIENT_REQUEST
        let l:item = printf("[%s]<-%d %s", l:time, a:msg.id, a:msg.method)
    elseif a:kind == g:WS_CLIENT_RESPONSE
        let l:item = printf("[%s]<-%d %s", l:time, a:msg.id, a:msg.result)
    elseif a:kind == g:WS_CLIENT_ERROR
        let l:item = printf("[%s]<E%d %s", l:time, a:msg.id, a:msg.error)
    elseif a:kind == g:WS_CLIENT_NOTIFY
        let l:item = printf("[%s]<-- %s", l:time, a:msg.method)
    else
        let l:item = printf("[%s][unknown] %s", l:time, a:msg)
    endif

    call add(s:log_list, l:item)
endfunction
" }}}

" clear {{{
function! ws#logger#clear()
    let s:log_list = []
endfunction
" }}}
