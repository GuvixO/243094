import shutil
import time

import pytest

import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup
from test.common.utils.primitives import random_line


class TestIO:
    @pytest.mark.parametrize('d', [1, 2, 5, 30])
    def test_read(self, d):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file, \
                tmpdir(process.resources / 'tmp', keep=True) as res, \
                tmpfile(res.loc('input')) as input_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))

            content = [random_line(d, d, utf8=True) for _ in range(d)]
            input_file.write('\n'.join(content))

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.read'
                runner = create(spec_run, '2.1#read')
                runner.multitest(
                    runner.manual(f'read {input_file.path}', 1).returns([f'$  > Прочитано {d} строк\n']),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(content)}\n']),
                    runner.manual('eval data.cursor', 1).returns(['$  > (0, 0)\n'])
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('d', [1, 2, 5, 30])
    def test_read_prefill(self, d):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file, \
                tmpdir(process.resources / 'tmp', keep=True) as res, \
                tmpfile(res.loc('input')) as input_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))

            pre_fill = [random_line(1, 5) for _ in range(d)]
            content = [random_line(d, d, utf8=True) for _ in range(d)]
            input_file.write('\n'.join(content))

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.fill.read'
                runner = create(spec_run, '2.1#read-prefill')
                runner.multitest(
                    runner.manual(f'exec data.lines = {pre_fill}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = ({d - 1}, {len(pre_fill[-1]) - 1})', 1).just_returns(),

                    runner.manual(f'read {input_file.path}', 1).returns([f'$  > Прочитано {d} строк\n']),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(content)}\n']),
                    runner.manual('eval data.cursor', 1).returns(['$  > (0, 0)\n'])
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('d', [1, 2, 5, 30])
    def test_save(self, d):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file, \
                tmpdir(process.resources / 'tmp', keep=True) as res:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))

            content = [random_line(d, d, utf8=True) for _ in range(d)]
            y = random.randint(0, d - 1)
            x = random.randint(0, len(content[y]) - 1)

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.save'
                runner = create(spec_run, '2.1#save')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = ({y}, {x})', 1).just_returns(),

                    runner.manual(f'save {res.loc("output")}', 1).returns([f'$  > Сохранено {d} строк\n']),
                    runner.manual('eval data.lines', 1).returns([f'$  > {repr(content)}\n']),
                    runner.manual('eval data.cursor', 1).returns([f'$  > ({y}, {x})\n'])
                )

            time.sleep(2)
            with res.loc('output').open('rb') as output:
                actual = output.read().replace(b'\r', b'')
                expect1 = '\n'.join(content)
                expect2 = expect1 + '\n'
                if actual != expect1.encode('utf-8') and actual != expect2.encode('utf-8'):
                    msg = f'Данные в файле отличаются от ожидаемых {content}'
                    runner._file_name()
                    output_file = res.loc(f'output~{runner.current_log_id:02d}')
                    shutil.copy(res.loc('output'), output_file.absolute())
                    runner.report_wa(f'{runner.test_name}/diff', None, f'resources/tmp/{output_file.name}', msg)
                    pytest.fail(msg)

            cleanup(runner, process)
