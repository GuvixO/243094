from __future__ import annotations

import random


def _english():
    return [chr(i) for i in range(ord('a'), ord('z') + 1)]


def _russian():
    return [chr(i) for i in range(ord('а'), ord('я') + 1)]


def random_word(length: int, chars=None) -> str:
    if chars is None:
        chars = _english()
    word = ''.join(random.choices(chars, k=length))
    return word


def random_line(words: int, words_width: int | tuple[int, int], utf8: bool = False):
    if isinstance(words_width, int):
        words_width = (words_width, words_width)
    chars = None if not utf8 else _english() + _russian()
    return ' '.join([random_word(random.randint(*words_width), chars) for _ in range(words)])


def random_value(size: int):
    randint = lambda: random.randint(-size, size)
    options = [
        randint,
        lambda: random.random() * size,
        lambda: [randint() for _ in range(abs(randint()))],
        lambda: random_word(size)
    ]
    return random.choice(options)()
