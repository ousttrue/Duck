let s:wf = fnamemodify(expand('<sfile>'), ':h:h') . '/workspacefolder/__init__.py'

function! wf#stop()
    if !exists('s:jobid')
        echom 'no job'
        return
    end

    call async#job#stop(s:jobid)
    echom printf('stop %d', s:jobid)
    let s:jobid=0
endfunction

function! wf#start()
    call wf#stop()

    let l:argv = [g:python3_host_prog, '-u', s:wf, 'wrap', 'pyls']
    echo l:argv

    let s:jobid = async#job#start(l:argv, {
        \ 'on_stdout': function('s:on_stdout'),
        \ 'on_stderr': function('s:on_stderr'),
        \ 'on_exit': function('s:on_exit'),
    \ })

    if !s:jobid
        echom 'job failed to start'
        return
    endif

    echom printf('job started: %d', s:jobid)
endfunction

function! s:on_stdout(job_id, data, event_type)
    echom printf('-->%s', a:data)
endfunction

function! s:on_stderr(job_id, data, event_type)
    echom printf('EE>%s', a:data)
endfunction

function! s:on_exit(job_id, data, event_type)
    if a:job_id == s:jobid
        echom printf('%d exit', a:job_id)
        let s:jobid=0
    else
        echom printf('unknown %d exit', a:job_id)
    endif
endfunction

