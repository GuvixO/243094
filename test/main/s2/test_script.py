import pytest

import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup
from test.common.utils.primitives import random_line


class TestScript:
    def test_comment_uncomment(self):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            content = [random_line(10, 10, utf8=True) for _ in range(100)]
            expect = ['# ' + line for line in content]

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.execute[c+unc]'
                runner = create(spec_run, '2.5#comment+uncomment')
                runner.multitest(
                    runner.manual(f'exec data.lines = {content}', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),

                    runner.manual(f'execute {process.resources / "scripts/comment.s"}', 0).just_returns(),
                    runner.manual(f'exec None', 1).just_returns(),
                    runner.manual(f'eval data.lines', 1).returns([f'$  > {repr(expect)}\n']),

                    runner.manual(f'execute {process.resources / "scripts/uncomment.s"}', 0).just_returns(),
                    runner.manual(f'exec None', 1).just_returns(),
                    runner.manual(f'eval data.lines', 1).returns([f'$  > {repr(content)}\n']),
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('times', [0, 1, 3, 7, 13, 25])
    def test_dev(self, times):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            expect = [f'{chr(c)}{chr(c)}' for c in range(ord('a'), ord('a') + times + 1)] + ['']

            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.execute[dev]'
                runner = create(spec_run, '2.5#dev')
                runner.multitest(
                    runner.manual(f'exec data.lines = [""]', 1).just_returns(),
                    runner.manual(f'exec data.cursor = (0, 0)', 1).just_returns(),
                    runner.manual(f'exec main.vars["TIMES"] = {times}', 1).just_returns(),

                    runner.manual(f'execute {process.resources / "scripts/dev.s"}', 3 * times + 1).just_returns(),
                    runner.manual(f'exec None', 1).just_returns(),
                    runner.manual(f'eval data.lines', 1).returns([f'$  > {repr(expect)}\n']),
                )

            cleanup(runner, process)
