from __future__ import annotations

import os
import re
import shutil
import pathlib

import pytest
import re
from datetime import datetime, timezone

from copy import deepcopy
from threading import Thread, Event

_whatever = object()


def root_directory():
    path = pathlib.Path().absolute()
    candidates = [path] + list(path.parents)
    for parent in candidates:
        if parent.parts[-1].startswith('assignment'):
            return parent
    raise AssertionError('Expected to find the assignment root as a parent directory')


def _trim_message(msg):
    lines = msg.split('\n')
    first_line = 0
    while first_line < len(lines) and lines[first_line].strip() == '':
        first_line += 1
    lines = lines[first_line:]

    max_prefix = max([len(re.match(r'^\s*', line).group()) for line in lines])
    return '\n'.join([line[max_prefix:] for line in lines])


class TestInstantiationError(Exception):
    pass


class _IdGenerator:
    def __init__(self):
        self.id = 0

    def __call__(self):
        self.id += 1
        return self.id


class TestBase:
    _root_path = root_directory() / 'testlog'
    _gen_id = _IdGenerator()

    @staticmethod
    def _default_check(result, answer):
        if result != answer:
            return False, 'Ответ отличается от ожидаемого'
        return True, 'Ok'

    def __init__(self, spec, test_name, gen=None, check=None):
        self._gen_id.id = 0

        self.test_name = test_name
        self.base_path = TestBase._root_path / self.test_name
        if self.base_path.exists():
            mod_time = datetime.fromtimestamp(os.stat(self.base_path).st_mtime) 
            if mod_time < pytest.start_time:
                for item in os.listdir(self.base_path):
                    full_path = self.base_path / item
                    if full_path.is_dir():
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.path: pathlib.Path | None = None
        self.current_log_id = -1
        self.spec: Callable | None = None

        self.default_gen = gen
        self.check = TestBase._default_check if check is None else check
        self.set_spec(spec)

    def set_spec(self, spec):
        self.spec = spec
        self.path = self.base_path / spec.__name__

    class _Test:
        def __init__(self, args, kwargs, answer):
            self.args = args
            self.kwargs = kwargs
            self.answer = answer

    class _Handler:
        def __init__(self, args, kwargs):
            self._args = args
            self._kwargs = kwargs

        def returns(self, return_value):
            return TestBase._Test(self._args, self._kwargs, return_value)

        def just_returns(self):
            return TestBase._Test(self._args, self._kwargs, _whatever)

    @staticmethod
    def manual(*args, **kwargs):
        return TestBase._Handler(args, kwargs)

    def auto(self, *args, **kwargs):
        gen = kwargs.pop('gen', self.default_gen)
        data = gen(*args, **kwargs)
        if len(data) == 2:
            test_args, test_answer = data
            test_kwargs = {}
        else:
            test_args, test_kwargs, test_answer = data
        return TestBase._Test(test_args, test_kwargs, test_answer)

    def run(self, test):
        test_no = self._gen_id()
        test_description = self.test_name
        if test_no is not None:
            test_description = f'{test_description}/{test_no}'

        try:
            args_c, kwargs_c = deepcopy(test.args), deepcopy(test.kwargs)
            result = self.spec(*args_c, **kwargs_c)
            if test.answer is _whatever:
                return
            verdict, msg = self.check(result, test.answer)
            if not verdict:
                self.report_wa(test_description, test, result, msg)
                pytest.fail(f'Неверный ответ на тесте {test_description}:\n{msg}')
        except TimeoutError:
            self.report_tl(test_description, test)
            pytest.fail(f'Превышено время работы на тесте {test_description}')
        except Exception as e:
            self.report_re(test_description, test, e)
            raise e

    def multitest(self, *tests):
        for test in tests:
            self.run(test)

    def _file_name(self):
        index = 1
        while True:
            path = f'{self.path}~{index:02d}.log'
            if not os.path.exists(path):
                break
            index += 1
        self.current_log_id = index
        return path

    def report_wa(self, test_description, test, result, msg):
        with open(self._file_name(), 'a', encoding='utf-8') as log:
            log.write(_trim_message(f'''
            ========================================
            Неверный ответ на тесте {test_description}
            {msg}'''))

            log.write('\n')
            if test is None:
                log.write(_trim_message(f'''
                Результат (получено):
                - {result}
                '''))
            else:
                log.write(_trim_message(f'''
                Входные данные:
                - args      : {test.args}
                - kwargs    : {test.kwargs}
                
                Результат:
                - ожидалось : {test.answer}
                - получено  : {result}
                '''))

    def report_tl(self, test_description, test):
        with open(self._file_name(), 'a', encoding='utf-8') as log:
            log.write(_trim_message(f'''
            ========================================
            Превышено время работы на тесте {test_description}
            
            Входные данные:
            - args      : {test.args}
            - kwargs    : {test.kwargs}
            '''))

    def report_re(self, test_description, test, ex):
        with open(self._file_name(), 'a', encoding='utf-8') as log:
            log.write(_trim_message(f'''
            ========================================
            Ошибка в работе решения на тесте {test_description}''') +
                      f'\n{repr(ex) if not isinstance(ex, str) else ex}')

            if test is None:
                return
            log.write('\n')
            log.write(_trim_message(f'''
            Входные данные:
            - args      : {test.args}
            - kwargs    : {test.kwargs}
            '''))

    def cleanup(self):
        if not os.listdir(self.path.parent):
            shutil.rmtree(self.path.parent)


create = TestBase


def timeout(spec, seconds=5.0):
    result = None

    def _worker(*args, **kwargs):
        nonlocal result
        result = spec(*args, **kwargs)

    def _run(*args, **kwargs):
        thread = Thread(target=_worker, args=args, kwargs=kwargs)
        thread._stop_event = Event()
        try:
            thread.start()
            thread.join(seconds)
            if thread.is_alive():
                raise TimeoutError('Function took too long to execute')
            return result
        finally:
            thread._stop_event.set()

    _run.__name__ = spec.__name__
    return _run
