import pathlib
import functools
import rich.console

console = rich.console.Console()

log = functools.partial(console.log, console)


def success(printable, *args, **kwargs):
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(f"⭕ [green][bold] {printable}", *args, **kwargs)


def warn(printable, *args, **kwargs):
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(f"⚠️ [gold][bold] {printable}", *args, **kwargs)


def error(printable, *args, **kwargs):
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    console.log(f"❌ [red][bold] {printable}", *args, **kwargs)


def mkdirp(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)
