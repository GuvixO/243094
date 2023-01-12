import pytest

import re
import json
import random

from test.common.test import create, timeout, root_directory
from test.common.mock.fs import tmpcd, tmpfile, tmpdir
from test.main.process import spawn
from test.main.base import config, cleanup


class TestRequests:
    @pytest.mark.parametrize('info', [
        ('posts', ('userId', 'id', 'title', 'body')),
        ('users', ('id', 'name', 'username', 'address', 'phone', 'website', 'company')),
        ('users/7/posts', ('userId=7',)),
        ('posts/13/comments', ('postId=13',))
    ])
    def test_json(self, info):
        url = 'https://jsonplaceholder.typicode.com/' + info[0]

        def check(output: str, _):
            nonlocal runner
            output = output[0].removeprefix('$  > ')
            try:
                lines = eval(output)
                obj = json.loads('\n'.join(lines))
                if not isinstance(obj, list):
                    return False, 'Полученный объект не является json-массивом'
                for key in info[1]:
                    msg = f'Элемент полученного объекта не содержит {key}'
                    value = None
                    if '=' in key:
                        key, value = key.split('=')
                        value = int(value)
                    for item in obj:
                        if key in item and value is None or value == item[key]:
                            continue
                        return False, (msg if value is None else f'{msg}: {value}')
            except (BaseException, ValueError) as e:
                return False, f'Ошибка при распознании полученного ответа в json-формате: {e}'
            return True, 'Ok'

        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            with process:
                spec_run = timeout(process.handler, 5)
                spec_run.__name__ = 'run.request.parse'
                runner = create(spec_run, '3.1#request-json', check=check)
                runner.multitest(
                    runner.manual(f'request {url}', 0).just_returns(),
                    runner.manual('exec None', 1).just_returns(),
                    runner.manual('eval data.lines', 1).returns('<Valid json-format response>')
                )

            cleanup(runner, process)

    @pytest.mark.parametrize('info', [
        ('https://noscript.net/', 'What is it? - NoScript: block scripts and own your browser!'),
        ('https://google.com', 'Google'),
        ('https://codeforces.com', 'Codeforces'),
        ('https://jsonplaceholder.typicode.com', 'JSONPlaceholder - Free Fake REST API')
    ])
    def test_html(self, info):
        url, title = info
        title = title.lower().replace(' ', '')

        def check(output: str, _):
            nonlocal runner
            output = output[0].removeprefix('$  > ')
            try:
                lines = eval(output)
                html = '\n'.join(lines).lower()
                html = re.sub(r'\s', '', html)
                if '<!doctypehtml' not in html:
                    return False, 'Данные не являются корректным html'
                if f'<title>{title.lower()}</title>' not in html:
                    return False, 'Данные не содержат корректное название страницы'
            except (BaseException, ValueError) as e:
                return False, f'Ошибка при распознании полученного ответа в html-формате: {e}'
            return True, 'Ok'

        process = spawn()
        with tmpcd(root_directory()), tmpfile('tasks/config.json') as config_file:
            config_file.write(json.dumps(config(False, -1, '$'), indent=2))
            with process:
                spec_run = timeout(process.handler, 5)
                spec_run.__name__ = 'run.request.parse'
                runner = create(spec_run, '3.1#request-html', check=check)
                runner.multitest(
                    runner.manual(f'request {url}', 0).just_returns(),
                    runner.manual('exec None', 1).just_returns(),
                    runner.manual('eval data.lines', 1).returns('<Valid html-format response>')
                )

            cleanup(runner, process)
