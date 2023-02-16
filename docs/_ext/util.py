import os
import shutil
import pathlib
from typing import Union


def debug(*args, **kwargs):
    if os.getenv("SPHINX_DEBUG") == "1":
        print(*args, **kwargs)


def rimraf(path: Union[str, os.PathLike]):
    try:
        shutil.rmtree(path)
    except NotADirectoryError:
        pathlib.Path(path).unlink(missing_ok=True)
    except FileNotFoundError:
        pass


def mkdirp(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)
