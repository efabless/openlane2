# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import atexit
import click
import typing
import logging

import rich.console
from rich.logging import RichHandler


console = rich.console.Console()
atexit.register(lambda: rich.console.Console().show_cursor())


class LogLevels:
    ALL: typing.ClassVar[int] = 0
    DEBUG: typing.ClassVar[int] = 10
    VERBOSE: typing.ClassVar[int] = 15
    INFO: typing.ClassVar[int] = 20
    WARN: typing.ClassVar[int] = 30
    ERROR: typing.ClassVar[int] = 40
    CRITICAL: typing.ClassVar[int] = 50


LogLevelsDict = {k: v for k, v in LogLevels.__dict__.items() if not k.startswith("__")}

for name, value in LogLevelsDict.items():
    logging.addLevelName(value, name)

FORMAT = "%(message)s"
logging.basicConfig(
    level=15,
    format=FORMAT,
    datefmt="",
    handlers=[
        RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            tracebacks_suppress=[
                click,
            ],
        )
    ],
)


def set_log_level(lv: typing.Union[str, int]):
    logging.getLogger().setLevel(lv)


def get_log_level() -> int:
    return logging.getLogger().getEffectiveLevel()


def print(*args, **kwargs):
    """
    Prints to the terminal without formatting.

    See the Rich API for more info: https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.print
    """
    if get_log_level() > LogLevels.INFO:
        return
    console.print(*args, **kwargs, crop=False, style=None)


def verbose(*args, **kwargs):
    """
    Prints to the terminal with automatic rich formatting.

    Verbose level or lower only.

    See the Rich API for more info: https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.log
    """
    if get_log_level() > LogLevels.VERBOSE:
        return
    console.print(*args, **kwargs)


def debug(*args, **kwargs):
    """
    Prints to the terminal with automatic rich formatting.

    Debug level or lower only.

    See the Rich API for more info: https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.log
    """
    if get_log_level() > LogLevels.DEBUG:
        return
    console.print(*args, **kwargs)


def info(*args, **kwargs):
    """
    Prints to the terminal with automatic rich formatting.

    See the Rich API for more info: https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.log
    """
    if get_log_level() > LogLevels.INFO:
        return
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(*args, **kwargs)


def rule(*args, **kwargs):
    """
    Prints a horizontal line on the terminal.

    See the Rich API for more info: https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.rule
    """
    if get_log_level() > LogLevels.INFO:
        return
    console.rule(*args, **kwargs)


def success(printable, *args, **kwargs):
    """
    Logs an item to the terminal with a success unicode character and
    green/bold formatting.
    """
    if get_log_level() > LogLevels.INFO:
        return
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(f"⭕ [green][bold] {printable}", *args, **kwargs)


def warn(printable, *args, **kwargs):
    """
    Logs an item to the terminal with a warning unicode character and
    gold/bold formatting.
    """
    if get_log_level() > LogLevels.WARN:
        return
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(f"⚠️ [gold][bold] {printable}", *args, **kwargs)


def err(printable, *args, **kwargs):
    """
    Logs an item to the terminal with a warning unicode character and
    gold/bold formatting.
    """
    if get_log_level() > LogLevels.ERROR:
        return
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(f"❌ [red][bold] {printable}", *args, **kwargs)
