function! ws#buffer#bufnr(path) abort
    let l:nr = bufnr(a:path)
    if l:nr!=-1
        return l:nr
    endif

    return -1
endfunction

" 指定の名前のバッファを得て編集可能にし・・・
function! ws#buffer#begin(name) abort
    let l:current = bufnr('%')
    call ws#buffer#get_or_create(a:name)
    setlocal buflisted modifiable noreadonly
    return l:current
endfunction

" 編集不可にして元のアクティブバッファを復旧する
function! ws#buffer#end(current) abort
    setlocal nobuflisted nomodifiable readonly
    execute printf("b%d", a:current)
endfunction

"
" カレントバッファが空か調べる
"
function! ws#buffer#is_empty() abort
    let l:lines = getline(1, '$')
    if len(l:lines)>1
        return 0
    endif

    return len(l:lines[len(l:lines)-1]) == 0
endfunction


function! s:new_buffer(name) abort
    enew
    exec printf(':file %s', a:name)

    echom printf('current %d', bufnr('%'))

    setlocal noshowcmd
    setlocal noswapfile
    setlocal buftype=nofile
    setlocal bufhidden=delete
    setlocal nobuflisted
    setlocal nomodifiable
    setlocal nowrap
    setlocal nonumber
    setlocal readonly
    " set up syntax highlighting
    if has("syntax")
        syn clear
        " syn match BufferNormal /  .*/
        " syn match BufferSelected /> .*/hs=s+1
        " hi def BufferNormal ctermfg=black ctermbg=white
        " hi def BufferSelected ctermfg=white ctermbg=black
    endif

    " set up the keymap
    noremap <silent> <buffer> q :close<CR>

    " cursor move
    " nnoremap <silent> <buffer> j j<C-R>=<SID>draw_cursor(line('.'))<CR>
    " nnoremap <silent> <buffer> k k<C-R>=<SID>draw_cursor(line('.'))<CR>
    " nnoremap <silent> <buffer> <Home> gg<C-R>=<SID>draw_cursor(line('.'))<CR>
    " nnoremap <silent> <buffer> <End> G<C-R>=<SID>draw_cursor(line('.'))<CR>
    nmap <silent> <buffer> <Down> j
    nmap <silent> <buffer> <Up> k

    " disable keys
    map <buffer> h <Nop>
    map <buffer> l <Nop>
    map <buffer> <Left> <Nop>
    map <buffer> <Right> <Nop>
    map <buffer> i <Nop>
    map <buffer> a <Nop>
    map <buffer> I <Nop>
    map <buffer> A <Nop>
    map <buffer> o <Nop>
    map <buffer> O <Nop>
endfunction


" 指定の名前のbufferがあればそれをアクティブにする。
" 無ければ新規に作成し、それがアクティブになる。
function! ws#buffer#get_or_create(name) abort
    let l:nr = bufnr(a:name)
    if bufexists(l:nr)
        echom printf('%d: get %s', l:nr, a:name)
        exec printf(':b%d', l:nr)
    else
        echom printf('%d: create %s', l:nr, a:name)
        call s:new_buffer(a:name)
    endif
endfunction

