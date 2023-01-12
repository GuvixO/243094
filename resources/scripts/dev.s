use TIMES CHAR
    set_str CHAR a

    macro TAIL
        exec pool.put(list(pool.commands)[-6:-1])
        eval len(pool.commands)
        stop
    
    repeat TAIL {TIMES}
    
    exec main.execute(pool.commands[0])
    type_inline {CHAR}
    set_eval CHAR
        chr(ord('{CHAR}') + 1)
    newline
    
    stop