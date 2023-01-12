from __future__ import annotations
from typing import Callable, Any, Iterable

from collections import deque
from copy import copy

from tasks.core.command import Command


def singleton(cls):
    instance = None

    def create(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance

    return create


# @singleton
class Descriptor:
    def __init__(self):
        self.lines: list[str] | None = None
        self.y: int | None = None
        self.x: int | None = None

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, item):
        return self.lines[item]

    def __setitem__(self, key, value):
        self.lines[key] = value

    @property
    def line(self):
        return self.lines[self.y]

    @line.setter
    def line(self, new_line):
        self.lines[self.y] = new_line

    @property
    def cursor(self):
        return self.y, self.x

    @cursor.setter
    def cursor(self, yx):
        self.y, self.x = yx

    def __bool__(self):
        return self.lines is not None


# @singleton
class CommandPool:
    def __init__(self):
        self.commands = deque()
        self.base_prefix: str | None = None
        self.indent_level: int = 0

    @property
    def _prefix(self):
        return f'{self.base_prefix} ' if self.indent_level == 0 \
            else '\t' * self.indent_level

    def input(self):
        return input(self._prefix)

    class _Indenter:
        def __init__(self, base: 'CommandPool'):
            self.base = base

        def __enter__(self):
            self.base.indent_level += 1

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.base.indent_level -= 1

    def scope(self):
        return self._Indenter(self)

    def next(self):
        if not self.commands:
            return self.input()
        return self.commands.popleft()

    def put(self, commands):
        for cmd in reversed(commands):
            self.commands.appendleft(cmd)


# @singleton
class Editor:
    def __init__(self):
        self.display: bool = False
        self.display_margin: int = 0

        self.commands: dict[str, Command] = {}
        self.indent_level: int = 0

        self.vars: dict[str, Any] = {}
        self.active_vars: set[str] = set()
        self.macros: dict[str, list[str]] = {}

    def configure(
            self, *,
            display: bool, display_margin: int,
            base_prefix: str, commands: dict[str, Command]
    ):
        self.display = display
        self.display_margin = display_margin
        self.commands = commands
        pool.base_prefix = base_prefix

    @staticmethod
    def report(msg: str, err: Exception | None = None):
        message = f' > {msg}'
        if err is not None:
            message = f'{message}: {err}'
        print(message)

    class _VarFormatter:
        def __init__(self, base: 'Editor', names: Iterable[str]):
            self.base = base
            self.names = names
            self.memory = None

        def __enter__(self):
            self.memory = copy(self.base.active_vars)
            self.base.active_vars |= set(self.names)

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.base.active_vars = self.memory

    def use_vars(self, names: Iterable[str]):
        return self._VarFormatter(self, names)

    class _SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    @property
    def var_formatter(self):
        return Editor._SafeDict(
            {name: self.vars.get(name) for name in self.active_vars} |
            {f'@{name}': repr(self.vars.get(name)) for name in self.active_vars}
        )

    def execute(self, line: str, *, silent: bool = False):
        cmd = line.split(maxsplit=1)[0]
        if cmd not in self.commands:
            return self.report('Некорректная команда, наберите `help` для вывода списка команд')

        command = self.commands[cmd]
        arg_line = line.removeprefix(cmd).format_map(self.var_formatter)
        if arg_line.startswith(' '):
            arg_line = arg_line.removeprefix(' ')
        if not command.validate_arg_count(arg_line):
            return self.report(f'Некорректное число аргументов')

        args = command.parse(arg_line)
        result = command.f(*args)
        if not silent:
            if result is not None:
                self.report(repr(result))
            elif self.display and data.lines is not None \
                    and 'show' in self.commands and cmd != 'show':
                from_line = max(0, data.y - self.display_margin)
                to_line = min(len(data) - 1, data.y + self.display_margin)
                self.execute(f'show {from_line} {to_line}', silent=True)
        return result


data = Descriptor()
pool = CommandPool()
main = Editor()
