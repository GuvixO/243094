import pytest

import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup
from test.common.utils.primitives import random_line, random_word


class TestEdit:
    def test_default(self):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [
                'Row zero',
                'Row 1',
                'Row dos'
            ]
            expect = [
                'Row zero',
                'Rolex',
                'watch and more 1',
                'Row dos'
            ]

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.newline.type'
                runner = create(spec_run, '2.3#edit-default')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),

                    runner.manual('move 1 2', 0).just_returns(),
                    runner.manual('type_inline lex', 0).just_returns(),
                    runner.manual('newline', 0).just_returns(),
                    runner.manual('move 2 1', 0).just_returns(),
                    runner.manual('type\natch and more', 0).just_returns(),

                    runner.manual('exec None', 1).just_returns(),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(expect)}\n']),
                    runner.manual('eval data.cursor', 1).returns(['$  > (2, 14)\n'])
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('lines', [1, 1000])
    @pytest.mark.parametrize('xp', ['start', 'mid', 'end'])
    def test_newline(self, lines, xp):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            part1 = [random_line(5, 5, utf8=True) for _ in range(lines)]
            part2 = [random_line(5, 5, utf8=True) for _ in range(lines)]
            if xp == 'start':
                part2[0] = part1[-1] + part2[0]
                part1[-1] = ''
            elif xp == 'end':
                part1[-1] += part2[0]
                part2[0] = ''
            content = part1[:-1] + [part1[-1] + part2[0]] + part2[1:]

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.newline'
                runner = create(spec_run, '2.3#newline')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = ({lines - 1}, {len(part1[-1])})', 1).just_returns(),

                    runner.manual('newline', 0).just_returns(),

                    runner.manual('exec None', 1).just_returns(),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(part1 + part2)}\n']),
                    runner.manual('eval data.cursor', 1).returns([f'$  > ({lines}, 0)\n'])
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('lines', [1, 100, 10000])
    def test_type(self, lines):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(5, 5, utf8=True) for _ in range(lines)]

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.type-inline'
                runner = create(spec_run, '2.3#type')

                commands, post_commands = [], []
                for _ in range(10):
                    y = random.randint(0, len(content) - 1)
                    x = random.randint(0, len(content[y]))
                    insertion = random_word(10, ['a', 'Я', ' '])
                    commands += [
                        runner.manual(f'exec data.cursor = ({y}, {x})', 1).just_returns(),
                        runner.manual(f'type_inline {insertion}', 0).just_returns()
                    ]
                    post_commands.append(
                        runner.manual(f'exec data[{y}] = data[{y}][:{x}] + data[{y}][{x + 10}:]', 1).just_returns()
                    )

                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    *commands,
                    *reversed(post_commands),

                    runner.manual('exec None', 1).just_returns(),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(content)}\n'])
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('xp', [0b00, 0b01, 0b10, 0b11])
    @pytest.mark.parametrize('lines', [1, 30, 1000])
    def test_backspace(self, lines, xp):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            parts = [
                [random_line(5, 5, utf8=True) for _ in range(lines)]
                for _ in range(3)
            ]
            content = parts[0] + parts[1] + parts[2]
            expect = parts[0] + parts[2]

            def _merge(data, y):
                data[y] += data[y + 1]
                return data[:y + 1] + data[y + 2:]

            rm = sum(map(len, parts[1])) + lines + 1
            expect = _merge(expect, lines - 1)
            y, x = 2 * lines, 0
            if xp & 1:
                content = _merge(content, 2 * lines - 1)
                y -= 1
                x = len(parts[1][-1])
                rm -= 1
            if xp & 2:
                content = _merge(content, lines - 1)
                y -= 1
                rm -= 1
            if lines == 1 and xp == 0b11:
                x += len(parts[0][-1])

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.backspace'
                runner = create(spec_run, '2.4#backspace')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = ({y}, {x})', 1).just_returns(),

                    runner.manual(f'backspace {rm}', 0).just_returns(),

                    runner.manual('exec None', 1).just_returns(),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(expect)}\n']),
                    runner.manual('eval data.cursor', 1).returns([f'$  > ({lines - 1}, {len(parts[0][-1])})\n'])
                )

            cleanup(runner, process)
