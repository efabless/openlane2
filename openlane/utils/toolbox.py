from .lib import LibTools
from typing import Optional


class Toolbox(object):
    libtools: LibTools

    def __init__(self, tmp_dir: Optional[str] = None) -> None:
        if tmp_dir is None:
            tmp_dir = "./openlane_tmp"  # Temporary
        self.libtools = LibTools(tmp_dir)
