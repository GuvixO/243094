import time

import pytest

from test.common.test import create, timeout
from test.main.process import spawn
from test.main.base import cleanup


class TestRuns:
    def test_runs(self):
        process = spawn(auto_exit=False)
        with process:
            spec_run = timeout(process.handler, 3)
            spec_run.__name__ = 'run.exit'
            runner = create(spec_run, '1.0')
            runner.run(runner.manual('exit', 1).just_returns())

        cleanup(runner, process)
