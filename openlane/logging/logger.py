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
import sys
import click
import atexit
import logging
import rich.console
from typing import ClassVar, Union
from rich.logging import RichHandler


class LogLevels:
    ALL: ClassVar[int] = 0
    DEBUG: ClassVar[int] = 10
    VERBOSE: ClassVar[int] = 15
    INFO: ClassVar[int] = 20
    WARN: ClassVar[int] = 30
    ERROR: ClassVar[int] = 40
    CRITICAL: ClassVar[int] = 50


def __log_levels_dict():
    result = {k: v for k, v in LogLevels.__dict__.items() if not k.startswith("__")}
    for name, value in result.items():
        logging.addLevelName(value, name)
    return result


LogLevelsDict = __log_levels_dict()

console = rich.console.Console()
atexit.register(lambda: rich.console.Console().show_cursor())
__plain_output = "pytest" in sys.modules


class NullFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()


def __logger():
    handler: logging.Handler
    if __plain_output:
        handler = logging.StreamHandler()
        handler.setFormatter(NullFormatter())
    else:
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            markup=True,
            tracebacks_suppress=[
                click,
            ],
            show_level=False,
        )
        handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    logger = logging.getLogger("__openlane__")
    logger.setLevel(LogLevels.VERBOSE)
    logger.addHandler(handler)
    return logger


__openlane_logger = __logger()


def register_additional_handler(handler: logging.Handler):
    """
    Adds a new handler to the default OpenLane logger.

    :param handler: The new handler. Must be of type ``logging.Handler``
        or its subclasses.
    """
    __openlane_logger.addHandler(handler)


def deregister_additional_handler(handler: logging.Handler):
    """
    Removes a registered handler from the default OpenLane logger.

    :param handler: The handler. If not registered, the behavior
        of this function is undefined.
    """
    __openlane_logger.removeHandler(handler)


def set_log_level(lv: Union[str, int]):
    """
    Sets the log level of the default OpenLane logger.

    :param lv: Either the name or number of the desired log level.
    """
    __openlane_logger.setLevel(lv)


def reset_log_level():
    """
    Sets the log level of the default OpenLane logger back to the
    default log level.
    """
    set_log_level("VERBOSE")


def get_log_level() -> int:
    """
    Obtains the numeric log level of the OpenLane logger.
    """
    return __openlane_logger.getEffectiveLevel()


def debug(msg: object, /, **kwargs):
    """
    Logs to the OpenLane logger with the log level DEBUG.

    :param msg: The message to log
    """
    if kwargs.get("stacklevel") is None:
        kwargs["stacklevel"] = 2
    __openlane_logger.debug(msg, **kwargs)


def verbose(*args, **kwargs):
    """
    Prints to the console if the log level is <= VERBOSE.

    All args and kwargs are passed to https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.print
    """
    if get_log_level() > LogLevels.VERBOSE:
        return
    if __plain_output:
        print(*args, **kwargs)
    else:
        console.print(*args, **kwargs)


def info(msg: object, /, **kwargs):
    """
    Logs to the OpenLane logger with the log level INFO.

    :param msg: The message to log
    """
    if kwargs.get("stacklevel") is None:
        kwargs["stacklevel"] = 2
    __openlane_logger.info(msg, **kwargs)


def rule(title: str = "", /, **kwargs):  # pragma: no cover
    """
    Prints a horizontal line on the terminal enclosing the first argument
    if the log level is <= INFO.

    Kwargs are passed to https://rich.readthedocs.io/en/stable/reference/console.html#rich.console.Console.rule

    :param title: A title string to enclose in the console rule
    """
    if get_log_level() > LogLevels.INFO:
        return
    if __plain_output:
        print(("-" * 10) + str(title) + ("-" * 10))
    else:
        console.rule(title, **kwargs)


def success(msg: object, /, **kwargs):
    """
    Logs an item to the OpenLane logger with a success unicode character and
    green/bold rich formatting syntax with the log level INFO.

    :param msg: The message to log
    """
    if kwargs.get("stacklevel") is None:
        kwargs["stacklevel"] = 2
    __openlane_logger.info(f"⭕ [green][bold] {msg}", **kwargs)


def warn(msg: object, /, **kwargs):
    """
    Logs an item to the OpenLane logger with a warning unicode character and
    gold/bold rich formatting syntax with the log level WARN.

    :param msg: The message to log
    """
    if kwargs.get("stacklevel") is None:
        kwargs["stacklevel"] = 2
    __openlane_logger.warning(f"⚠️  [gold][bold] {msg}", **kwargs)


def err(msg: object, /, **kwargs):
    """
    Logs an item to the OpenLane logger terminal with an error unicode character and
    red/bold rich formatting syntax with the log level ERROR.
    """
    if kwargs.get("stacklevel") is None:
        kwargs["stacklevel"] = 2
    __openlane_logger.error(f"❌ [red][bold] {msg}", **kwargs)


if __name__ == "__main__":
    debug("Debug")
    verbose("Verbose")
    rule()
    info("Info")
    success("Success")
    warn("Warn")
    err("Err")
