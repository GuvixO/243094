import inspect

from tasks.core import main, pool
from tasks.driver import COMMANDS

# --------------- Задание 1.1 --------------- #

DISPLAY = ...
DISPLAY_MARGIN = ...
PREFIX = ...


if __name__ == '__main__':
    main.configure(
        display=DISPLAY,
        display_margin=DISPLAY_MARGIN,
        base_prefix=PREFIX,
        commands=COMMANDS
    )
    while True:
        main.execute(pool.next())
