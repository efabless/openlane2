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
import click
import logging
from rich.logging import RichHandler
from rich.text import Text
from rich.style import Style, StyleType
from ..logging import set_handler, console, set_log_level, LogLevels, add_filter


class DebugRichHandler(RichHandler):
    def __init__(self, *args, **kwargs):
        kwargs.pop("show_time", None)
        kwargs.pop("omit_repeated_times", None)
        kwargs.pop("show_level", None)
        kwargs.pop("rich_tracebacks", None)
        kwargs.pop("markup", None)
        kwargs.pop("tracebacks_suppress", None)
        kwargs.pop("level", None)
        super().__init__(
            rich_tracebacks=True,
            markup=True,
            tracebacks_suppress=[
                click,
            ],
            show_level=True,
            show_time=True,
            omit_repeated_times=False,
            *args,
            **kwargs,
        )
        self._log_render.level_width = 3

    def get_level_text(self, record: logging.LogRecord) -> Text:
        level_name = record.levelname
        style: StyleType
        if level_name == "WARNING":
            style = Style(color="yellow", bold=True)
        else:
            style = f"logging.level.{level_name.lower()}"
        level_text = Text.styled(
            f"[{level_name.ljust(8)[0]}]",
            style,
        )
        return level_text


class DebugFilter(logging.Filter):
    def filter(self, record):
        return not record.levelno == LogLevels.SUBPROCESS


_DEBUG_HANDLER = False
_SAVE_ENV = False
_PDB = True


def set_debug_mode():
    global _DEBUG_HANDLER, _SAVE_ENV, _PDB
    _DEBUG_HANDLER = True
    _SAVE_ENV = True

    handler = DebugRichHandler(console=console)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)
    set_handler(handler)
    set_log_level(LogLevels.DEBUG)
    add_filter(DebugFilter())

    if _PDB:
        import sys

        def info(type, value, tb):
            if (
                hasattr(sys, "ps1")
                or not sys.stdin.isatty()
                or not sys.stdout.isatty()
                or not sys.stderr.isatty()
                or issubclass(type, SyntaxError)
            ):
                # we are in interactive mode or we don't have a tty-like
                # device, so we call the default hook
                sys.__excepthook__(type, value, tb)
            else:
                import traceback, pdb

                # we are NOT in interactive mode, print the exception...
                traceback.print_exception(type, value, tb)
                # ...then start the debugger in post-mortem mode.
                pdb.pm()

        sys.excepthook = info
