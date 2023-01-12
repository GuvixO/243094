import sys
import inspect

import tasks.driver.files.commands as cmd_files
import tasks.driver.network.commands as cmd_net
from tasks.core.command import BasicCommand, GreedyCommand

COMMANDS = {}


def _cmd_help():
    print('Все доступные команды:')
    for cmd in sorted(COMMANDS.keys()):
        print(f' * {cmd}')


files_commands = dict(inspect.getmembers(cmd_files, inspect.isfunction))
net_commands = dict(inspect.getmembers(cmd_net, inspect.isfunction))
commands = files_commands | net_commands
commands[_cmd_help.__name__] = _cmd_help

for name, f in commands.items():
    if not name.startswith('_cmd_'): continue
    short_name = name.removeprefix('_cmd_')
    code = inspect.getsource(f)
    if 'TODO' not in code:
        if f.__dict__.get('__greedy__', False):
            COMMANDS[short_name] = GreedyCommand(f)
        else:
            COMMANDS[short_name] = BasicCommand(f)
