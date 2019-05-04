let s:wf = fnamemodify(expand('<sfile>'), ':h:h') . '/workspacefolder/__init__.py'

function! wf#stop() abort
    call wf#rpc#stop()
endfunction

function! wf#start() abort
    call wf#stop()

    let l:argv = [g:python3_host_prog, '-u', s:wf, '--rpc', '--debug']
    call wf#rpc#start(l:argv)

    " debug
    call wf#rpc#request({value -> execute(printf(':echoerr " = %d"', value))}, 'add', 1, 2)
endfunction

