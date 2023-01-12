use LINES LINE
    macro COUNT
        set_cmd LINES
            total
        set_eval LINES
            {LINES}[0]
        stop
        
    macro LINE
        set_cmd LINE
            cursor
        set_eval LINE
            {LINE}[0]
        stop

    macro UNCOMMENT_LINE
        repeat LINE 1
        move {LINE} 2
        backspace 2 
        down
        stop

    move 0 0
    repeat COUNT 1
    repeat UNCOMMENT_LINE {LINES}
    stop