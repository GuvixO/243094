use LINES
    macro COUNT
        set_cmd LINES
            total
        set_eval LINES
            {LINES}[0]
        stop

    macro COMMENT_LINE
        home
        type_inline # 
        down
        stop

    move 0 0
    repeat COUNT 1
    repeat COMMENT_LINE {LINES}
    stop