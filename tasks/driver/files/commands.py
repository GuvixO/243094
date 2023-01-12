from __future__ import annotations

import os
import sys

from tasks.core import data, pool, main
from tasks.driver.utils import requires_data, greedy


# --------------- Задание 2.0 --------------- #

def _cmd_example():
    # TODO сотрите эту строку, чтобы добавить команду
    main.report('Команда-пример, выводит это сообщение')


def _cmd_example_square(arg: int):
    # TODO сотрите эту строку, чтобы добавить команду
    return arg ** 2


def _cmd_exit():
    sys.exit(0)


# --------------- Задание 2.1 --------------- #

def _cmd_clear():
    data.lines = ['']
    data.cursor = (0, 0)


def _cmd_discard():
    data.lines = None
    data.cursor = (None, None)


def _cmd_read(filename: str):
    if not os.path.exists(filename):
        return main.report(f'Файл `{filename}` не существует')

    # TODO реализуйте заполнение `data` данными из файла `filename`

    main.report(f'Прочитано {len(data)} строк')


@requires_data
def _cmd_save(filename: str):
    # TODO реализуйте сохранение строк из `data` в файл `filename`

    main.report(f'Сохранено {len(data)} строк')


# --------------- Задание 2.2 --------------- #

@requires_data
def _cmd_total():
    line_count, total_count = len(data), sum(map(len, data.lines))
    return line_count, total_count


@requires_data
def _cmd_cursor():
    return data.cursor


@requires_data
def _cmd_linewidth(line_number: int):
    return len(data[line_number])


@requires_data
def _cmd_show(from_line: int, to_line: int):
    if from_line not in range(len(data)):
        return main.report('Некорректный номер начальной строки')
    if to_line not in range(len(data)):
        return main.report('Некорректный номер конечной строки')

    # TODO реализуйте вывод строк в редакторе


# --------------- Задание 2.3 --------------- #

@requires_data
def _cmd_home():
    data.x = 0


@requires_data
def _cmd_end():
    data.x = len(data.line)


@requires_data
def _cmd_down():
    data.y = min(data.y + 1, len(data) - 1)
    data.x = min(data.x, len(data.line))


@requires_data
def _cmd_up():
    data.y = max(data.y - 1, 0)
    data.x = min(data.x, len(data.line))


@requires_data
def _cmd_move(line: int, position: int):
    if line not in range(len(data)):
        return main.report('Некорректный номер строки')
    if position not in range(len(data[line]) + 1):
        return main.report(f'Некорректная позиция внутри строки')

    data.cursor = (line, position)


@requires_data
def _cmd_newline():
    # TODO реализуйте перевод строки
    pass


@greedy
@requires_data
def _cmd_type_inline(insertion: str):
    # TODO реализуйте добавление текста `insertion` в `data
    pass


@requires_data
def _cmd_type():
    insertion = input()
    _cmd_type_inline(insertion)


# --------------- Задание 2.4 --------------- #

@requires_data
def _cmd_backspace(count: int):
    # TODO реализуйте удаление символов из `data` слева от курсора
    pass


@greedy
@requires_data
def _cmd_find_inline(text: str):
    # TODO реализуйте поиск строки `text` в `data` 
    # (оставьте `return 'Не найдено'`, когда `text` нет в `data`)
    return 'Не найдено'


@requires_data
def _cmd_find():
    text = input()
    return _cmd_find_inline(text)


# --------------- Задание 2.5 --------------- #

def _cmd_macro(name: str):
    script = []
    with pool.scope():
        while True:
            command = pool.next()
            if command == 'stop':
                break
            script.append(command)
    main.macros[name] = script


def _cmd_repeat(macro: str, times: int):
    if macro not in main.macros:
        return main.report(f'Нет макро с именем `{macro}`')

    for _ in range(times):
        pool.put(main.macros[macro])


def _cmd_execute(filename: str):
    if not os.path.exists(filename):
        return main.report(f'Файл `{filename}` не существует')
    
    # TODO реализуйте чтение скрипта из `filename` и добавление его команд в `pool`


# --------------- Задание 2.* --------------- #

def _cmd_use(*names: str):
    with pool.scope(), main.use_vars(names):
        while True:
            command = pool.next()
            if command == 'stop':
                break
            main.execute(command)


def _cmd_set_int(name: str, value: int):
    main.vars[name] = value


def _cmd_set_str(name: str, value: str):
    main.vars[name] = value


def _cmd_set_cmd(name: str):
    with pool.scope():
        command = pool.next()
        main.vars[name] = main.execute(command, silent=True)


def _cmd_set_eval(name: str):
    with pool.scope():
        command = pool.next()
        main.vars[name] = eval(command.format_map(main.var_formatter))


def _cmd_get(name: str):
    if name not in main.vars:
        return main.report(f'Нет переменной с именем `{name}`')
    return main.vars[name]


def _cmd_if_eval():
    with pool.scope():
        expression, command = pool.next(), pool.next()
        value = eval(expression.format_map(main.var_formatter))
        if value:
            main.execute(command)
