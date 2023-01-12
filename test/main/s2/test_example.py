import pytest

import json

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile
from test.main.process import spawn
from test.main.base import config, cleanup


class TestExample:
    def test_example(self):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.example'
                runner = create(spec_run, '2.0#example')
                runner.run(runner.manual('example', 1).returns(
                    [f'$  > Команда-пример, выводит это сообщение\n']
                ))

            cleanup(runner, process)

    @pytest.mark.parametrize('arg', [-3, 0, 1, 3, 17, 77])
    def test_example_square(self, arg):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.example-square'
                runner = create(spec_run, '2.0#example-square')
                runner.run(runner.manual(f'example_square {arg}', 1).returns(
                    [f'$  > {arg ** 2}\n']
                ))

            cleanup(runner, process)

    def test_no_display(self):
        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            with process:
                spec_run = timeout(process.handler, 3)
                spec_run.__name__ = 'run.cursor.home-show'
                runner = create(spec_run, '1.1#config.nodisplay')
                runner.multitest(
                    runner.manual('exec data.lines = [""] * 100', 1).just_returns(),

                    runner.manual('exec data.cursor = (0, 0)', 1).returns(['$  > \'Done\'\n']),
                    runner.manual('home', 0).just_returns(),
                    runner.manual('exec data.cursor = (50, 0)', 1).returns(['$ $  > \'Done\'\n']),
                    runner.manual('home', 0).just_returns(),
                    runner.manual('exec data.cursor = (97, 0)', 1).returns(['$ $  > \'Done\'\n']),
                    runner.manual('home', 0).just_returns(),

                    runner.manual('exit', 1).returns(['$ $ '])
                )

            cleanup(runner, process)
