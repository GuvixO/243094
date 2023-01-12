import pytest

import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup
from test.common.utils.primitives import random_line


class TestFind:
    @pytest.mark.parametrize('lines', [1, 30, 1000])
    def test_find_one(self, lines):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(50, 50, utf8=True) for _ in range(lines)]

            y = random.randint(lines // 2, lines - 1)
            x = random.randint(0, 10000)
            line = random_line(10, 10, utf8=True) + '#'
            content[y] = '*' * x + line + '*' * y

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.find-inline'
                runner = create(spec_run, '2.4#find-one')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                    runner.manual(f'find_inline {line}', 1).returns([f'$  > ({y}, {x})\n'])
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('lines', [1, 30, 1000])
    def test_find_many(self, lines):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(50, 50, utf8=True) for _ in range(lines)]

            line = random_line(5, 5, utf8=True) + '#'
            c = min(lines, 100)

            with process:
                spec_run = timeout(process.handler, 5)
                spec_run.__name__ = 'run.find-inline'
                runner = create(spec_run, '2.4#find-many')

                xs, commands = [], []
                for i in range(c):
                    y = lines // c * i
                    for it in range(2):
                        x = len(content[y])
                        commands += [
                            runner.manual(f'find_inline {line}', 1).returns([f'$  > ({y}, {x - it})\n']),
                            runner.manual(f'exec data.cursor = ({y}, 0)', 1).just_returns(),
                            runner.manual(f'exec data.line = '
                                          f'data.line[:{x + len(line) - 1 - it}] + '
                                          f'data.line[{x + len(line) - it}:]', 1).just_returns()
                        ]
                        content[y] = content[y] + line + random_line(10, 10)

                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                    *commands,
                    runner.manual(f'find_inline {line}', 1).returns([f'$  > \'Не найдено\'\n'])
                )

            cleanup(runner, process)