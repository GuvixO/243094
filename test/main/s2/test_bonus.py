import os
import time

import pytest

import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup
from test.common.utils.primitives import random_line


class TestBonus:
    @pytest.mark.parametrize('lines', [1, 30, 1000])
    def test_ban(self, lines):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))

            content = [random_line(7, 7, utf8=True) for _ in range(lines)]
            expect = content[:]
            line = random_line(5, 5, utf8=True) + '#'
            repl = '*' * len(line)
            for i in range(lines):
                x = random.randint(len(content[i]) // 3, len(content[i]))
                in1, in2, in3 = random_line(3, 3), random_line(4, 4), random_line(5, 5)
                content[i] = content[i][:x] + line + in1 + line[:-1] + in2 + line + in3
                expect[i] = expect[i][:x] + repl + in1 + line[:-1] + in2 + repl + in3

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.execute[ban]'
                runner = create(spec_run, '2.B#ban')

                if not (process.resources / 'scripts/ban.s').exists():
                    msg = 'Скрипт `ban.s` не найден'
                    runner.report_wa(f'{runner.test_name}/exits.script', None, None, msg)
                    pytest.fail(msg)
                else:
                    runner.multitest(
                        runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                        runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                        runner.manual(f'exec main.vars["BAN"] = {repr(line)}', 1).just_returns(),

                        runner.manual(f'execute {process.resources / "scripts/ban.s"}', 0).just_returns(),
                        runner.manual(f'exec None', 1).just_returns(),
                        runner.manual(f'eval data.lines', 1).returns([f'$  > {repr(expect)}\n']),
                    )

            cleanup(runner, process)

    @pytest.mark.parametrize('lines', [1, 30, 1000])
    def test_process(self, lines):
        process = spawn(auto_exit=True)
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file, \
                tmpdir(process.resources / 'tmp/process', keep=True) as tmp:
            for item in os.listdir(tmp.path):
                os.remove(tmp.path / item)
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))

            content = [random_line(10, 10, utf8=True) for _ in range(lines)]
            input_path = tmp.loc('data')
            with open(input_path, 'wb') as input_file:
                input_file.write('\n'.join(content).encode('utf-8'))
            expect_line = ''.join(content).replace(' ', '')
            expect_stat = sum(map(len, content)) + len(content) - 1 - len(expect_line)

            with process:
                spec_run = timeout(process.handler, 300)
                spec_run.__name__ = 'run.execute[process]'
                runner = create(spec_run, '2.B#process')

                if not (process.resources / 'scripts/process.s').exists():
                    msg = 'Скрипт `process.s` не найден'
                    runner.report_wa(f'{runner.test_name}/exits.script', None, None, msg)
                    pytest.fail(msg)
                else:
                    runner.multitest(
                        runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                        runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                        runner.manual(f'exec main.vars["FILE"] = {repr(str(input_path))}', 1).just_returns(),
                        runner.manual(f'execute {process.resources / "scripts/process.s"}', 0).just_returns(),
                    )

                    output_path = tmp.loc('data.processed')
                    time.sleep(2)
                    if not output_path.exists():
                        msg = 'Файл `data.processed` не был создан после выполнения скрипта'
                        runner.report_wa(f'{runner.test_name}/exists.output', None, None, msg)
                        pytest.fail(msg)
                    else:
                        with open(output_path, 'rb') as output_file:
                            output = output_file.read()
                        output = output.decode('utf-8').replace('\r', '')
                        if output.endswith('\n'):
                            output = output.removesuffix('\n')
                        if output.split('\n') != [expect_line, str(expect_stat)]:
                            msg = 'Ожидался другой ответ'
                            runner.report_wa(f'{runner.test_name}/check', None, output, msg + f' на тесте {content}')
                            pytest.fail(msg)

            cleanup(runner, process)
