import inspect
import typing
from typing import Callable
from dataclasses import dataclass


@dataclass
class Argument:
    arg_type: type
    variadic: bool = False


class Command:
    def __init__(self, f: Callable):
        self.f = f

    def validate_arg_count(self, arg_line: str):
        return True

    def parse(self, arg_line: str):
        raise NotImplementedError


class BasicCommand(Command):
    def __init__(self, f: Callable):
        super().__init__(f)
        type_hints = typing.get_type_hints(f)
        self.arguments = [
            Argument(type_hints[k], v.kind == inspect.Parameter.VAR_POSITIONAL)
            for k, v in inspect.signature(f).parameters.items()
        ]

    def validate_arg_count(self, arg_line: str):
        count = len(arg_line.split())
        if len(self.arguments) > 0 and self.arguments[-1].variadic:
            return count >= len(self.arguments) - 1
        return count == len(self.arguments)

    def parse(self, arg_line: str):
        arg_reprs = arg_line.split()
        arg_types = [arg.arg_type for arg in self.arguments]
        args = [t(x) for x, t in zip(arg_reprs, arg_types)]
        if len(arg_reprs) > len(arg_types):
            assert self.arguments[-1].variadic
            args += list(map(self.arguments[-1].arg_type, arg_reprs[len(arg_types):]))
        return args


class GreedyCommand(Command):
    def __init__(self, f: Callable):
        super().__init__(f)
        type_hints = typing.get_type_hints(f)
        assert len(type_hints) == 1
        annotation = list(type_hints.values())[0]
        assert annotation is str

    def parse(self, arg_line: str):
        return [arg_line]


class ShowDummy(Command):
    def __init__(self, f: Callable):
        super().__init__(f)

    def parse(self, arg_line: str):
        return list(map(int, arg_line.split()))
