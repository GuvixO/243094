import pytest

import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup
from test.common.utils.primitives import random_line


class TestShow:
    def test_default(self):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [''] * 8 + [
                'Somebody once told me the world is gonna roll me',
                'I ain\'t the sharpest tool in the shed',
                'She was looking kind of dumb with her finger and her thumb',
                'In the shape of an "L" on her forehead'
            ]
            expect = [
                ' 8: Somebody once told me the world is gonna roll me\n',
                ' 9: I ain\'t the sharpest tool in the shed\n',
                '         ^\n',
                '10: She was looking kind of dumb with her finger and her thumb\n',
                '11: In the shape of an "L" on her forehead\n'
            ]
            expect[0] = '$ ' + expect[0]

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.show'
                runner = create(spec_run, '2.2#show-default')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (9, 5)', 1).just_returns(),
                    runner.manual(f'show 8 11', 5).returns(expect)
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('d', [2, 5, 30])
    def test_show_primitive(self, d):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(d, d, utf8=True) for _ in range(d)]

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.show'
                runner = create(spec_run, '2.2#show-primitive')

                commands = []
                for _ in range(10):
                    i = random.randint(1, len(content) - 1)
                    commands.append(runner.manual(f'show {i} {i}', 1).returns(
                        [f'$ {i}: {content[i]}\n']
                    ))

                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                    *commands
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('d', [1, 2, 3, 4])
    def test_show_no_cursor(self, d):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(5, 5, utf8=True) for _ in range(2 * 10 ** d)]

            with process:
                spec_run = timeout(process.handler, 5)
                spec_run.__name__ = 'run.show'
                runner = create(spec_run, '2.2#show-no-cursor')

                commands = []
                for di in range(1, d + 1):
                    i = random.randint(10 ** (di - 1), 10 ** di - 1)
                    j = random.randint(10 ** d, len(content) - 1)
                    i, j = min(i, j), max(i, j)
                    ret = []
                    for idx in range(i, j + 1):
                        ret.append(f'{idx}: {content[idx]}\n')
                        ret[-1] = ' ' * (d + 1 - ret[-1].find(':')) + ret[-1]
                    ret[0] = '$ ' + ret[0]
                    commands.append(runner.manual(f'show {i} {j}', len(ret)).returns(ret))

                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                    *commands
                )

            cleanup(runner, process)

    def test_show_cursor(self):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(5, 5, utf8=True) for _ in range(100002)]

            with process:
                spec_run = timeout(process.handler, 5)
                spec_run.__name__ = 'run.show'
                runner = create(spec_run, '2.2#show-cursor')

                commands = []
                for d in range(1, 5):
                    i = 10 ** d
                    x = random.randint(0, len(content[i]) - 1)
                    commands += [
                        runner.manual(f'exec data.cursor = ({i}, {x})', 1).just_returns(),
                        runner.manual(f'show {i - 1} {i + 1}', 4).returns([
                            f'$  {i - 1}: {content[i - 1]}\n',
                            f'{i}: {content[i]}\n',
                            ' ' * (x + d + 3) + '^\n',
                            f'{i + 1}: {content[i + 1]}\n'
                        ])
                    ]

                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    *commands
                )

            cleanup(runner, process)
