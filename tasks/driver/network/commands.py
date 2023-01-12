from __future__ import annotations

import os
import sys
import requests
import socket

from tasks.core import data, pool, main
from tasks.driver.utils import requires_data, greedy


# --------------- Задание 3.1 --------------- #

def _cmd_request(url: str):
    # TODO реализуйте заполнение `data` результатом HTTP-запроса
    pass


# --------------- Задание 3.2 --------------- #

def _cmd_await_receive(port: int):
    host = '127.0.0.1'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((host, port))
        server.listen()
        conn, addr = server.accept()
        main.report(f'Connected from {addr}')

        with conn:
            # TODO реализуйте получение данных файла и сохранения его в `data`
            conn.sendall(b'Ok')

    main.report(f'Принято {len(data)} строк')


def _cmd_send(host: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))

        # TODO реализуйте отправку данных из `data`

        main.report(f'Отправлено {len(data)} строк')
        response = client.recv(2).decode('utf-8')
        main.report(f'Ответ: {response}')

# --------------- Задание 3.* --------------- #
