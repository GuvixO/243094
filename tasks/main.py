import inspect

from tasks.core import main, pool
from tasks.driver import COMMANDS# --------------- Задание 1.1 --------------- #
import json
with open('config.json', 'r', encoding='utf-8') as f: #открыли файл с данными
    text = json.load(f)

DISPLAY = text['display']['show']
DISPLAY_MARGIN = text['display']['margin']
PREFIX = text['prefix']


if __name__ == '__main__':
    main.configure(
        display=DISPLAY,
        display_margin=DISPLAY_MARGIN,
        base_prefix=PREFIX,
        commands=COMMANDS
    )
    while True:
        main.execute(pool.next())
